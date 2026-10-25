# Copyright (C) 2025-2026 VanilleIce
# All rights reserved.
#
# SkySheet Converter is proprietary software.
# Commercial use, redistribution, and modification are prohibited.
# See LICENSE.md for details.

import ctypes
import json
import math
import os
import queue
import sys
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from tkinter import filedialog, messagebox

# =============================================================================
if __name__ == "__main__":
    try:
        if getattr(sys, 'frozen', False):
            os.chdir(Path(sys.executable).parent)
        else:
            os.chdir(Path(__file__).resolve().parent)
    except Exception:
        pass
# =============================================================================

import customtkinter as ctk

# ==================== Konstanten ====================

VERSION = "2.0.0"

# Fenster-Größen (exakt)
DEFAULT_WINDOW_SIZE = (520, 760)
WINDOW_WIDTH = 520

# Button-Breiten
MAIN_BUTTON_WIDTH = 400
OPTION_BUTTON_WIDTH = 400

# Card-Style
CARD_STYLE = {
    "fg_color": "transparent",
    "border_width": 1,
    "border_color": ("gray75", "gray35"),
    "corner_radius": 10,
}
CARD_PADY = 4

# Farben
CONVERT_COLOR = "#2fa572"
CONVERT_HOVER = "#106a43"

FILE_BTN_COLOR = ("#3B8ED0", "#1F6AA5")
FILE_BTN_HOVER = ("#4A9EDF", "#2E7BB8")

# Unterstützte Datei-Endungen
SUPPORTED_EXTENSIONS = (".json", ".skysheet", ".txt")
SUPPORTED_FILETYPES = [
    ("SkySheet files", "*.json *.skysheet *.txt"),
    ("JSON", "*.json"),
    ("SkySheet", "*.skysheet"),
    ("Text", "*.txt"),
    ("All files", "*.*"),
]
SUPPORTED_LABEL = ".json / .skysheet / .txt"

# ==================== Keyboard-Layout Daten ====================

ROWS = [
    ["Key0", "Key1", "Key2", "Key3", "Key4"],
    ["Key5", "Key6", "Key7", "Key8", "Key9"],
    ["Key10", "Key11", "Key12", "Key13", "Key14"]
]

DEFAULT_LAYOUT = {
    "Key0": "z", "Key1": "u", "Key2": "i", "Key3": "o", "Key4": "p",
    "Key5": "h", "Key6": "j", "Key7": "k", "Key8": "l", "Key9": "ö",
    "Key10": "n", "Key11": "m", "Key12": ",", "Key13": ".", "Key14": "-"
}

LAYOUT_ALIASES = {"RUSSIAN": "йцукен"}
PREFERRED_DEFAULT = "QWERTZ"


# ==================== Path helpers ====================

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def user_data_path(relative_path=""):
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path) if relative_path else base


def _safe_folder_name(name):
    if not name:
        return "output"
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, '_')
    name = name.strip().strip('.')
    return name or "output"


def make_output_dir(song_name):
    base = user_data_path("output")
    folder = _safe_folder_name(song_name)
    out_dir = os.path.join(base, folder)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


# ==================== Loaders ====================

def parse_key(raw_key):
    if "Key" not in raw_key:
        return raw_key
    parts = raw_key.split("Key")
    if len(parts) < 2:
        return raw_key
    return "Key" + parts[1]


def load_translations():
    translations = {}
    lang_dir = resource_path('lang')
    if not os.path.isdir(lang_dir):
        return translations
    for lang_file in sorted(os.listdir(lang_dir)):
        if not lang_file.lower().endswith(".xml"):
            continue
        lang_code = os.path.splitext(lang_file)[0].lower()
        try:
            root = ET.parse(os.path.join(lang_dir, lang_file)).getroot()
            translations[lang_code] = {el.tag: (el.text or "") for el in root}
        except Exception:
            pass
    return translations


def _read_layout_file(path):
    root = ET.parse(path).getroot()
    layout = {}
    for key in root.findall('key'):
        key_id = key.attrib.get('id')
        if key_id:
            layout[key_id] = key.text or ""
    return layout


def load_layouts():
    layouts = {}
    layouts_dir = resource_path('layouts')

    if os.path.isdir(layouts_dir):
        for fname in sorted(os.listdir(layouts_dir)):
            if not fname.lower().endswith(".xml"):
                continue
            name = os.path.splitext(fname)[0]
            if name.strip().lower() == "custom":
                continue
            label = name
            for ui_name, file_name in LAYOUT_ALIASES.items():
                if name == file_name:
                    label = ui_name
                    break
            try:
                layouts[label.upper()] = _read_layout_file(os.path.join(layouts_dir, fname))
            except Exception:
                pass

    if "QWERTZ" not in layouts:
        layouts["QWERTZ"] = dict(DEFAULT_LAYOUT)

    has_custom = False
    for candidate in (user_data_path("custom.xml"),
                      os.path.join(layouts_dir, "custom.xml"),
                      os.path.join(layouts_dir, "CUSTOM.xml")):
        if os.path.isfile(candidate):
            try:
                layouts["CUSTOM"] = _read_layout_file(candidate)
                has_custom = True
                break
            except Exception:
                pass

    return layouts, has_custom


