# SkySheet to HTML Converter

Converts SkySheet files into interactive HTML pages with keyboard views.
**This software is intended for private/personal use only. Any commercial use is expressly prohibited.**

## Features

- 🌍 **Multilingual support** - Built-in translations for 7 languages
- 🖨️ **Print-optimised output** - Creates print-friendly scores
- 🎚️ **Customisable layouts** - Support for QWERTZ, QWERTY, AZERTY and more
- 📱 **Responsive design** - Works on desktop and mobile devices


## Installation

1. **Install Python** (version 3.10 or higher):

   - [Download Python](https://www.python.org/downloads/)

2. **Clone repository**:

```bash

   git clone https://github.com/VanilleIce/SkySheet-to-HTML-Converter.git

   cd skysheet-converter
```

## Usage

1. **Convert SkySheet file**:

   - Drag your `.skysheet` `.txt` `.json` file onto `converter.bat`
   - Or run the following command line:

     ```
     converter.bat ‘path\to\file.skysheet’
     ```

2. **Result**:

   - If successful, the following message appears: ‘CONVERSION SUCCESSFUL!’
   - The HTML file is created in the same folder as the SkySheet file.
   - Open the HTML file in a browser.


## Custom keyboard layouts

To create your own layout:

1. Create a `custom.xml` file in the same folder as `converter.bat`
2. Insert this content:

```xml

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
```