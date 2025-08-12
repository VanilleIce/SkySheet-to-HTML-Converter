# Copyright (C) 2025 VanilleIce

import json
import math
import os
import sys
import time
import xml.etree.ElementTree as ET

# Wiki URL for custom layouts
CUSTOM_LAYOUT_WIKI_URL = "https://github.com/VanilleIce/SkySheet-to-HTML-Converter/wiki/Custom-Layouts"

# Keyboard rows configuration
ROWS = [
    ["Key0", "Key1", "Key2", "Key3", "Key4"],
    ["Key5", "Key6", "Key7", "Key8", "Key9"],
    ["Key10", "Key11", "Key12", "Key13", "Key14"]
]

# Default QWERTZ layout
DEFAULT_LAYOUT = {
    "Key0": "z", "Key1": "u", "Key2": "i", "Key3": "o", "Key4": "p",
    "Key5": "h", "Key6": "j", "Key7": "k", "Key8": "l", "Key9": "ö",
    "Key10": "n", "Key11": "m", "Key12": ",", "Key13": ".", "Key14": "-"
}

def resource_path(relative_path):
    """Get absolute path to resource for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def parse_key(raw_key):
    """Extract pure key name from JSON entry (e.g. 'NoteKey3' -> 'Key3')"""
    return "Key" + raw_key.split("Key")[1]

def load_translations():
    """Load all translation XML files from lang/ directory"""
    translations = {}
    lang_dir = resource_path('lang')
    
    if not os.path.exists(lang_dir):
        return translations
    
    for lang_file in os.listdir(lang_dir):
        if lang_file.endswith(".xml"):
            lang_code = os.path.splitext(lang_file)[0]
            try:
                tree = ET.parse(os.path.join(lang_dir, lang_file))
                root = tree.getroot()
                lang_data = {}
                for element in root:
                    lang_data[element.tag] = element.text
                translations[lang_code] = lang_data
            except Exception:
                pass
    return translations

def load_custom_layout():
    """Load custom keyboard layout from custom.xml in executable directory"""
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    
    custom_path = os.path.join(script_dir, "custom.xml")
    
    if os.path.exists(custom_path):
        try:
            tree = ET.parse(custom_path)
            root = tree.getroot()
            custom_layout = {}
            for key in root.findall('key'):
                key_id = key.attrib['id']
                custom_layout[key_id] = key.text
            return custom_layout
        except Exception as e:
            print(f"Error loading custom layout: {str(e)}")
            return None
    return None

def load_skysheet_file(file_path):
    """Load SkySheet file with robust encoding detection"""
    # First try UTF-16 with BOM support
    try:
        with open(file_path, 'r', encoding='utf-16') as f:
            return json.load(f)
    except UnicodeDecodeError:
        pass
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")
    
    # Then try UTF-8 with BOM support
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except UnicodeDecodeError:
        pass
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")
    
    # Finally try UTF-8 without BOM
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Unsupported file encoding: {str(e)}")

def convert_file(input_path):
    """Convert SkySheet file to interactive HTML"""
    # Load translations and custom layout
    translations = load_translations()
    custom_layout = load_custom_layout()
    has_custom_layout = custom_layout is not None
    
    # Load song data with encoding detection
    try:
        data = load_skysheet_file(input_path)
    except ValueError as e:
        print(f"Error loading file: {str(e)}")
        sys.exit(1)
    
    song_data = data[0]
    notes = song_data['songNotes']
    song_name = song_data.get('name', '')
    
    # Use filename if song name is missing
    if not song_name:
        song_name = os.path.splitext(os.path.basename(input_path))[0]
    
    # Get author and transcribedBy if available
    author = song_data.get('author')
    transcribed_by = song_data.get('transcribedBy')
    
    # Format subtitle with labels
    subtitle_parts = []
    if author:
        subtitle_parts.append(f"Author: {author}")
    if transcribed_by:
        subtitle_parts.append(f"Transcribed by: {transcribed_by}")
    subtitle = " | ".join(subtitle_parts) if subtitle_parts else None

    safe_song_name = song_name.replace('"', '\\"').replace("'", "\\'")
    
    # Process notes
    processed_notes = []
    for note in notes:
        key_id = parse_key(note['key'])
        processed_notes.append({
            'key': key_id,
            'time': note['time']
        })
    
    # Calculate duration
    min_time = min(note['time'] for note in processed_notes)
    max_time = max(note['time'] for note in processed_notes)
    duration_sec = (max_time - min_time) / 1000.0
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration_str = f"{minutes} min {seconds} sec"
    
    # Create intervals (100ms steps)
    INTERVAL_SIZE = 100
    intervals = []
    current = min_time
    while current <= max_time:
        intervals.append({
            'start': current,
            'end': current + INTERVAL_SIZE,
            'keys': set()
        })
        current += INTERVAL_SIZE
    
    # Assign notes to intervals
    for note in processed_notes:
        interval_index = math.floor((note['time'] - min_time) / INTERVAL_SIZE)
        if 0 <= interval_index < len(intervals):
            intervals[interval_index]['keys'].add(note['key'])
    
    # Filter non-empty intervals
    non_empty_intervals = [interval for interval in intervals if interval['keys']]
    
    # Prepare HTML content
    current_year = time.strftime('%Y')
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{song_name}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: 'Arial', sans-serif;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            padding: 20px;
            background-color: #121212;
            color: #e0e0e0;
            position: relative;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            flex: 1;
        }}
        h1 {{
            text-align: center;
            color: #4fc3f7;
            margin-bottom: 10px;
            font-size: 2.8em;
        }}
        .author {{
            text-align: center;
            color: #aaa;
            margin-bottom: 15px;
            font-size: 18px;
        }}
        .file-info {{
            text-align: center;
            margin-bottom: 30px;
            color: #aaa;
            font-size: 18px;
        }}
        .legend {{
            text-align: center;
            margin: 0 auto 30px auto;
            padding: 15px;
            background: #1e1e1e;
            border-radius: 8px;
            max-width: 600px;
            font-size: 18px;
        }}
        .timeline-container {{
            position: relative;
            background-color: #1e1e1e;
            border-radius: 12px;
            padding: 20px;
            height: 70vh;
            overflow-y: auto;
        }}
        .timeline {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .chord-row {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
        }}
        .chord-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .chord-label {{
            text-align: center;
            font-weight: bold;
            margin-bottom: 10px;
            height: 20px;
            color: #81c784;
            font-size: 16px;
        }}
        .chord {{
            display: flex;
            flex-direction: column;
            border: 2px solid #333;
            padding: 15px 10px;
            border-radius: 8px;
            background-color: #2a2a2a;
            min-width: 260px;
        }}
        .keyboard {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .row {{
            display: flex;
            justify-content: center;
            gap: 10px;
        }}
        .key {{
            width: 90px;
            height: 35px;
            border: 2px solid #444;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            background-color: #333;
            user-select: none;
            font-size: 24px;
            color: #ddd;
        }}
        .key.active {{
            background-color: #f44336;
            color: white;
            border-color: #d32f2f;
        }}
        .key-label {{
            font-size: 24px;
            pointer-events: none;
        }}
        .arrow {{
            font-size: 24px;
            color: #4fc3f7;
            min-width: 30px;
            text-align: center;
        }}
        footer {{
            margin-top: auto;
            padding: 10px 20px;
            text-align: center;
            color: #aaa;
            font-size: 14px;
            border-top: 1px solid #333;
        }}
        footer a {{
            color: #4fc3f7;
            text-decoration: none;
        }}
        .settings-menu {{
            position: fixed;
            left: 20px;
            top: 20px;
            z-index: 1000;
            background: #2a2a2a;
            padding: 15px;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            min-width: 200px;
        }}
        .setting-group {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        .setting-label {{
            color: #fff;
            font-weight: bold;
            margin-bottom: 3px;
        }}
        .setting-select {{
            padding: 8px;
            border-radius: 5px;
            background: #444;
            color: white;
            border: 1px solid #666;
            cursor: pointer;
        }}
        .print-btn {{
            padding: 12px 24px;
            background: #4fc3f7;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            width: 100%;
            text-align: center;
        }}
        @media print {{
            @page {{
                margin-top: 1.5cm;
                margin-bottom: 0.8cm;
                margin-left: 0.5cm;
                margin-right: 0.5cm;
                size: auto;
                @top-center {{
                    content: "{safe_song_name}";
                    font-size: 16pt;
                    color: #000;
                    font-weight: bold;
                }}
                @bottom-center {{
                    content: "© {current_year} | Support my work on GitHub | Page " counter(page);
                    font-size: 11pt;
                    color: #000;
                    font-weight: bold;
                }}
            }}
            
            @page :first {{
                @top-center {{
                    content: "";
                }}
            }}
            
            body {{
                background-color: white !important;
                padding: 5px !important;
                padding-top: 0.5cm !important;
                color: #000 !important;
                font-size: 10pt;
            }}
            .container {{
                max-width: 100% !important;
                padding: 0 !important;
            }}
            .timeline-container {{
                height: auto !important;
                overflow: visible !important;
                padding: 10px !important;
                background-color: white !important;
                border: none !important;
            }}
            .timeline {{
                gap: 10px;
            }}
            .chord-row {{
                page-break-inside: avoid;
                gap: 10px;
                margin-bottom: 15px;
            }}
            .chord {{
                border: 1px solid #999 !important;
                padding: 10px !important;
                background-color: white !important;
                min-width: 260px !important;
            }}
            .key {{
                background-color: #f8f8f8 !important;
                color: #000 !important;
                border: 1px solid #666 !important;
                font-size: 20pt !important;
                width: 80px !important;
                height: 35px !important;
                line-height: 35px !important;
            }}
            .key.active {{
                background-color: #ffe6e6 !important;
                border: 2px solid #cc0000 !important;
            }}
            .key-label {{
                text-align: center !important;
            }}
            h1 {{
                color: #000 !important;
                font-size: 22pt !important;
                margin-bottom: 5px !important;
                margin-top: 0.5cm !important;
            }}
            .author, .file-info, .legend {{
                color: #000 !important;
                background-color: white !important;
                border: 1px solid #ddd !important;
                font-size: 12pt;
                padding: 8px !important;
                margin-bottom: 15px !important;
            }}
            .legend {{
                margin-bottom: 15px !important;
            }}
            .settings-menu {{
                display: none !important;
            }}
            .arrow {{
                color: #000 !important;
                font-size: 18pt;
            }}
            body::before, body::after {{
                display: none !important;
            }}
            footer {{
                display: none !important;
            }}
        }}
    </style>
    <script>
        // Global variables for translation data
        const notesCount = {len(processed_notes)};
        const durationStr = {json.dumps(duration_str)};
        
        // Layout definitions
        const layouts = {{
            "QWERTZ": {json.dumps(DEFAULT_LAYOUT)},
            "QWERTY": {{
                "Key0": "y", "Key1": "u", "Key2": "i", "Key3": "o", "Key4": "p",
                "Key5": "h", "Key6": "j", "Key7": "k", "Key8": "l", "Key9": ";",
                "Key10": "n", "Key11": "m", "Key12": ",", "Key13": ".", "Key14": "/"
            }},
            "AZERTY": {{
                "Key0": "y", "Key1": "u", "Key2": "i", "Key3": "o", "Key4": "p",
                "Key5": "h", "Key6": "j", "Key7": "k", "Key8": "l", "Key9": "m",
                "Key10": "b", "Key11": "n", "Key12": ",", "Key13": ";", "Key14": ":"
            }},
            "ARABIC": {{
                "Key0": "ش", "Key1": "س", "Key2": "ي", "Key3": "ب", "Key4": "ل",
                "Key5": "ا", "Key6": "ت", "Key7": "ن", "Key8": "م", "Key9": "ك",
                "Key10": "ط", "Key11": "ئ", "Key12": "ء", "Key13": "ض", "Key14": "ظ"
            }},
            "JIS": {{
                "Key0": "た", "Key1": "て", "Key2": "い", "Key3": "す", "Key4": "か",
                "Key5": "ん", "Key6": "な", "Key7": "に", "Key8": "ら", "Key9": "せ",
                "Key10": "ゆ", "Key11": "も", "Key12": "る", "Key13": "け", "Key14": "く"
            }},
            "RUSSIAN": {{
                "Key0": "й", "Key1": "ц", "Key2": "у", "Key3": "к", "Key4": "е",
                "Key5": "н", "Key6": "г", "Key7": "ш", "Key8": "щ", "Key9": "з",
                "Key10": "ф", "Key11": "ы", "Key12": "в", "Key13": "а", "Key14": "п"
            }}"""
    
    # Add custom layout if available
    if has_custom_layout:
        html_content += f""",
            "CUSTOM": {json.dumps(custom_layout)}"""
    
    html_content += f"""
        }};
        
        // Language-layout mapping
        const langLayoutMap = {{
            "de": "QWERTZ",
            "en": "QWERTY",
            "fr": "AZERTY",
            "es": "QWERTY",
            "ru": "RUSSIAN",
            "ar": "ARABIC",
            "ja": "JIS"
        }};
        
        // Translation dictionary
        const translations = {json.dumps(translations)};
        let currentLanguage = "en";
        let currentLayout = "QWERTZ";
        
        // Change language
        function changeLanguage(lang) {{
            currentLanguage = lang;
            applyTranslations();
            
            // Auto-select layout for language
            const suggestedLayout = langLayoutMap[lang] || "QWERTY";
            changeLayout(suggestedLayout);
            document.getElementById("layout-select").value = suggestedLayout;
        }}
        
        // Change keyboard layout
        function changeLayout(layout) {{
            // Check for custom layout file
            if (layout === "CUSTOM") {{
                if (!layouts.CUSTOM) {{
                    alert("Custom layout file missing!\\n\\n" +
                          "Please create 'custom.xml' next to the application.\\n" +
                          "See the wiki for instructions: {CUSTOM_LAYOUT_WIKI_URL}");
                    document.getElementById("layout-select").value = "QWERTZ";
                    return;
                }}
            }}
            
            currentLayout = layout;
            document.querySelectorAll('.key').forEach(key => {{
                const keyId = key.getAttribute('data-key');
                const newChar = layouts[layout][keyId];
                if (newChar) {{
                    key.querySelector('.key-label').textContent = newChar;
                }}
            }});
        }}
        
        // Apply translations
        function applyTranslations() {{
            const langData = translations[currentLanguage] || {{}};
            const currentYear = new Date().getFullYear();
            
            // Update UI elements
            document.querySelectorAll('[data-translate]').forEach(el => {{
                const key = el.getAttribute('data-translate');
                if (langData[key]) {{
                    let text = langData[key]
                        .replace("{{notes_count}}", notesCount)
                        .replace("{{duration}}", durationStr)
                        .replace("{{year}}", currentYear);
                    el.innerHTML = text;
                }}
            }});

            // Update print button text
            const printBtn = document.querySelector('.print-btn');
            if (langData['print'] && printBtn) {{
                printBtn.textContent = langData['print'];
            }}
            
            // Update dropdown labels
            if (langData['language']) {{
                document.querySelector('.lang-label').textContent = langData['language'];
            }}
            if (langData['keyboard']) {{
                document.querySelector('.layout-label').textContent = langData['keyboard'];
            }}
        }}
        
        // Initialize on load
        document.addEventListener('DOMContentLoaded', function() {{
            changeLanguage("en");
            changeLayout("QWERTZ");
            
            document.getElementById("language-select").addEventListener("change", function() {{
                changeLanguage(this.value);
            }});
            
            document.getElementById("layout-select").addEventListener("change", function() {{
                changeLayout(this.value);
            }});
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
            <select id="layout-select" class="setting-select">
                <option value="QWERTZ">QWERTZ</option>
                <option value="QWERTY">QWERTY</option>
                <option value="AZERTY">AZERTY</option>
                <option value="ARABIC">العربية</option>
                <option value="JIS">日本語</option>
                <option value="RUSSIAN">Русский</option>
                <option value="CUSTOM">Custom</option>
            </select>
        </div>
        
        <button class="print-btn" onclick="window.print()" data-translate="print">Print</button>
    </div>
    
    <div class="container">
        <h1>{song_name}</h1>"""
    
    # Add author/transcribedBy if available
    if subtitle:
        html_content += f"""
        <div class="author">{subtitle}</div>"""
    
    html_content += f"""
        <div class="file-info" data-translate="notes">
            Notes: {len(processed_notes)} | Duration: {duration_str}
        </div>
        
        <div class="legend" data-translate="legend">
            Keyboard Legend: The keys highlighted in red must be pressed simultaneously
        </div>
        
        <div class="timeline-container">
            <div class="timeline">"""
    
    # Generate chord groups
    chords_per_row = 2
    chord_groups = [non_empty_intervals[i:i+chords_per_row] 
                    for i in range(0, len(non_empty_intervals), chords_per_row)]
    
    for group in chord_groups:
        html_content += '<div class="chord-row">'
        
        for i, interval in enumerate(group):
            # Label START/END
            translate_key = ""
            if i == 0 and group == chord_groups[0]:
                label = "START"
                translate_key = "start"
            elif i == len(group) - 1 and group == chord_groups[-1]:
                label = "END"
                translate_key = "end"
            else:
                label = ""
            
            # Add chord
            html_content += f"""
            <div class="chord-container">
                <div class="chord-label" data-translate="{translate_key}">{label}</div>
                <div class="chord">
                    <div class="keyboard">"""
            
            # Generate keyboard rows
            for row_keys in ROWS:
                html_content += '<div class="row">'
                for key_id in row_keys:
                    key_char = DEFAULT_LAYOUT[key_id]
                    is_active = "active" if key_id in interval['keys'] else ""
                    html_content += f'<div class="key {is_active}" data-key="{key_id}"><span class="key-label">{key_char}</span></div>'
                html_content += '</div>'
            
            html_content += """
                    </div>
                </div>
            </div>"""
            
            # Add arrow between chords
            if i < len(group) - 1:
                html_content += '<div class="arrow">→</div>'
        
        html_content += '</div>'
    
    # Close HTML
    html_content += f"""
            </div>
        </div>
    </div>
    
    <footer data-translate="footer"></footer>
</body>
</html>"""
    
    # Save output
    output_path = os.path.splitext(input_path)[0] + '.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path

if __name__ == "__main__":
    """Command line entry point"""
    if len(sys.argv) < 2:
        print("Usage: python converter.py <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.isfile(input_file):
        print(f"File not found: {input_file}")
        sys.exit(1)
    
    try:
        output_file = convert_file(input_file)
        print(f"HTML file generated: {output_file}")
    except Exception as e:
        print(f"Conversion error: {str(e)}")
        sys.exit(1)