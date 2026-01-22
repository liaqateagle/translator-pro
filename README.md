# ✨ Translator Pro

A modern, professional text and document translation application built with Python and PyQt6. Featuring a sleek dark theme UI and support for multiple translation backends.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-green?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## 🌟 Features

- **🎨 Modern Dark Theme UI** - Beautiful, professional interface with smooth animations
- **🌐 Multiple Translation Backends**
  - Google Translate (Googletrans) - Free, unlimited
  - Deep Translator - Reliable Google backend
  - DeepL API - Premium quality (free tier: 500k chars/month)
- **📄 Document Support** - Load and translate TXT and PDF files
- **🔄 Language Swap** - Quickly swap source and target languages
- **📋 Clipboard Integration** - Paste from and copy to clipboard
- **💾 Export** - Save translations to text files
- **🚀 Smart Chunking** - Handles large texts with automatic chunking
- **⚡ Retry Logic** - Exponential backoff for reliable translations

## 📸 Screenshot

![Translator Pro Interface](https://via.placeholder.com/800x500?text=Translator+Pro+Screenshot)

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/liaqateagle/translator-pro.git
   cd translator-pro
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| PyQt6 | ≥6.5.0 | GUI Framework |
| googletrans | 4.0.0-rc1 | Google Translate API |
| deep-translator | ≥1.11.4 | Alternative translation backend |
| deepl | ≥1.17.0 | DeepL API integration |
| PyPDF2 | ≥3.0.0 | PDF file support |

## 🎮 Usage

1. **Enter Text** - Type or paste text in the source panel
2. **Load File** - Or click "Open File" to load a TXT/PDF document
3. **Select Languages** - Choose source and target languages from dropdowns
4. **Translate** - Click the "Translate" button
5. **Export** - Copy to clipboard or save to file

### ⚙️ Settings

Click the **Settings** button to configure:
- **Translation Backend** - Choose between Googletrans, Deep Translator, or DeepL
- **DeepL API Key** - Enter your API key for DeepL (optional)

### 🔑 DeepL API Setup (Optional)

1. Sign up for a free account at [deepl.com/pro-api](https://www.deepl.com/pro-api)
2. Get your API key from the account page
3. Enter it in the Settings dialog

## 🏗️ Building Executable

Create a standalone executable using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --name="TranslatorPro" main.py
```

The executable will be in the `dist` folder.

## 📁 Project Structure

```
translator-pro/
├── main.py           # Main application code
├── requirements.txt  # Python dependencies
├── icon.ico          # Application icon
├── README.md         # This file
├── LICENSE           # MIT License
└── .gitignore        # Git ignore rules
```

## 🌍 Supported Languages

The application supports 90+ languages including:

English, Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese (Simplified/Traditional), Arabic, Hindi, Dutch, Swedish, Polish, Turkish, Vietnamese, Thai, Indonesian, and many more!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Liaqat Eagle**

- 🎬 YouTube: [@learnwithliaqat](https://www.youtube.com/@learnwithliaqat)
- 👤 Facebook: [Liaqat Eagle](https://www.facebook.com/profile.php?id=100008667968822)

## 🙏 Acknowledgments

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [Googletrans](https://github.com/ssut/py-googletrans) - Google Translate API
- [Deep Translator](https://github.com/nidhaloff/deep-translator) - Translation library
- [DeepL](https://www.deepl.com/) - Premium translation service

---

<p align="center">
Made with ❤️ by Liaqat Eagle
</p>
