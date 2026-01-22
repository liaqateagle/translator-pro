import sys
import os
import signal
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QComboBox,
                           QFileDialog, QTextEdit, QProgressBar, QFrame,
                           QSplitter, QGraphicsDropShadowEffect, QMessageBox,
                           QStatusBar, QToolButton, QSizePolicy, QDialog,
                           QLineEdit, QRadioButton, QButtonGroup, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QPalette, QColor, QIcon, QFont, QFontDatabase, QLinearGradient, QPainter

# ============== MODERN COLOR PALETTE ==============
class Colors:
    # Primary colors
    PRIMARY = "#6366F1"           # Indigo
    PRIMARY_DARK = "#4F46E5"
    PRIMARY_LIGHT = "#818CF8"

    # Accent colors
    ACCENT = "#10B981"            # Emerald
    ACCENT_DARK = "#059669"

    # Background colors
    BG_DARK = "#0F172A"           # Slate 900
    BG_CARD = "#1E293B"           # Slate 800
    BG_ELEVATED = "#334155"       # Slate 700

    # Text colors
    TEXT_PRIMARY = "#F8FAFC"      # Slate 50
    TEXT_SECONDARY = "#94A3B8"    # Slate 400
    TEXT_MUTED = "#64748B"        # Slate 500

    # Border colors
    BORDER = "#475569"            # Slate 600
    BORDER_LIGHT = "#64748B"

    # Status colors
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"


class TranslationWorker(QThread):
    """Background worker for handling translation tasks"""
    progress = pyqtSignal(int)
    translation_done = pyqtSignal(str)  # Renamed to avoid conflict with QThread.finished
    translation_error = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def __init__(self, text, target_lang, translation_backend='googletrans', deepl_api_key=''):
        super().__init__()
        self.text = text
        self.target_lang = target_lang
        self.translation_backend = translation_backend
        self.deepl_api_key = deepl_api_key
        self._is_running = True

    def run(self):
        try:
            print(f"DEBUG: TranslationWorker.run() started with backend: {self.translation_backend}")
            import time
            
            # Smart chunking for better translation
            chunks = [self.text[i:i+4500] for i in range(0, len(self.text), 4500)]
            translated_text = ""
            total_chunks = len(chunks)

            self.status_update.emit(f"Translating {total_chunks} chunk(s)...")

            for i, chunk in enumerate(chunks):
                if not self._is_running:
                    print("DEBUG: Translation cancelled")
                    return
                    
                self.status_update.emit(f"Processing chunk {i + 1}/{total_chunks}...")
                print(f"DEBUG: Translating chunk {i + 1}/{total_chunks}")
                
                # Retry logic with exponential backoff
                max_retries = 3
                retry_delay = 2
                
                for attempt in range(max_retries):
                    try:
                        if attempt > 0:
                            self.status_update.emit(f"Retry {attempt}/{max_retries - 1} for chunk {i + 1}...")
                            print(f"DEBUG: Retry attempt {attempt} for chunk {i + 1}")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        
                        # Translate based on selected backend
                        translated_chunk = self._translate_chunk(chunk)
                        translated_text += translated_chunk + " "
                        break  # Success, exit retry loop
                        
                    except Exception as retry_error:
                        print(f"DEBUG: Attempt {attempt + 1} failed: {retry_error}")
                        if attempt == max_retries - 1:
                            # Last attempt failed
                            raise Exception(f"Translation failed after {max_retries} attempts. Error: {str(retry_error)}")
                        
                progress = int((i + 1) / total_chunks * 100)
                self.progress.emit(progress)

            print("DEBUG: Translation complete, emitting result")
            self.translation_done.emit(translated_text.strip())
        except Exception as e:
            print(f"DEBUG: Translation error: {e}")
            import traceback
            traceback.print_exc()
            self.translation_error.emit(str(e))
    
    def _translate_chunk(self, chunk):
        """Translate a single chunk using the selected backend"""
        if self.translation_backend == 'googletrans':
            return self._translate_with_googletrans(chunk)
        elif self.translation_backend == 'deep-translator':
            return self._translate_with_deep_translator(chunk)
        elif self.translation_backend == 'deepl':
            return self._translate_with_deepl(chunk)
        else:
            raise Exception(f"Unknown translation backend: {self.translation_backend}")
    
    def _translate_with_googletrans(self, chunk):
        """Translate using googletrans library"""
        from googletrans import Translator
        translator = Translator()
        # Set timeout on the underlying httpx client
        try:
            import httpx
            translator.client = httpx.Client(timeout=30.0)
            print("DEBUG: Set googletrans timeout to 30 seconds")
        except Exception as e:
            print(f"DEBUG: Could not set custom timeout: {e}")
        return translator.translate(chunk, dest=self.target_lang).text
    
    def _translate_with_deep_translator(self, chunk):
        """Translate using deep-translator library (Google backend)"""
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='auto', target=self.target_lang)
        return translator.translate(chunk)
    
    def _translate_with_deepl(self, chunk):
        """Translate using DeepL API"""
        if not self.deepl_api_key:
            raise Exception("DeepL API key is required. Please configure it in Settings.")
        
        import deepl
        translator = deepl.Translator(self.deepl_api_key)
        
        # Map common language codes to DeepL format
        deepl_lang_map = {
            'en': 'EN-US', 'es': 'ES', 'fr': 'FR', 'de': 'DE', 'it': 'IT',
            'pt': 'PT-PT', 'pl': 'PL', 'ru': 'RU', 'ja': 'JA', 'zh': 'ZH',
            'nl': 'NL', 'sv': 'SV', 'da': 'DA', 'fi': 'FI', 'el': 'EL',
            'cs': 'CS', 'ro': 'RO', 'hu': 'HU', 'sk': 'SK', 'bg': 'BG',
            'et': 'ET', 'lv': 'LV', 'lt': 'LT', 'sl': 'SL', 'tr': 'TR',
            'id': 'ID', 'uk': 'UK', 'ko': 'KO', 'no': 'NB'
        }
        
        target_lang = deepl_lang_map.get(self.target_lang, self.target_lang.upper())
        result = translator.translate_text(chunk, target_lang=target_lang)
        return result.text

    def stop(self):
        """Stop the worker thread"""
        self._is_running = False

