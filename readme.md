SkySheet-to-HTML-Converter
==================

Converts SkySheet JSON files into interactive HTML pages, plain-text chord
sheets, and printable PNG images.

This software is intended for private/personal use only. Any commercial
use is expressly prohibited.

- Commercial use is prohibited
- Redistribution is prohibited (except unmodified, non-commercial)
- Modification is prohibited (except for private use)


Features
--------

- Multilingual UI - 7 built-in translations (de, en, fr, es, ru, ar, ja)
- Multiple keyboard layouts - QWERTZ, QWERTY, AZERTY, ARABIC, JIS, RUSSIAN,
  plus a user-provided custom.xml
- Three output formats:
    .html  - interactive page with layout & language switcher, print-optimised
    .txt   - plain chord sheet (KL MND - one line per 100 ms, letters pressed
             together)
    .png   - printable image of the whole timeline (requires Pillow)
- Print-optimised HTML - page headers, page numbers, white background
- Responsive - works on desktop and mobile browsers


Requirements
------------

- Python 3.10 or higher
- pillow (only for PNG output; install with: pip install pillow)
- pyinstaller (only for building the EXE; install with: pip install pyinstaller)


Installation (from source)
--------------------------

    git clone https://github.com/VanilleIce/SkySheet-to-HTML-Converter.git
    cd SkySheet-to-HTML-Converter
    pip install -r requirements.txt


Usage
-----

Command line:

    python converter.py path/to/file.json              # all formats
    python converter.py path/to/file.json --html       # HTML only
    python converter.py path/to/file.json --txt        # TXT only
    python converter.py path/to/file.json --png        # PNG only
    python converter.py path/to/file.json --all        # all formats (explicit)


Output location:

All output goes into an "output/" folder next to the script (or next to the
EXE when built):

    output/
    └── <Song name from the JSON>/
        ├── file.html
        ├── file.txt
        └── file.png


Drag & drop (Windows):

You can drag a .json file onto converter.py (or onto the built .exe).
The converter will use the file as input.


Custom keyboard layouts
-----------------------

1. Create a file named custom.xml next to converter.py (or next to the
   built .exe).

2. Use this structure:

    <?xml version="1.0"?>
    <layout>
      <key id="Key0">A</key>
      <key id="Key1">B</key>
      <key id="Key2">C</key>
      <key id="Key3">D</key>
      <key id="Key4">E</key>
      <key id="Key5">F</key>
      <key id="Key6">G</key>
      <key id="Key7">H</key>
      <key id="Key8">I</key>
      <key id="Key9">J</key>
      <key id="Key10">K</key>
      <key id="Key11">L</key>
      <key id="Key12">M</key>
      <key id="Key13">N</key>
      <key id="Key14">O</key>
    </layout>

3. The layout will appear as "Custom" in the HTML layout dropdown.

You can also place additional layouts in layouts/*.xml. The filename
(without .xml, uppercased) becomes the dropdown label.


Building the EXE
----------------

    python build.py

The EXE is written to dist/SkySheetConverter.exe. It bundles lang/ and
layouts/ so no extra files are needed next to the EXE - except an optional
custom.xml.


License
-------

Private, non-commercial use only. See the header of converter.py.