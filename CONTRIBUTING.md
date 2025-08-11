# CONTRIBUTING.md

## 💖 Welcome to **SkySheet to HTML Converter**

Thank you for considering contributing to **SkySheet to HTML Converter**! This guide will help you get started quickly and contribute effectively.

---

## 📋 Requirements

- Python **3.10** or higher
- A GitHub account

---

## 🚀 Getting Started

### 🔀 Fork & Download the Repository

1. Go to the [Project Lyrica GitHub page](https://github.com/VanilleIce/SkySheet-to-HTML-Converter/) and click **"Fork"** in the top right.
2. Download the repository as a `.zip` file and extract it locally.

---

## 🧪 Testing

**Tests are mandatory before any pull request is submitted.**

Please verify the following manually:

```bash
python converter.py
```

Make sure:

- All features work as expected
- No new errors are introduced
- Translations follow the required structure

---

## 🔧 Submitting Contributions

1. Make your changes locally
2. Ensure they work and are tested
3. Use clear and descriptive commit messages, such as:

```text
feat: added new French language file
fix: corrected XML error in *.xml
```

4. Submit a pull request via GitHub

> ⚠️ Note: Both `main` and `dev` branches are protected. Contributions require CLA agreement and possibly manual review by maintainers.

---

## 🌍 Adding Translations

1. Create a new file in `lang/`, e.g. `fr.xml`
2. Use this structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<translations>
  <language>Langue</language>
</translations>
```

---

## 🐛 Bug Reports & Feature Requests

### Reporting Bugs

- Clearly describe the issue
- Include reproduction steps
- Mention your environment:
  - Operating system
  - Python version
  - Screenshots, if applicable

> ⚠️ There are currently **no issue templates** – clarity is appreciated!

### Requesting Features

- Open an issue to discuss your idea first
- Describe:
  - The benefit
  - Possible implementation
  - Impact on existing features

---

## ⚖️ License

By contributing, you agree that your changes will be licensed.

---

## 🙏 Acknowledgments

Every contribution matters – whether it’s a bugfix, a translation, or a suggestion.  
**Thank you for helping improve SkySheet to HTML Converter.**