def load_skysheet_file(file_path):
    for enc in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            with open(file_path, 'r', encoding=enc) as f:
                return json.load(f)
        except UnicodeDecodeError:
            continue
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    raise ValueError("Unsupported file encoding (tried UTF-16, UTF-8-BOM, UTF-8).")


# ==================== Escaping helpers ====================

def safe_html(text):
    if text is None:
        return ""
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;'))


# ==================== Note preparation ====================

def _prepare_processed_notes(song_data):
    notes = song_data.get('songNotes', [])
    processed = [{'key': parse_key(n['key']), 'time': n['time']} for n in notes]
    if not processed:
        raise ValueError("Song contains no notes.")
    return processed, min(n['time'] for n in processed), max(n['time'] for n in processed)


def _build_intervals(processed_notes, min_time, max_time, interval_size=100):
    intervals = []
    t = min_time
    while t <= max_time:
        intervals.append({'start': t, 'end': t + interval_size, 'keys': set()})
        t += interval_size
    for note in processed_notes:
        idx = math.floor((note['time'] - min_time) / interval_size)
        if 0 <= idx < len(intervals):
            intervals[idx]['keys'].add(note['key'])
    return [i for i in intervals if i['keys']]


def _ordered_keys(keys):
    pos = {}
    for r, row in enumerate(ROWS):
        for c, k in enumerate(row):
            pos[k] = (r, c)
    return sorted(keys, key=lambda k: pos.get(k, (99, 99)))


def _chord_to_text(keys, layout):
    return "".join(layout.get(k, k) for k in _ordered_keys(keys))


# ==================== TXT output ====================

def convert_to_txt(input_path, non_empty_intervals, song_name, duration_str,
                   layout, out_dir, layout_suffix=None):
    base = os.path.splitext(os.path.basename(input_path))[0]
    suffix = f"_{layout_suffix}" if layout_suffix else ""
    output_path = os.path.join(out_dir, base + suffix + '.txt')

    lines = [
        song_name,
        f"Duration: {duration_str} | Chords: {len(non_empty_intervals)}",
        f"Layout: {layout_suffix or 'QWERTZ'}",
        "",
        "Legend:",
        "  - One line = one moment in time (100ms step).",
        "  - Characters on the same line must be pressed TOGETHER.",
        "  - Consecutive lines are pressed one after another.",
        "",
        "-" * 40,
    ]
    for idx, interval in enumerate(non_empty_intervals, start=1):
        chord = _chord_to_text(interval['keys'], layout)
        if len(interval['keys']) == 1:
            hint = f"1 key: {chord}"
        else:
            hint = f"{len(interval['keys'])} keys: " + " + ".join(
                layout.get(k, k) for k in _ordered_keys(interval['keys']))
        lines.append(f"{idx:04d}  {chord:<10} ({hint})")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    return output_path


# ==================== PNG output ====================