# ============== CUSTOM STYLED WIDGETS ==============

class StyledButton(QPushButton):
    """Modern styled button with hover effects and proper sizing"""
    def __init__(self, text, parent=None, primary=False, compact=False):
        super().__init__(text, parent)
        self.setFixedHeight(38 if compact else 44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 9 if compact else 10, QFont.Weight.DemiBold))
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        if primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {Colors.PRIMARY}, stop:1 {Colors.PRIMARY_LIGHT});
                    border: none;
                    border-radius: 8px;
                    color: white;
                    padding: 10px 24px;
                    font-weight: 600;
                    font-size: 13px;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {Colors.PRIMARY_DARK}, stop:1 {Colors.PRIMARY});
                }}
                QPushButton:pressed {{
                    background: {Colors.PRIMARY_DARK};
                }}
                QPushButton:disabled {{
                    background: {Colors.BG_ELEVATED};
                    color: {Colors.TEXT_MUTED};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_ELEVATED};
                    border: 1px solid {Colors.BORDER};
                    border-radius: 8px;
                    color: {Colors.TEXT_PRIMARY};
                    padding: 8px 16px;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {Colors.BORDER};
                    border-color: {Colors.PRIMARY_LIGHT};
                }}
                QPushButton:pressed {{
                    background-color: {Colors.BG_CARD};
                }}
            """)

class IconButton(QPushButton):
    """Circular icon button for actions like swap"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(48, 48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                border: none;
                border-radius: 24px;
                color: white;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_LIGHT};
            }}
        """)


class StyledComboBox(QComboBox):
    """Modern styled dropdown with smooth appearance"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setFont(QFont("Segoe UI", 11))
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {Colors.BG_ELEVATED};
                border: 2px solid {Colors.BORDER};
                border-radius: 10px;
                color: {Colors.TEXT_PRIMARY};
                padding: 10px 16px;
                padding-right: 40px;
                min-width: 180px;
            }}
            QComboBox:hover {{
                border-color: {Colors.PRIMARY_LIGHT};
            }}
            QComboBox:focus {{
                border-color: {Colors.PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 36px;
                subcontrol-position: center right;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 8px solid {Colors.TEXT_SECONDARY};
                margin-right: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Colors.BG_CARD};
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 10px;
                padding: 8px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 10px 14px;
                border-radius: 6px;
                min-height: 24px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {Colors.BG_ELEVATED};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {Colors.PRIMARY};
            }}
        """)

class StyledTextEdit(QTextEdit):
    """Modern styled text editor with enhanced visuals"""
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFont(QFont("Consolas", 11))
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Colors.BG_CARD};
                border: 2px solid {Colors.BORDER};
                border-radius: 12px;
                color: {Colors.TEXT_PRIMARY};
                padding: 16px;
                selection-background-color: {Colors.PRIMARY};
                line-height: 1.6;
            }}
            QTextEdit:focus {{
                border-color: {Colors.PRIMARY};
            }}
            QScrollBar:vertical {{
                background: {Colors.BG_DARK};
                width: 10px;
                border-radius: 5px;
                margin: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.BORDER};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Colors.PRIMARY};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

# ============== CARD WIDGET ==============

class CardFrame(QFrame):
    """Styled card container with shadow effect"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            CardFrame {{
                background-color: {Colors.BG_CARD};
                border-radius: 16px;
                border: 1px solid {Colors.BORDER};
            }}
        """)
        # Add subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)


# ============== SETTINGS DIALOG ==============

class SettingsDialog(QDialog):
    """Settings dialog for translation backend configuration"""
    
    def __init__(self, parent=None, current_backend='googletrans', current_api_key=''):
        super().__init__(parent)
        self.setWindowTitle("Translation Settings")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.selected_backend = current_backend
        self.api_key = current_api_key
        self.setup_ui()
        
    def setup_ui(self):
        """Build the settings dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Apply dark theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_DARK};
            }}
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
            }}
            QGroupBox {{
                color: {Colors.TEXT_PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: {Colors.PRIMARY_LIGHT};
            }}
            QRadioButton {{
                color: {Colors.TEXT_PRIMARY};
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
            }}
            QRadioButton::indicator::unchecked {{
                border: 2px solid {Colors.BORDER};
                border-radius: 9px;
                background: {Colors.BG_ELEVATED};
            }}
            QRadioButton::indicator::checked {{
                border: 2px solid {Colors.PRIMARY};
                border-radius: 9px;
                background: {Colors.PRIMARY};
            }}
            QLineEdit {{
                background-color: {Colors.BG_ELEVATED};
                border: 2px solid {Colors.BORDER};
                border-radius: 8px;
                color: {Colors.TEXT_PRIMARY};
                padding: 10px;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: {Colors.PRIMARY};
            }}
        """)
        
        # Title
        title = QLabel("Translation Backend Settings")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Choose your preferred translation service:")
        desc.setFont(QFont("Segoe UI", 10))
        desc.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(desc)
        
        # Backend selection group
        backend_group = QGroupBox("Translation Service")
        backend_layout = QVBoxLayout(backend_group)
        backend_layout.setSpacing(12)
        
        self.backend_button_group = QButtonGroup(self)
        
        # Google Translate (googletrans)
        self.radio_googletrans = QRadioButton("Google Translate (googletrans)")
        self.radio_googletrans.setFont(QFont("Segoe UI", 10))
        desc1 = QLabel("  Free, unlimited, no API key required")
        desc1.setFont(QFont("Segoe UI", 9))
        desc1.setStyleSheet(f"color: {Colors.TEXT_MUTED}; margin-left: 26px;")
        
        # Deep Translator
        self.radio_deep_translator = QRadioButton("Deep Translator (Google backend)")
        self.radio_deep_translator.setFont(QFont("Segoe UI", 10))
        desc2 = QLabel("  Free, more reliable, no API key required")
        desc2.setFont(QFont("Segoe UI", 9))
        desc2.setStyleSheet(f"color: {Colors.TEXT_MUTED}; margin-left: 26px;")
        
        # DeepL
        self.radio_deepl = QRadioButton("DeepL API")
        self.radio_deepl.setFont(QFont("Segoe UI", 10))
        desc3 = QLabel("  Best quality, requires free API key (500k chars/month)")
        desc3.setFont(QFont("Segoe UI", 9))
        desc3.setStyleSheet(f"color: {Colors.TEXT_MUTED}; margin-left: 26px;")
        
        self.backend_button_group.addButton(self.radio_googletrans, 0)
        self.backend_button_group.addButton(self.radio_deep_translator, 1)
        self.backend_button_group.addButton(self.radio_deepl, 2)
        
        backend_layout.addWidget(self.radio_googletrans)
        backend_layout.addWidget(desc1)
        backend_layout.addSpacing(8)
        backend_layout.addWidget(self.radio_deep_translator)
        backend_layout.addWidget(desc2)
        backend_layout.addSpacing(8)
        backend_layout.addWidget(self.radio_deepl)
        backend_layout.addWidget(desc3)
        
        # Set current selection
        if self.selected_backend == 'googletrans':
            self.radio_googletrans.setChecked(True)
        elif self.selected_backend == 'deep-translator':
            self.radio_deep_translator.setChecked(True)
        elif self.selected_backend == 'deepl':
            self.radio_deepl.setChecked(True)
        
        layout.addWidget(backend_group)
        
        # DeepL API Key section
        api_group = QGroupBox("DeepL API Configuration (Optional)")
        api_layout = QVBoxLayout(api_group)
        api_layout.setSpacing(8)
        
        api_label = QLabel("API Key:")
        api_label.setFont(QFont("Segoe UI", 10))
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your DeepL API key...")
        self.api_key_input.setText(self.api_key)
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        show_key_btn = StyledButton("Show/Hide", compact=True)
        show_key_btn.setMaximumWidth(100)
        show_key_btn.clicked.connect(self.toggle_api_key_visibility)
        
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(self.api_key_input)
        api_key_layout.addWidget(show_key_btn)
        
        help_label = QLabel('Get your free API key at: <a href="https://www.deepl.com/pro-api">deepl.com/pro-api</a>')
        help_label.setFont(QFont("Segoe UI", 9))
        help_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        help_label.setOpenExternalLinks(True)
        
        api_layout.addWidget(api_label)
        api_layout.addLayout(api_key_layout)
        api_layout.addWidget(help_label)
        
        layout.addWidget(api_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = StyledButton("Cancel")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = StyledButton("Save", primary=True)
        save_btn.setMinimumWidth(100)
        save_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addSpacing(10)
        layout.addLayout(button_layout)
    
    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def get_settings(self):
        """Return selected settings"""
        if self.radio_googletrans.isChecked():
            backend = 'googletrans'
        elif self.radio_deep_translator.isChecked():
            backend = 'deep-translator'
        else:
            backend = 'deepl'
        
        return backend, self.api_key_input.text().strip()


# ============== MAIN APPLICATION ==============

class TranslatorApp(QMainWindow):
    """Modern Translation Application with Professional UI"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("✨ Translator Pro | By Liaqat Eagle")
        self.setMinimumSize(1100, 750)
        self.worker = None
        
        # Translation settings
        self.translation_backend = 'googletrans'  # Default backend
        self.deepl_api_key = ''
        
        self.setup_dark_theme()
        self.setup_ui()
        self.setup_status_bar()

    def setup_dark_theme(self):
        """Apply modern dark theme to the application"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {Colors.BG_DARK};
            }}
            QWidget {{
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 13px;
            }}
            QProgressBar {{
                border: none;
                border-radius: 6px;
                background-color: {Colors.BG_ELEVATED};
                text-align: center;
                color: {Colors.TEXT_PRIMARY};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.PRIMARY}, stop:1 {Colors.ACCENT});
                border-radius: 6px;
            }}
            QSplitter::handle {{
                background-color: {Colors.BORDER};
                width: 2px;
                margin: 8px 4px;
                border-radius: 1px;
            }}
            QSplitter::handle:hover {{
                background-color: {Colors.PRIMARY};
            }}
            QStatusBar {{
                background-color: {Colors.BG_CARD};
                color: {Colors.TEXT_SECONDARY};
                border-top: 1px solid {Colors.BORDER};
                padding: 8px;
                font-size: 12px;
            }}
            QToolTip {{
                background-color: {Colors.BG_ELEVATED};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        
    def setup_status_bar(self):
        """Configure the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready to translate")
        self.char_count_label = QLabel("Characters: 0")
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addPermanentWidget(self.char_count_label)

    def setup_ui(self):
        """Build the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # ===== HEADER SECTION =====
        header_card = CardFrame()
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(24, 20, 24, 20)
        header_layout.setSpacing(20)

        # App title with branding
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        app_title = QLabel("Translator Pro")
        app_title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        app_title.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            background: transparent;
        """)

        app_subtitle = QLabel("Professional Text & Document Translation")
        app_subtitle.setFont(QFont("Segoe UI", 10))
        app_subtitle.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")

        title_layout.addWidget(app_title)
        title_layout.addWidget(app_subtitle)

        header_layout.addWidget(title_container)
        header_layout.addStretch()

        # Settings button
        self.settings_btn = StyledButton("⚙ Settings", compact=True)
        self.settings_btn.setMinimumWidth(100)
        self.settings_btn.clicked.connect(self.open_settings)
        self.settings_btn.setToolTip("Configure translation backend")
        header_layout.addWidget(self.settings_btn)

        # File selection area
        self.file_label = QLabel("No file selected")
        self.file_label.setFont(QFont("Segoe UI", 10))
        self.file_label.setStyleSheet(f"""
            padding: 10px 18px;
            background-color: {Colors.BG_ELEVATED};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            color: {Colors.TEXT_MUTED};
        """)
        self.select_button = StyledButton("Open File")
        self.select_button.setMinimumWidth(110)
        self.select_button.clicked.connect(self.select_file)
        self.select_button.setToolTip("Open a text or PDF file")

        header_layout.addWidget(self.file_label)
        header_layout.addWidget(self.select_button)
        main_layout.addWidget(header_card)

        # ===== LANGUAGE SELECTION SECTION =====
        lang_card = CardFrame()
        lang_layout = QHBoxLayout(lang_card)
        lang_layout.setContentsMargins(20, 16, 20, 16)
        lang_layout.setSpacing(20)

        # Source language
        source_lang_container = QWidget()
        source_lang_layout = QVBoxLayout(source_lang_container)
        source_lang_layout.setContentsMargins(0, 0, 0, 0)
        source_lang_layout.setSpacing(8)

        source_lang_label = QLabel("Source Language")
        source_lang_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        source_lang_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")

        self.source_lang = StyledComboBox()
        source_lang_layout.addWidget(source_lang_label)
        source_lang_layout.addWidget(self.source_lang)

        # Swap button - using IconButton for circular appearance
        self.swap_btn = IconButton("⇄")
        self.swap_btn.setToolTip("Swap languages")
        self.swap_btn.clicked.connect(self.swap_languages)

        # Target language
        target_lang_container = QWidget()
        target_lang_layout = QVBoxLayout(target_lang_container)
        target_lang_layout.setContentsMargins(0, 0, 0, 0)
        target_lang_layout.setSpacing(8)

        target_lang_label = QLabel("Target Language")
        target_lang_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        target_lang_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")

        self.target_lang = StyledComboBox()
        target_lang_layout.addWidget(target_lang_label)
        target_lang_layout.addWidget(self.target_lang)

        # Populate languages with proper capitalization (predefined for fast loading)
        self.lang_map = {
            'Afrikaans': 'af', 'Albanian': 'sq', 'Amharic': 'am', 'Arabic': 'ar',
            'Armenian': 'hy', 'Azerbaijani': 'az', 'Basque': 'eu', 'Belarusian': 'be',
            'Bengali': 'bn', 'Bosnian': 'bs', 'Bulgarian': 'bg', 'Catalan': 'ca',
            'Cebuano': 'ceb', 'Chinese (Simplified)': 'zh-cn', 'Chinese (Traditional)': 'zh-tw',
            'Corsican': 'co', 'Croatian': 'hr', 'Czech': 'cs', 'Danish': 'da',
            'Dutch': 'nl', 'English': 'en', 'Esperanto': 'eo', 'Estonian': 'et',
            'Finnish': 'fi', 'French': 'fr', 'Frisian': 'fy', 'Galician': 'gl',
            'Georgian': 'ka', 'German': 'de', 'Greek': 'el', 'Gujarati': 'gu',
            'Haitian Creole': 'ht', 'Hausa': 'ha', 'Hawaiian': 'haw', 'Hebrew': 'he',
            'Hindi': 'hi', 'Hmong': 'hmn', 'Hungarian': 'hu', 'Icelandic': 'is',
            'Igbo': 'ig', 'Indonesian': 'id', 'Irish': 'ga', 'Italian': 'it',
            'Japanese': 'ja', 'Javanese': 'jw', 'Kannada': 'kn', 'Kazakh': 'kk',
            'Khmer': 'km', 'Korean': 'ko', 'Kurdish': 'ku', 'Kyrgyz': 'ky',
            'Lao': 'lo', 'Latin': 'la', 'Latvian': 'lv', 'Lithuanian': 'lt',
            'Luxembourgish': 'lb', 'Macedonian': 'mk', 'Malagasy': 'mg', 'Malay': 'ms',
            'Malayalam': 'ml', 'Maltese': 'mt', 'Maori': 'mi', 'Marathi': 'mr',
            'Mongolian': 'mn', 'Myanmar': 'my', 'Nepali': 'ne', 'Norwegian': 'no',
            'Nyanja': 'ny', 'Pashto': 'ps', 'Persian': 'fa', 'Polish': 'pl',
            'Portuguese': 'pt', 'Punjabi': 'pa', 'Romanian': 'ro', 'Russian': 'ru',
            'Samoan': 'sm', 'Scots Gaelic': 'gd', 'Serbian': 'sr', 'Sesotho': 'st',
            'Shona': 'sn', 'Sindhi': 'sd', 'Sinhala': 'si', 'Slovak': 'sk',
            'Slovenian': 'sl', 'Somali': 'so', 'Spanish': 'es', 'Sundanese': 'su',
            'Swahili': 'sw', 'Swedish': 'sv', 'Tagalog': 'tl', 'Tajik': 'tg',
            'Tamil': 'ta', 'Telugu': 'te', 'Thai': 'th', 'Turkish': 'tr',
            'Ukrainian': 'uk', 'Urdu': 'ur', 'Uzbek': 'uz', 'Vietnamese': 'vi',
            'Welsh': 'cy', 'Xhosa': 'xh', 'Yiddish': 'yi', 'Yoruba': 'yo', 'Zulu': 'zu'
        }
        lang_list = sorted(self.lang_map.keys())
        self.source_lang.addItems(lang_list)
        self.target_lang.addItems(lang_list)

        # Set defaults
        self.source_lang.setCurrentText("English")
        self.target_lang.setCurrentText("Spanish")

        lang_layout.addWidget(source_lang_container, 1)
        lang_layout.addWidget(self.swap_btn)
        lang_layout.addWidget(target_lang_container, 1)
        main_layout.addWidget(lang_card)

        # ===== TEXT AREAS SECTION =====
        text_splitter = QSplitter(Qt.Orientation.Horizontal)
        text_splitter.setHandleWidth(12)
        text_splitter.setChildrenCollapsible(False)

        # Source text panel
        source_panel = CardFrame()
        source_layout = QVBoxLayout(source_panel)
        source_layout.setContentsMargins(20, 16, 20, 16)
        source_layout.setSpacing(12)

        source_header = QHBoxLayout()
        source_header.setSpacing(12)
        source_label = QLabel("Source Text")
        source_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        source_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")

        self.paste_btn = StyledButton("Paste", compact=True)
        self.paste_btn.setMinimumWidth(75)
        self.paste_btn.clicked.connect(self.paste_from_clipboard)

        self.clear_btn = StyledButton("Clear", compact=True)
        self.clear_btn.setMinimumWidth(75)
        self.clear_btn.clicked.connect(lambda: self.source_text.clear())

        source_header.addWidget(source_label)
        source_header.addStretch()
        source_header.addWidget(self.paste_btn)
        source_header.addWidget(self.clear_btn)

        self.source_text = StyledTextEdit("Enter or paste your text here...")
        self.source_text.textChanged.connect(self.update_char_count)

        source_layout.addLayout(source_header)
        source_layout.addWidget(self.source_text)
        text_splitter.addWidget(source_panel)

        # Target text panel
        target_panel = CardFrame()
        target_layout = QVBoxLayout(target_panel)
        target_layout.setContentsMargins(20, 16, 20, 16)
        target_layout.setSpacing(12)

        target_header = QHBoxLayout()
        target_header.setSpacing(12)
        target_label = QLabel("Translation")
        target_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        target_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")

        self.copy_btn = StyledButton("Copy", compact=True)
        self.copy_btn.setMinimumWidth(75)
        self.copy_btn.clicked.connect(self.copy_translation)

        self.save_btn = StyledButton("Save", compact=True)
        self.save_btn.setMinimumWidth(75)
        self.save_btn.clicked.connect(self.save_translation)

        target_header.addWidget(target_label)
        target_header.addStretch()
        target_header.addWidget(self.copy_btn)
        target_header.addWidget(self.save_btn)

        self.target_text = StyledTextEdit("Translation will appear here...")
        self.target_text.setReadOnly(True)

        target_layout.addLayout(target_header)
        target_layout.addWidget(self.target_text)
        text_splitter.addWidget(target_panel)

        text_splitter.setSizes([500, 500])
        main_layout.addWidget(text_splitter, 1)

        # ===== PROGRESS AND ACTION SECTION =====
        action_card = CardFrame()
        action_layout = QVBoxLayout(action_card)
        action_layout.setContentsMargins(24, 20, 24, 20)
        action_layout.setSpacing(16)

        # Progress bar with label
        progress_container = QHBoxLayout()
        progress_container.setSpacing(12)

        self.progress_label = QLabel("")
        self.progress_label.setFont(QFont("Segoe UI", 9))
        self.progress_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)

        progress_container.addWidget(self.progress_bar, 1)
        progress_container.addWidget(self.progress_label)
        action_layout.addLayout(progress_container)

        # Translate button - centered
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.translate_button = StyledButton("Translate", primary=True)
        self.translate_button.setMinimumWidth(180)
        self.translate_button.setFixedHeight(50)
        self.translate_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.translate_button.clicked.connect(self.translate_text)

        button_layout.addWidget(self.translate_button)
        button_layout.addStretch()
        action_layout.addLayout(button_layout)

        main_layout.addWidget(action_card)
        
        # ===== SOCIAL MEDIA FOOTER SECTION =====
        social_card = CardFrame()
        social_layout = QHBoxLayout(social_card)
        social_layout.setContentsMargins(20, 12, 20, 12)
        social_layout.setSpacing(16)
        
        # "Connect with me" label
        connect_label = QLabel("Connect with me:")
        connect_label.setFont(QFont("Segoe UI", 10))
        connect_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        social_layout.addWidget(connect_label)
        
        # YouTube button
        youtube_btn = StyledButton("🎬 YouTube", compact=True)
        youtube_btn.setMinimumWidth(110)
        youtube_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        youtube_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FF0000;
                border: none;
                border-radius: 8px;
                color: white;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #CC0000;
            }}
            QPushButton:pressed {{
                background-color: #990000;
            }}
        """)
        youtube_btn.setToolTip("Subscribe to my YouTube channel")
        youtube_btn.clicked.connect(lambda: self.open_social_link("https://www.youtube.com/@learnwithliaqat"))
        social_layout.addWidget(youtube_btn)
        
        # Facebook button
        facebook_btn = StyledButton("👤 Facebook", compact=True)
        facebook_btn.setMinimumWidth(110)
        facebook_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        facebook_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1877F2;
                border: none;
                border-radius: 8px;
                color: white;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #1565C0;
            }}
            QPushButton:pressed {{
                background-color: #0D47A1;
            }}
        """)
        facebook_btn.setToolTip("Follow me on Facebook")
        facebook_btn.clicked.connect(lambda: self.open_social_link("https://www.facebook.com/profile.php?id=100008667968822"))
        social_layout.addWidget(facebook_btn)
        
        social_layout.addStretch()
        main_layout.addWidget(social_card)
        
    # ============== HELPER METHODS ==============

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self, self.translation_backend, self.deepl_api_key)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            backend, api_key = dialog.get_settings()
            self.translation_backend = backend
            self.deepl_api_key = api_key
            
            # Show confirmation
            backend_names = {
                'googletrans': 'Google Translate (googletrans)',
                'deep-translator': 'Deep Translator',
                'deepl': 'DeepL API'
            }
            backend_name = backend_names.get(backend, backend)
            self.status_label.setText(f"✓ Backend set to: {backend_name}")
            QTimer.singleShot(3000, lambda: self.status_label.setText("Ready to translate"))

    def open_social_link(self, url):
        """Open a social media link in the default browser"""
        import webbrowser
        webbrowser.open(url)
        self.status_label.setText("✓ Opening link in browser...")
        QTimer.singleShot(2000, lambda: self.status_label.setText("Ready to translate"))

    def swap_languages(self):
        """Swap source and target languages"""
        source_idx = self.source_lang.currentIndex()
        target_idx = self.target_lang.currentIndex()
        self.source_lang.setCurrentIndex(target_idx)
        self.target_lang.setCurrentIndex(source_idx)
        self.status_label.setText("✓ Languages swapped")
        QTimer.singleShot(2000, lambda: self.status_label.setText("Ready to translate"))

    def update_char_count(self):
        """Update character count in status bar"""
        try:
            count = len(self.source_text.toPlainText())
            self.char_count_label.setText(f"Characters: {count:,}")
        except Exception as e:
            print(f"Error updating char count: {e}")

    def paste_from_clipboard(self):
        """Paste text from clipboard"""
        try:
            print("DEBUG: paste_from_clipboard called")
            clipboard_text = QApplication.clipboard().text()
            print(f"DEBUG: clipboard text length: {len(clipboard_text)}")
            if clipboard_text:
                print("DEBUG: setting text...")
                self.source_text.blockSignals(True)
                self.source_text.setText(clipboard_text)
                self.source_text.blockSignals(False)
                print("DEBUG: updating char count...")
                self.update_char_count()
                print("DEBUG: updating status...")
                self.status_label.setText("✓ Pasted from clipboard")
                QTimer.singleShot(2000, lambda: self.status_label.setText("Ready to translate"))
                print("DEBUG: paste complete")
        except Exception as e:
            print(f"ERROR pasting from clipboard: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"Error: {str(e)}")

    def copy_translation(self):
        """Copy translation to clipboard"""
        text = self.target_text.toPlainText()
        if text and text != "Translation will appear here...":
            QApplication.clipboard().setText(text)
            self.status_label.setText("✓ Copied to clipboard!")
            # Visual feedback on button
            self.copy_btn.setText("Copied!")
            QTimer.singleShot(1500, lambda: self.copy_btn.setText("Copy"))
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready to translate"))
        else:
            self.status_label.setText("Nothing to copy")

    def save_translation(self):
        """Save translation to file"""
        text = self.target_text.toPlainText()
        if not text or text == "Translation will appear here...":
            self.status_label.setText("Nothing to save")
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Translation", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.status_label.setText(f"✓ Saved to {os.path.basename(file_name)}")
                self.save_btn.setText("Saved!")
                QTimer.singleShot(1500, lambda: self.save_btn.setText("Save"))
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not save file: {e}")

    def select_file(self):
        """Open file dialog to select a document"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "Text Files (*.txt);;PDF Files (*.pdf);;All Files (*)"
        )

        if file_name:
            # Truncate long filenames
            display_name = os.path.basename(file_name)
            if len(display_name) > 25:
                display_name = display_name[:22] + "..."
            self.file_label.setText(display_name)
            self.file_label.setStyleSheet(f"""
                padding: 10px 18px;
                background-color: {Colors.ACCENT_DARK};
                border: 1px solid {Colors.ACCENT};
                border-radius: 8px;
                color: {Colors.TEXT_PRIMARY};
                font-weight: 500;
            """)
            self.load_file_content(file_name)
            self.status_label.setText(f"✓ Loaded: {os.path.basename(file_name)}")

    def load_file_content(self, file_name):
        """Load content from a file (TXT or PDF)"""
        try:
            text = ""
            if file_name.lower().endswith('.pdf'):
                import PyPDF2
                with open(file_name, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    total_pages = len(pdf_reader.pages)
                    for i, page in enumerate(pdf_reader.pages):
                        text += page.extract_text() + "\n"
                        self.status_label.setText(f"Loading page {i+1}/{total_pages}...")
            else:
                with open(file_name, 'r', encoding='utf-8') as file:
                    text = file.read()

            self.source_text.setText(text)
            self.status_label.setText("File loaded successfully")
        except Exception as e:
            self.source_text.setText(f"Error loading file: {str(e)}")
            self.status_label.setText("Error loading file")

    def translate_text(self):
        """Start translation process"""
        try:
            print("DEBUG: translate_text() called")
            source_text = self.source_text.toPlainText()
            if not source_text or source_text == "Enter or paste your text here...":
                self.status_label.setText("⚠ Please enter text to translate")
                return

            # Get language code from the capitalized name using our stored mapping
            target_lang_name = self.target_lang.currentText()
            target_lang_code = self.lang_map.get(target_lang_name, 'en')
            print(f"DEBUG: Translating to {target_lang_name} ({target_lang_code})")

            # Clean up any previous worker
            if self.worker is not None:
                print("DEBUG: Cleaning up previous worker")
                self.worker.stop()
                if self.worker.isRunning():
                    self.worker.quit()
                    self.worker.wait(1000)  # Wait up to 1 second
                self.worker = None

            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.translate_button.setEnabled(False)
            self.translate_button.setText("Translating...")
            self.status_label.setText(f"Translating to {target_lang_name}...")

            print("DEBUG: Creating new TranslationWorker")
            self.worker = TranslationWorker(
                source_text, 
                target_lang_code,
                self.translation_backend,
                self.deepl_api_key
            )
            self.worker.progress.connect(self.update_progress)
            self.worker.translation_done.connect(self.translation_finished)
            self.worker.translation_error.connect(self.translation_error)
            self.worker.status_update.connect(lambda msg: self.status_label.setText(msg))

            print("DEBUG: Starting worker thread")
            self.worker.start()
            print("DEBUG: Worker thread started")
        except Exception as e:
            print(f"ERROR in translate_text: {e}")
            import traceback
            traceback.print_exc()
            self.translation_error(str(e))

    def update_progress(self, value):
        """Update progress bar value"""
        self.progress_bar.setValue(value)

    def translation_finished(self, translated_text):
        """Handle successful translation"""
        self.target_text.setText(translated_text)
        self.progress_bar.setVisible(False)
        self.translate_button.setEnabled(True)
        self.translate_button.setText("Translate")
        self.status_label.setText("✓ Translation complete!")
        # Update word count
        word_count = len(translated_text.split())
        self.char_count_label.setText(f"Words: {word_count:,} | Characters: {len(self.source_text.toPlainText()):,}")

    def translation_error(self, error_message):
        """Handle translation error"""
        self.target_text.setText(f"Translation Error:\n\n{error_message}\n\nPlease try again.")
        self.progress_bar.setVisible(False)
        self.translate_button.setEnabled(True)
        self.translate_button.setText("Translate")
        self.status_label.setText("⚠ Translation failed - Please try again")


# ============== APPLICATION ENTRY POINT ==============

def exception_hook(exctype, value, tb):
    """Global exception hook to prevent silent crashes"""
    import traceback
    print("=" * 60)
    print("UNHANDLED EXCEPTION:")
    print("=" * 60)
    traceback.print_exception(exctype, value, tb)
    print("=" * 60)
    # Don't exit - let the app try to continue
    # sys.exit(1)


if __name__ == '__main__':
    # Install the global exception hook
    sys.excepthook = exception_hook

    # Gracefully handle Ctrl+C / KeyboardInterrupt so the terminal
    # does not show an ugly traceback for normal exits.
    def _handle_sigint(_signum, _frame):
        app = QApplication.instance()
        if app is not None:
            app.quit()
        # Exit cleanly without raising KeyboardInterrupt
        sys.exit(0)

    try:
        signal.signal(signal.SIGINT, _handle_sigint)
    except Exception:
        # On some platforms signal configuration may fail; ignore.
        pass

    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for consistent look

    # Set application metadata
    app.setApplicationName("Translator Pro")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Liaqat Eagle")

    print("DEBUG: Starting Translator Pro...")
    window = TranslatorApp()
    window.show()
    print("DEBUG: Window shown, entering event loop")

    try:
        exit_code = app.exec()
        print(f"DEBUG: App exited with code {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("DEBUG: KeyboardInterrupt received")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Unhandled exception in main loop: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)