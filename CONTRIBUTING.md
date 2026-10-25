CONTRIBUTING
============

Welcome to SkySheet-to-HTML-Converter
-----------------------------

Thank you for considering contributing to SkySheet-to-HTML-Converter. This guide will
help you get started quickly and contribute effectively.


Requirements
------------

- Python 3.10 or higher
- A GitHub account
- pillow (for PNG output; install with: pip install pillow)


Getting Started
---------------

Fork & clone the repository:

1. Go to https://github.com/VanilleIce/SkySheet-to-HTML-Converter and click
   "Fork" in the top right.

2. Clone your fork locally:

    git clone https://github.com/YOUR_USERNAME/SkySheet-to-HTML-Converter.git
    cd SkySheet-to-HTML-Converter

Install dependencies:

    pip install -r requirements.txt


Project Layout
--------------

    converter.py        Main script
    build.py            PyInstaller build script
    requirements.txt    Python dependencies
    lang/*.xml          UI translations (de, en, fr, es, ru, ar, ja)
    layouts/*.xml       Keyboard layouts (QWERTZ, QWERTY, ...)
    custom.xml          Optional user-provided layout (next to converter.py)


Testing
-------

Tests are mandatory before any pull request is submitted.

Please verify the following manually:

    python converter.py path/to/sample.json

Make sure:

- All three outputs are generated (HTML, TXT, PNG)
- The HTML opens in a browser and shows the song
- Language switcher and layout switcher work
- Print preview looks reasonable
- No new errors are introduced
- Translations follow the required structure (see below)


Submitting Contributions
------------------------

1. Create a feature branch:

    git checkout -b feature/my-feature

2. Make your changes locally.

3. Ensure they work and are tested.

4. Use clear and descriptive commit messages, such as:

    feat: added new Italian language file
    fix: corrected XML error in lang/de.xml
    docs: updated README with new screenshots

5. Push to your fork:

    git push origin feature/my-feature

6. Submit a pull request via GitHub.

Note: Both main and dev branches are protected. Contributions require CLA
agreement (see below) and manual review by maintainers.


Contributor License Agreement (CLA)
-----------------------------------

By submitting a pull request, you agree to the following terms:

1. Copyright License

You grant VanilleIce a perpetual, worldwide, non-exclusive, royalty-free,
irrevocable license to:

- Use, reproduce, modify, and distribute your contribution
- Sublicense your contribution under the SkySheet-to-HTML-Converter license
- Include your contribution in commercial or non-commercial versions of
  SkySheet-to-HTML-Converter

2. Ownership

You retain copyright ownership of your contribution. This CLA does not
transfer ownership - it grants the Author a license to use it.

3. Representations

You confirm that:

- You have the legal right to grant this license
- Your contribution does not infringe any third-party rights
- Your contribution is your original work, or you have permission to submit it

4. No Compensation

Contributions are voluntary and unpaid. You receive no compensation for your
contribution.

5. Project License

Your contribution will be licensed under the SkySheet-to-HTML-Converter proprietary
license (see TERMS OF USE). You agree that the Author may change the license
in the future.


Adding Translations
-------------------

1. Create a new file in lang/, e.g. lang/it.xml (use the ISO 639-1 language
   code as filename).

2. Use this structure:

    <?xml version="1.0" encoding="UTF-8"?>
    <translations>
        <language>Lingua</language>
        <keyboard>Tastiera</keyboard>
        <notes>Note: {notes_count} | Durata: {duration}</notes>
        <legend>Legenda tastiera: i tasti evidenziati in rosso in un accordo
                devono essere premuti contemporaneamente</legend>
        <start>INIZIO</start>
        <end>FINE</end>
        <print>Stampa</print>
        <footer>&amp;copy; {year} | Supporta il mio lavoro su &lt;a
                href="https://github.com/VanilleIce/SkySheet-to-HTML-Converter"
                target="_blank" rel="noopener"&gt;GitHub&lt;/a&gt;</footer>
    </translations>

   Important: use &amp;, &lt;, &gt; for special characters, and keep the
   placeholders {notes_count}, {duration}, {year} intact.

3. No code change is needed - the language is picked up automatically from
   the filename.

4. Test the translation by opening the generated HTML and selecting the new
   language in the dropdown.


Adding Keyboard Layouts
-----------------------

1. Create a new file in layouts/, e.g. layouts/DVORAK.xml.

2. Use this structure:

    <?xml version="1.0" encoding="UTF-8"?>
    <layout>
        <key id="Key0">p</key>
        <key id="Key1">y</key>
        <key id="Key2">f</key>
        <key id="Key3">g</key>
        <key id="Key4">c</key>
        <key id="Key5">r</key>
        <key id="Key6">l</key>
        <key id="Key7">a</key>
        <key id="Key8">o</key>
        <key id="Key9">e</key>
        <key id="Key10">u</key>
        <key id="Key11">i</key>
        <key id="Key12">d</key>
        <key id="Key13">h</key>
        <key id="Key14">t</key>
    </layout>

3. The filename (without .xml, uppercased) becomes the dropdown label.

4. If your layout is not a standard one, you may also need to add an entry
   to langLayoutMap in converter.py so that the language switcher suggests
   the right layout.


Bug Reports & Feature Requests
------------------------------

Reporting Bugs:

- Clearly describe the issue
- Include reproduction steps
- Mention your environment:
  - Operating system (Windows 10/11, Linux, etc.)
  - Python version
  - Application version (git commit or EXE version)
  - Screenshots, if applicable

Requesting Features:

- Open an issue to discuss your idea first
- Describe:
  - The benefit
  - Possible implementation
  - Impact on existing features


Code Style
----------

- Follow PEP 8
- Use type hints where possible
- Write docstrings for public functions
- Keep functions small and focused


What We Don't Accept
--------------------

- Code copied from other projects without permission
- Changes that break existing functionality
- Contributions that violate the proprietary license
- Large refactorings without prior discussion


Acknowledgments
---------------

Every contribution matters - whether it's a bugfix, a translation, or a
suggestion.

Thank you for helping improve SkySheet-to-HTML-Converter.