def convert_to_png(input_path, non_empty_intervals, song_name, duration_str,
                   layout, out_dir, layout_suffix=None, chords_per_row=4):
    """Render chord sheet as multiple A4-sized PNG pages (150 DPI).

    Returns a list of output paths (one per page).
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return []

    # A4 landscape at 150 DPI: 1754 x 1240 px
    # We leave margins, so usable area is ~1650 x 1100
    PAGE_W = 1754
    PAGE_H = 1240
    MARGIN = 40
    USABLE_W = PAGE_W - 2 * MARGIN
    USABLE_H = PAGE_H - 2 * MARGIN

    # Compact chord cards
    KEY_W, KEY_H = 60, 28
    KEY_GAP, ROW_GAP = 6, 6
    CHORD_W = 5 * KEY_W + 4 * KEY_GAP + 20
    CHORD_H = 3 * KEY_H + 2 * ROW_GAP + 20 + 24
    ARROW_W = 30
    ROW_H = CHORD_H + 20

    # Header only on first page
    HEADER_H = 90

    def _font(size):
        for candidate in ("DejaVuSans-Bold.ttf", "Arial.ttf", "arial.ttf"):
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
        return ImageFont.load_default()

    font_title = _font(22)
    font_info = _font(12)
    font_key = _font(16)
    font_label = _font(11)
    font_page = _font(10)

    # Determine how many chords fit per row
    max_cols = max(1, (USABLE_W + ARROW_W) // (CHORD_W + ARROW_W))
    if chords_per_row is None or chords_per_row > max_cols:
        chords_per_row = max_cols

    # Build groups of chords (one row each)
    groups = [non_empty_intervals[i:i + chords_per_row]
              for i in range(0, len(non_empty_intervals), chords_per_row)]

    # Split groups into pages
    # First page has header, so less space for rows
    rows_first_page = max(1, (USABLE_H - HEADER_H) // ROW_H)
    rows_other_pages = max(1, USABLE_H // ROW_H)

    pages = []
    idx = 0
    while idx < len(groups):
        if not pages:
            capacity = rows_first_page
        else:
            capacity = rows_other_pages
        pages.append(groups[idx:idx + capacity])
        idx += capacity

    total_pages = len(pages)
    base = os.path.splitext(os.path.basename(input_path))[0]
    suffix = f"_{layout_suffix}" if layout_suffix else ""

    outputs = []

    for page_num, page_groups in enumerate(pages, start=1):
        img = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        draw = ImageDraw.Draw(img)

        # Header only on first page
        y_offset = MARGIN
        if page_num == 1:
            draw.text((MARGIN, y_offset), song_name, fill="black", font=font_title)
            y_offset += 32
            draw.text((MARGIN, y_offset),
                      f"Duration: {duration_str} | Chords: {len(non_empty_intervals)} | "
                      f"Layout: {layout_suffix or 'QWERTZ'}",
                      fill="#444", font=font_info)
            y_offset += 22
            draw.text((MARGIN, y_offset),
                      "Press keys on the same card together. Cards go left to right, "
                      "top to bottom.",
                      fill="#666", font=font_info)
            y_offset += 22
            y_offset += 14  # gap before first row
        else:
            y_offset = MARGIN

        # Draw chords for this page
        for gi, group in enumerate(page_groups):
            y = y_offset + gi * ROW_H
            for ci, interval in enumerate(group):
                x = MARGIN + ci * (CHORD_W + ARROW_W)
                draw.rectangle([x, y, x + CHORD_W, y + CHORD_H],
                               outline="#333", width=1, fill="#fafafa")

                ky = y + 10
                for row in ROWS:
                    kx = x + 10
                    for key_id in row:
                        active = key_id in interval['keys']
                        draw.rectangle([kx, ky, kx + KEY_W, ky + KEY_H],
                                       outline="#cc0000" if active else "#666",
                                       width=1,
                                       fill="#ffcccc" if active else "#f0f0f0")
                        ch = layout.get(key_id, key_id)
                        bbox = draw.textbbox((0, 0), ch, font=font_key)
                        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                        draw.text((kx + (KEY_W - tw) / 2 - bbox[0],
                                   ky + (KEY_H - th) / 2 - bbox[1]),
                                  ch, fill="black", font=font_key)
                        kx += KEY_W + KEY_GAP
                    ky += KEY_H + ROW_GAP

                if ci < len(group) - 1:
                    ax = x + CHORD_W + ARROW_W / 2
                    ay = y + CHORD_H / 2
                    draw.text((ax - 6, ay - 8), "→", fill="#0066cc", font=font_key)

            # START / END labels
            if page_num == 1 and gi == 0:
                draw.text((MARGIN, y - 14), "START", fill="#006600", font=font_label)
            if page_num == total_pages and gi == len(page_groups) - 1:
                last_x = MARGIN + (len(group) - 1) * (CHORD_W + ARROW_W)
                draw.text((last_x + CHORD_W - 30, y - 14), "END",
                          fill="#cc0000", font=font_label)

        # Footer: page number + branding
        footer_text = (
            f"Generated by SkySheet Converter – {time.strftime('%Y')}   "
            f"Page {page_num} / {total_pages}"
        )
        draw.text((MARGIN, PAGE_H - MARGIN - 15), footer_text,
                  fill="#888", font=font_page)

        # Save
        if total_pages == 1:
            out_path = os.path.join(out_dir, base + suffix + '.png')
        else:
            out_path = os.path.join(out_dir, base + suffix + f'_{page_num}.png')
        img.save(out_path)
        outputs.append(out_path)

    return outputs


# ==================== HTML output ====================

def _convert_to_html(input_path, song_name, safe_song_name, subtitle,
                     processed_notes, non_empty_intervals, duration_str,
                     translations, layouts, has_custom, out_dir):
    current_year = time.strftime('%Y')
    layouts_js = json.dumps(layouts, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{song_name}</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: 'Arial', sans-serif;
    display: flex; flex-direction: column; min-height: 100vh;
    padding: 20px; background-color: #121212; color: #e0e0e0; position: relative;
}}
.container {{ max-width: 1400px; margin: 0 auto; padding: 20px; flex: 1; }}
h1 {{ text-align: center; color: #4fc3f7; margin-bottom: 10px; font-size: 2.8em; }}
.author {{ text-align: center; color: #aaa; margin-bottom: 15px; font-size: 18px; }}
.file-info {{ text-align: center; margin-bottom: 30px; color: #aaa; font-size: 18px; }}
.legend {{
    text-align: center; margin: 0 auto 30px auto; padding: 15px;
    background: #1e1e1e; border-radius: 8px; max-width: 600px; font-size: 18px;
}}
.timeline-container {{
    position: relative; background-color: #1e1e1e; border-radius: 12px;
    padding: 20px; height: 70vh; overflow-y: auto;
}}
.timeline {{ display: flex; flex-direction: column; gap: 20px; }}
.chord-row {{ display: flex; justify-content: center; align-items: center; gap: 20px; }}
.chord-container {{ display: flex; flex-direction: column; align-items: center; }}
.chord-label {{
    text-align: center; font-weight: bold; margin-bottom: 10px;
    height: 20px; color: #81c784; font-size: 16px;
}}
.chord {{
    display: flex; flex-direction: column; border: 2px solid #333;
    padding: 15px 10px; border-radius: 8px; background-color: #2a2a2a; min-width: 260px;
}}
.keyboard {{ display: flex; flex-direction: column; gap: 10px; }}
.row {{ display: flex; justify-content: center; gap: 10px; }}
.key {{
    width: 90px; height: 35px; border: 2px solid #444; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-weight: bold; background-color: #333; user-select: none;
    font-size: 24px; color: #ddd;
}}
.key.active {{ background-color: #f44336 !important; color: white !important; border-color: #d32f2f !important; }}
.key-label {{ font-size: 24px; pointer-events: none; }}
.arrow {{ font-size: 24px; color: #4fc3f7; min-width: 30px; text-align: center; }}
footer {{
    margin-top: auto; padding: 10px 20px; text-align: center;
    color: #aaa; font-size: 14px; border-top: 1px solid #333;
}}
footer a {{ color: #4fc3f7; text-decoration: none; }}
.settings-menu {{
    position: fixed; left: 20px; top: 20px; z-index: 1000;
    background: #2a2a2a; padding: 15px; border-radius: 8px;
    display: flex; flex-direction: column; gap: 15px; min-width: 200px;
}}
.setting-group {{ display: flex; flex-direction: column; gap: 5px; }}
.setting-label {{ color: #fff; font-weight: bold; margin-bottom: 3px; }}
.setting-select {{ padding: 8px; border-radius: 5px; background: #444; color: white; border: 1px solid #666; cursor: pointer; }}
.print-btn {{
    padding: 12px 24px; background: #4fc3f7; color: white; border: none;
    border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold;
    width: 100%; text-align: center;
}}
@media print {{
    @page {{
        margin: 1.5cm 0.5cm 0.8cm 0.5cm;
        @top-center {{ content: "{safe_song_name}"; font-size: 16pt; font-weight: bold; }}
        @bottom-center {{ content: "\\00A9 {current_year} | Page " counter(page); font-size: 11pt; font-weight: bold; }}
    }}
    @page :first {{ @top-center {{ content: ""; }} }}
    body {{ background: white !important; padding: 5px !important; color: #000 !important; font-size: 10pt; }}
    .container {{ max-width: 100% !important; padding: 0 !important; }}
    .timeline-container {{ height: auto !important; overflow: visible !important; padding: 10px !important; background: white !important; border: none !important; }}
    .chord-row {{ page-break-inside: avoid; gap: 10px; margin-bottom: 15px; }}
    .chord {{ border: 1px solid #999 !important; padding: 10px !important; background: white !important; min-width: 260px !important; }}
    .key {{ background: #f8f8f8 !important; color: #000 !important; border: 1px solid #666 !important; font-size: 20pt !important; width: 80px !important; height: 35px !important; }}
    .key.active {{ background: #ffe6e6 !important; border: 2px solid #cc0000 !important; }}
    h1 {{ color: #000 !important; font-size: 22pt !important; }}
    .author, .file-info, .legend {{ color: #000 !important; background: white !important; border: 1px solid #ddd !important; font-size: 12pt; padding: 8px !important; }}
    .settings-menu, footer {{ display: none !important; }}
    .arrow {{ color: #000 !important; font-size: 18pt; }}
}}
</style>
<script>
const notesCount = {len(processed_notes)};
const durationStr = {json.dumps(duration_str)};
const layouts = {layouts_js};
const hasCustomLayout = {str(has_custom).lower()};

const langLayoutMap = {{
    "de": "QWERTZ", "en": "QWERTY", "fr": "AZERTY",
    "es": "QWERTY", "ru": "RUSSIAN", "ar": "ARABIC", "ja": "JIS"
}};

const translations = {json.dumps(translations, ensure_ascii=False)};
let currentLanguage = "en";
let currentLayout = Object.keys(layouts).includes("QWERTZ") ? "QWERTZ" : Object.keys(layouts)[0];

function applyTranslations() {{
    const langData = translations[currentLanguage] || {{}};
    const currentYear = new Date().getFullYear();
    document.querySelectorAll('[data-translate]').forEach(el => {{
        const key = el.getAttribute('data-translate');
        if (!key || !langData[key]) return;
        el.innerHTML = langData[key]
            .replace(/{{notes_count}}/g, notesCount)
            .replace(/{{duration}}/g, durationStr)
            .replace(/{{year}}/g, currentYear);
    }});
    const btn = document.querySelector('.print-btn');
    if (btn && langData['print']) btn.textContent = langData['print'];
    if (langData['language']) document.querySelector('.lang-label').textContent = langData['language'];
    if (langData['keyboard']) document.querySelector('.layout-label').textContent = langData['keyboard'];
}}

function changeLanguage(lang) {{
    currentLanguage = lang;
    applyTranslations();
    const suggested = langLayoutMap[lang];
    if (suggested && layouts[suggested]) {{
        changeLayout(suggested);
        document.getElementById("layout-select").value = suggested;
    }}
}}

function changeLayout(layout) {{
    if (layout === "CUSTOM" && !hasCustomLayout) {{
        alert("Custom layout file missing!\\n\\nPlease create 'custom.xml' next to the application.\\nSee the wiki for instructions: https://github.com/VanilleIce/SkySheet-to-HTML-Converter/wiki/Custom-Layouts");
        const fallback = (currentLayout !== "CUSTOM" && layouts[currentLayout]) ? currentLayout : Object.keys(layouts)[0];
        document.getElementById("layout-select").value = fallback;
        changeLayout(fallback);
        return;
    }}
    currentLayout = layout;
    document.querySelectorAll('.key').forEach(key => {{
        const keyId = key.getAttribute('data-key');
        const newChar = layouts[layout] && layouts[layout][keyId];
        if (newChar) key.querySelector('.key-label').textContent = newChar;
    }});
}}

document.addEventListener('DOMContentLoaded', function() {{
    const sel = document.getElementById("layout-select");
    sel.innerHTML = "";
    let customShown = false;
    const names = Object.keys(layouts).sort();
    names.forEach(name => {{
        const isCustom = name.toUpperCase() === "CUSTOM";
        if (isCustom) {{
            if (customShown) return;
            customShown = true;
        }}
        const opt = document.createElement("option");
        opt.value = name;
        opt.textContent = isCustom ? "Custom" : name;
        sel.appendChild(opt);
    }});
    if (hasCustomLayout && !customShown) {{
        const opt = document.createElement("option");
        opt.value = "CUSTOM";
        opt.textContent = "Custom";
        sel.appendChild(opt);
        customShown = true;
    }}
    if (!layouts[currentLayout]) {{
        currentLayout = Object.keys(layouts).find(k => k.toUpperCase() !== "CUSTOM") || "QWERTZ";
    }}
    sel.value = currentLayout;

    changeLanguage("en");
    changeLayout(currentLayout);

    document.getElementById("language-select").addEventListener("change", function() {{ changeLanguage(this.value); }});
    document.getElementById("layout-select").addEventListener("change", function() {{ changeLayout(this.value); }});
}});
</script>
</head>
<body>
<div class="settings-menu">
    <div class="setting-group">
        <div class="setting-label lang-label" data-translate="language">Language</div>
        <select id="language-select" class="setting-select">
            <option value="de">Deutsch</option>
            <option value="en" selected>English</option>
            <option value="fr">Français</option>
            <option value="es">Español</option>
            <option value="ru">Русский</option>
            <option value="ar">العربية</option>
            <option value="ja">日本語</option>
        </select>
    </div>
    <div class="setting-group">
        <div class="setting-label layout-label" data-translate="keyboard">Keyboard</div>
        <select id="layout-select" class="setting-select"></select>
    </div>
    <button class="print-btn" onclick="window.print()" data-translate="print">Print</button>
</div>

<div class="container">
    <h1>{song_name}</h1>"""

    if subtitle:
        html += f'\n    <div class="author">{subtitle}</div>'

    html += f"""
    <div class="file-info" data-translate="notes">Notes: {len(processed_notes)} | Duration: {duration_str}</div>
    <div class="legend" data-translate="legend">Keyboard Legend: The keys highlighted in red must be pressed simultaneously</div>
    <div class="timeline-container"><div class="timeline">"""

    chords_per_row = 2
    groups = [non_empty_intervals[i:i + chords_per_row]
              for i in range(0, len(non_empty_intervals), chords_per_row)]

    initial = layouts.get("QWERTZ") or next(iter(layouts.values()))

    for gi, group in enumerate(groups):
        html += '<div class="chord-row">'
        for i, interval in enumerate(group):
            if gi == 0 and i == 0:
                label, tkey = "START", "start"
            elif gi == len(groups) - 1 and i == len(group) - 1:
                label, tkey = "END", "end"
            else:
                label, tkey = "", ""

            attr = f' data-translate="{tkey}"' if tkey else ""
            html += f"""
        <div class="chord-container">
            <div class="chord-label"{attr}>{label}</div>
            <div class="chord"><div class="keyboard">"""
            for row_keys in ROWS:
                html += '<div class="row">'
                for key_id in row_keys:
                    active = "active" if key_id in interval['keys'] else ""
                    html += (f'<div class="key {active}" data-key="{key_id}">'
                             f'<span class="key-label">{initial.get(key_id, "")}</span></div>')
                html += '</div>'
            html += "</div></div></div>"
            if i < len(group) - 1:
                html += '<div class="arrow">→</div>'
        html += '</div>'

    html += """
    </div></div>
</div>
<footer data-translate="footer"></footer>
</body>
</html>"""

    base = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(out_dir, base + '.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return output_path


# ==================== Core conversion ====================

def convert_file(input_path, make_html=True, make_txt=True, make_png=True,
                 layout_names=None, log=None):
    if log is None:
        log = lambda msg: None

    log("Loading translations...")
    translations = load_translations()

    log("Loading layouts...")
    layouts, has_custom = load_layouts()
    log(f"Found {len(layouts)} layout(s): {', '.join(sorted(layouts.keys()))}")

    ext = os.path.splitext(input_path)[1].lower()
    log(f"Reading '{os.path.basename(input_path)}' (format: {ext})...")
    try:
        data = load_skysheet_file(input_path)
    except ValueError as e:
        raise ValueError(f"Could not load file: {e}")

    if not isinstance(data, list) or not data:
        raise ValueError(
            f"Unexpected format – the file should be a .json, .skysheet or .txt "
            f"exported from SkySheet (expected a non-empty list)."
        )

    song_data = data[0]
    raw_name = song_data.get('name', '') or os.path.splitext(os.path.basename(input_path))[0]
    song_name = safe_html(raw_name)
    safe_song_name = (raw_name
                      .replace('\\', '\\\\')
                      .replace('"', '\\"')
                      .replace("'", "\\'"))

    author = safe_html(song_data.get('author'))
    transcribed_by = safe_html(song_data.get('transcribedBy'))
    parts = []
    if author: parts.append(f"Author: {author}")
    if transcribed_by: parts.append(f"Transcribed by: {transcribed_by}")
    subtitle = " | ".join(parts) if parts else None

    log("Parsing notes...")
    try:
        processed, min_t, max_t = _prepare_processed_notes(song_data)
    except ValueError as e:
        raise ValueError(str(e))

    dur = (max_t - min_t) / 1000.0
    duration_str = f"{int(dur // 60)} min {int(dur % 60)} sec"
    log(f"Song: '{raw_name}' | {len(processed)} notes | {duration_str}")

    intervals = _build_intervals(processed, min_t, max_t)
    log(f"Built {len(intervals)} chord(s) from notes.")

    out_dir = make_output_dir(raw_name)
    log(f"Output folder: {out_dir}")

    if layout_names is None:
        layout_names = [PREFERRED_DEFAULT] if PREFERRED_DEFAULT in layouts else [next(iter(layouts))]
    valid = []
    for ln in layout_names:
        key = ln.upper()
        if key in layouts:
            valid.append(key)
        else:
            log(f"Warning: unknown layout '{ln}' – skipping.")
    if not valid:
        valid = [PREFERRED_DEFAULT] if PREFERRED_DEFAULT in layouts else [next(iter(layouts))]

    multi = len(valid) > 1
    outputs = []

    for lname in valid:
        layout_data = layouts[lname]
        suffix = lname if multi else None
        if make_txt:
            log(f"Writing TXT ({lname})...")
            outputs.append(convert_to_txt(input_path, intervals, raw_name,
                                          duration_str, layout_data, out_dir, suffix))
        if make_png:
            log(f"Writing PNG ({lname})...")
            png_paths = convert_to_png(input_path, intervals, raw_name, duration_str,
                                       layout_data, out_dir, suffix)
            if png_paths:
                outputs.extend(png_paths)
                log(f"  -> {len(png_paths)} page(s)")
            else:
                log("  (Pillow missing – PNG skipped)")

    if make_html:
        log("Writing HTML...")
        outputs.append(_convert_to_html(
            input_path, song_name, safe_song_name, subtitle,
            processed, intervals, duration_str,
            translations, layouts, has_custom, out_dir))

    return outputs, raw_name


# ==================== GUI ====================

class ConverterApp:
    """SkySheet Converter - customtkinter GUI."""

    def __init__(self, initial_file=None):
        self.selected_file = initial_file
        self.busy = False
        self.out_dir = None
        self.layout_vars = {}

        self.layouts, self.has_custom = load_layouts()

        self._init_gui()
        self._create_gui_components()
        self._setup_gui_layout()

        if initial_file:
            self._update_file_info()

    # ----- GUI init ------------------------------------------------------

    def _init_gui(self):
        self.root = ctk.CTk()
        self.root.title(f"SkySheet Converter – {SUPPORTED_LABEL}")
        self.root.protocol('WM_DELETE_WINDOW', self._shutdown)
        self.root.resizable(False, False)

        icon_path = resource_path("icon.ico")
        if Path(icon_path).exists():
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        ctk.set_appearance_mode("dark")

        try:
            self.root.geometry(f"{DEFAULT_WINDOW_SIZE[0]}x{DEFAULT_WINDOW_SIZE[1]}")
        except Exception:
            pass

    def _create_button(self, text, command, width=MAIN_BUTTON_WIDTH, height=40, main=True):
        return ctk.CTkButton(
            self.root,
            text=text,
            command=command,
            font=("Arial", 13 if main else 12),
            width=width,
            height=height,
        )

    def _create_gui_components(self):
        # ============================================================
        # File button – built as a Frame + Label for perfect centering
        # ============================================================
        self.file_btn_frame = ctk.CTkFrame(
            self.root,
            width=MAIN_BUTTON_WIDTH,
            height=50,
            corner_radius=8,
            fg_color=FILE_BTN_COLOR,
            cursor="hand2",
        )
        self.file_btn_frame.pack_propagate(False)

        self.file_btn_label = ctk.CTkLabel(
            self.file_btn_frame,
            text=f"Select file ({SUPPORTED_LABEL})",
            font=("Arial", 13),
            text_color="#FFFFFF",
            anchor="center",
            justify="center",
        )
        self.file_btn_label.pack(expand=True, fill="both")

        # Make frame + label clickable
        for widget in (self.file_btn_frame, self.file_btn_label):
            widget.bind("<Button-1>", lambda e: self._select_file())

        # Hover effect
        def _on_enter(e=None):
            try:
                self.file_btn_frame.configure(fg_color=FILE_BTN_HOVER)
            except Exception:
                pass

        def _on_leave(e=None):
            try:
                self.file_btn_frame.configure(fg_color=FILE_BTN_COLOR)
            except Exception:
                pass

        for widget in (self.file_btn_frame, self.file_btn_label):
            widget.bind("<Enter>", _on_enter)
            widget.bind("<Leave>", _on_leave)

        # Format card
        self.fmt_card = ctk.CTkFrame(self.root, **CARD_STYLE)

        ctk.CTkLabel(
            self.fmt_card,
            text="Output formats",
            font=("Arial", 13, "bold"),
        ).pack(pady=(8, 4), padx=15, anchor="w")

        self.fmt_html = ctk.BooleanVar(value=True)
        self.fmt_txt = ctk.BooleanVar(value=True)
        self.fmt_png = ctk.BooleanVar(value=True)

        for text, var in [
            ("HTML (interactive)", self.fmt_html),
            ("TXT (chord sheet)", self.fmt_txt),
            ("PNG (printable image)", self.fmt_png),
        ]:
            ctk.CTkCheckBox(
                self.fmt_card,
                text=text,
                variable=var,
                font=("Arial", 13),
                checkbox_width=20,
                checkbox_height=20,
            ).pack(pady=2, padx=20, anchor="w")

        # Layout card
        self.lay_card = ctk.CTkFrame(self.root, **CARD_STYLE)

        ctk.CTkLabel(
            self.lay_card,
            text="Keyboard layouts for TXT / PNG",
            font=("Arial", 13, "bold"),
        ).pack(pady=(8, 4), padx=15, anchor="w")

        self.layout_grid = ctk.CTkFrame(self.lay_card, fg_color="transparent")
        self.layout_grid.pack(pady=2, padx=15, fill="x")
        self._build_layout_checkboxes()

        # Select all/none buttons
        sel_frame = ctk.CTkFrame(self.lay_card, fg_color="transparent")
        sel_frame.pack(pady=(2, 8), padx=15, anchor="w")

        ctk.CTkButton(
            sel_frame, text="All", width=60, height=26,
            font=("Arial", 12),
            command=self._select_all_layouts,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            sel_frame, text="None", width=60, height=26,
            font=("Arial", 12),
            command=self._select_none_layouts,
        ).pack(side="left")

        ctk.CTkLabel(
            self.lay_card,
            text="(HTML always contains all layouts.)",
            font=("Arial", 11),
            text_color=("gray30", "gray70"),
        ).pack(pady=(0, 8), padx=15, anchor="w")

        # Action buttons
        self.convert_btn = ctk.CTkButton(
            self.root,
            text="Convert",
            command=self._do_convert,
            font=("Arial", 14, "bold"),
            width=MAIN_BUTTON_WIDTH,
            height=42,
            fg_color=CONVERT_COLOR,
            hover_color=CONVERT_HOVER,
        )
        self.open_btn = ctk.CTkButton(
            self.root,
            text="Open output folder",
            command=self._open_output,
            font=("Arial", 13),
            width=MAIN_BUTTON_WIDTH,
            height=32,
            state="disabled",
        )

        # Log
        self.log_frame = ctk.CTkFrame(self.root, **CARD_STYLE)
        ctk.CTkLabel(
            self.log_frame,
            text="Log",
            font=("Arial", 13, "bold"),
        ).pack(pady=(8, 4), padx=15, anchor="w")

        self.log_text = ctk.CTkTextbox(
            self.log_frame,
            height=140,
            font=("Consolas", 11),
            wrap="word",
        )
        self.log_text.pack(pady=(0, 8), padx=10, fill="both", expand=True)
        self.log_text.configure(state="disabled")

    def _setup_gui_layout(self):
        # Title
        ctk.CTkLabel(
            self.root,
            text="SkySheet Converter",
            font=("Arial", 20, "bold"),
        ).pack(pady=(18, 4))

        ctk.CTkLabel(
            self.root,
            text=f"Convert {SUPPORTED_LABEL} files to HTML, TXT and PNG.",
            font=("Arial", 12),
            text_color=("gray30", "gray70"),
        ).pack(pady=(0, 12))

        self.file_btn_frame.pack(pady=(0, 12))

        self.fmt_card.pack(pady=(0, CARD_PADY), padx=20, fill="x")
        self.lay_card.pack(pady=(0, CARD_PADY), padx=20, fill="x")

        self.convert_btn.pack(pady=(12, 4))
        self.open_btn.pack(pady=(0, 8))

        self.log_frame.pack(pady=(0, 12), padx=20, fill="both", expand=True)

    # ----- Layout checkboxes --------------------------------------------

    def _build_layout_checkboxes(self):
        for w in self.layout_grid.winfo_children():
            w.destroy()

        self.layout_vars = {}
        normal_names = sorted(n for n in self.layouts.keys() if n.upper() != "CUSTOM")
        has_custom = any(n.upper() == "CUSTOM" for n in self.layouts.keys())

        cols = 2
        for i, name in enumerate(normal_names):
            var = ctk.BooleanVar(value=(name == PREFERRED_DEFAULT))
            self.layout_vars[name] = var
            ctk.CTkCheckBox(
                self.layout_grid,
                text=name,
                variable=var,
                font=("Arial", 12),
                checkbox_width=18,
                checkbox_height=18,
            ).grid(row=i // cols, column=i % cols, sticky="w", padx=(0, 16), pady=2)

        # CUSTOM in its own row, full width, below the grid
        if has_custom:
            row = (len(normal_names) + cols - 1) // cols
            var = ctk.BooleanVar(value=False)
            self.layout_vars["CUSTOM"] = var
            ctk.CTkCheckBox(
                self.layout_grid,
                text="Custom",
                variable=var,
                font=("Arial", 12),
                checkbox_width=18,
                checkbox_height=18,
            ).grid(
                row=row,
                column=0,
                columnspan=cols,
                sticky="w",
                padx=(0, 16),
                pady=(6, 2),
            )

    def _select_all_layouts(self):
        for v in self.layout_vars.values():
            v.set(True)

    def _select_none_layouts(self):
        for v in self.layout_vars.values():
            v.set(False)

    # ----- Log ----------------------------------------------------------

    def _log(self, msg):
        try:
            self.log_text.configure(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
            self.root.update_idletasks()
        except Exception:
            pass

    # ----- File helpers -------------------------------------------------

    def _truncate_filename(self, filename, max_len=26):
        if len(filename) <= max_len:
            return filename
        ext = os.path.splitext(filename)[1]
        name_part = filename[:-len(ext)] if ext else filename
        keep = max_len - len(ext) - 3
        return f"{name_part[:keep]}...{ext}"

    # ----- File selection -----------------------------------------------

    def _select_file(self):
        file = filedialog.askopenfilename(
            title=f"Select a song file ({SUPPORTED_LABEL})",
            filetypes=SUPPORTED_FILETYPES,
        )
        if file:
            self.selected_file = file
            self._update_file_info()

    def _update_file_info(self):
        if not self.selected_file:
            self.file_btn_label.configure(
                text=f"Select file ({SUPPORTED_LABEL})"
            )
            return

        filename = self._truncate_filename(os.path.basename(self.selected_file), 26)

        if not os.path.isfile(self.selected_file):
            self.file_btn_label.configure(
                text=f"⚠  {filename}  (not found)"
            )
            return

        try:
            data = load_skysheet_file(self.selected_file)
            song = data[0] if isinstance(data, list) and data else {}
            name = song.get('name', '') or os.path.splitext(filename)[0]
            notes = song.get('songNotes', [])
            if notes:
                times = [n['time'] for n in notes]
                d = (max(times) - min(times)) / 1000.0
                dur = f"{int(d // 60)}:{int(d % 60):02d}"
            else:
                dur = "0:00"

            self.file_btn_label.configure(
                text=f"{filename}   |   {len(notes)} notes   |   {dur}"
            )
        except Exception:
            self.file_btn_label.configure(
                text=f"⚠  {filename}  (could not read)"
            )

    # ----- Convert ------------------------------------------------------

    def _do_convert(self):
        if self.busy:
            return
        path = self.selected_file
        if not path:
            messagebox.showwarning(
                "No file",
                f"Please select a file first.\n\nSupported formats: {SUPPORTED_LABEL}",
                parent=self.root,
            )
            return
        if not os.path.isfile(path):
            messagebox.showerror(
                "File not found",
                f"File not found:\n{path}\n\nSupported formats: {SUPPORTED_LABEL}",
                parent=self.root,
            )
            return

        mh = self.fmt_html.get()
        mt = self.fmt_txt.get()
        mp = self.fmt_png.get()
        if not (mh or mt or mp):
            messagebox.showwarning(
                "No format",
                "Please select at least one output format.",
                parent=self.root,
            )
            return

        layout_names = [n for n, v in self.layout_vars.items() if v.get()]
        if (mt or mp) and not layout_names:
            messagebox.showwarning(
                "No layout",
                "Please select at least one layout for TXT/PNG.",
                parent=self.root,
            )
            return

        self.busy = True
        self.convert_btn.configure(state="disabled")
        self.open_btn.configure(state="disabled")

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        result_queue = queue.Queue()

        def worker():
            try:
                outs, _ = convert_file(
                    path, mh, mt, mp,
                    layout_names=layout_names or None,
                    log=self._log,
                )
                result_queue.put(("ok", outs))
            except Exception as e:
                import traceback
                result_queue.put(("err", (str(e), traceback.format_exc())))

        threading.Thread(target=worker, daemon=True).start()

        def poll():
            try:
                kind, payload = result_queue.get_nowait()
            except queue.Empty:
                self.root.after(80, poll)
                return

            self.busy = False
            self.convert_btn.configure(state="normal")

            if kind == "ok":
                outs = payload
                if outs:
                    self.out_dir = os.path.dirname(outs[0])
                    self.open_btn.configure(state="normal")
                    self._log("")
                    self._log(f"Done. {len(outs)} file(s) written.")
                    self._log(f"Output folder: {self.out_dir}")
                else:
                    self._log("No output generated.")
            else:
                msg, tb = payload
                self._log("")
                self._log(f"ERROR: {msg}")
                self._log(tb)
                messagebox.showerror("Conversion failed", msg, parent=self.root)

        poll()

    def _open_output(self):
        d = self.out_dir
        if not d or not os.path.isdir(d):
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(d)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", d])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", d])
        except Exception as e:
            messagebox.showerror("Could not open folder", str(e), parent=self.root)

    # ----- Shutdown -----------------------------------------------------

    def _shutdown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        self.root.mainloop()


# ==================== Entry Point ====================

if __name__ == "__main__":
    if os.name == 'nt':
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)

    initial = None
    if len(sys.argv) >= 2:
        candidate = sys.argv[1]
        if os.path.isfile(candidate):
            initial = candidate

    try:
        app = ConverterApp(initial_file=initial)
        app.run()
    except Exception as e:
        try:
            import traceback
            messagebox.showerror(
                "Critical Error",
                f"The application encountered a critical error:\n\n{e}\n\n"
                f"{traceback.format_exc()}",
            )
        except Exception:
            print(f"Critical Error: {e}", file=sys.stderr)