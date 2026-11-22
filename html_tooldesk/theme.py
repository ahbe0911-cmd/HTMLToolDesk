"""A compact Persian-first visual system. Avoid heavy drop shadows or wide chrome."""
from __future__ import annotations

from PyQt6.QtGui import QFont, QFontDatabase
from .paths import resource_path


def install_font(app) -> str:
    """Load the bundled open-source Vazirmatn family, including bold text."""
    families = []
    for filename in ("Vazirmatn-Regular.ttf", "Vazirmatn-Medium.ttf",
                     "Vazirmatn-SemiBold.ttf", "Vazirmatn-Bold.ttf"):
        path = resource_path(f"assets/fonts/{filename}")
        if not path.is_file():
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id >= 0:
            families.extend(QFontDatabase.applicationFontFamilies(font_id))
    family = next((name for name in families if "Vazirmatn" in name), None)
    if family:
        font = QFont(family, 10)
    else:
        font = QFont("Tahoma" if __import__("sys").platform == "win32" else "Sans Serif", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)
    return font.family()


def stylesheet(mode: str) -> str:
    dark = mode == "dark"
    bg = "#0B1120" if dark else "#F7F9FC"
    sidebar = "#0E1829" if dark else "#FFFFFF"
    surface = "#142239" if dark else "#FFFFFF"
    raised = "#1C2A41" if dark else "#F3F6FA"
    text = "#ECF2FA" if dark else "#17263E"
    muted = "#91A6C2" if dark else "#7B8798"
    line = "#25344B" if dark else "#E5EAF2"
    hover = "#1E2F4A" if dark else "#EFF3F9"
    selected = "#23395B" if dark else "#EAF0FF"
    accent = "#8C9CFF" if dark else "#4358DC"
    return f"""
    /* Application fonts are loaded by install_font; keep all Qt widgets uniform. */
    QWidget {{ font-family: "Vazirmatn"; font-size: 12px; }}
    QWidget#AppRoot {{ background: {bg}; color: {text}; }}
    QWidget#SideBar {{ background: {sidebar}; border-left: 1px solid {line}; }}
    QWidget#MainArea {{ background: {bg}; }}
    QWidget#TopBar {{ background: {surface}; border-bottom: 1px solid {line}; }}
    QWidget#WelcomeCard {{ background: {surface}; border: 1px solid {line}; border-radius: 18px; }}
    QFrame#SideRule {{ background: {line}; min-height: 1px; max-height: 1px; }}
    QLabel {{ color: {text}; background: transparent; }}
    QLabel#MutedText {{ color: {muted}; font-size: 11px; font-weight: 400; }}
    QLabel#AppTitle {{ color: {text}; font-size: 17px; font-weight: 700; }}
    QLabel#SectionTitle {{ font-size: 14px; font-weight: 600; }}
    QLabel#WelcomeTitle {{ font-size: 23px; font-weight: 700; }}
    QLabel#WelcomeArrow {{ color: {accent}; font-family: "Segoe UI Symbol"; font-size: 48px; font-weight: 700; }}
    QLabel#BrandCaption {{ color: {accent}; letter-spacing: 1px; font-size: 9px; font-weight: 600; }}
    QLabel#ShamsiDate {{ color: {accent}; background: {selected}; border: 1px solid {line};
        border-radius: 8px; padding: 5px 11px; font-size: 11px; font-weight: 600; }}
    QLabel#SectionCaption {{ color: {muted}; font-size: 10px; font-weight: 500; }}
    QLineEdit, QTextEdit {{ color: {text}; background: {raised}; border: 1px solid {line};
        border-radius: 9px; padding: 6px 9px; selection-background-color: {accent}; }}
    QLineEdit:focus, QTextEdit:focus {{ border-color: {accent}; }}
    QPushButton, QToolButton {{ color: {text}; background: {raised}; border: 1px solid {line};
        border-radius: 8px; padding: 5px 10px; font-size: 12px; font-weight: 500; }}
    QPushButton:hover, QToolButton:hover {{ background: {hover}; border-color: {accent}; }}
    QPushButton:disabled, QToolButton:disabled {{ color: {muted}; }}
    QPushButton#PrimaryButton {{ color: #FFFFFF; background: {accent}; border: 0;
        border-radius: 10px; font-weight: 600; padding: 8px 10px; }}
    QPushButton#PrimaryButton:hover {{ background: {"#7385FB" if dark else "#374DCC"}; }}
    QToolButton#IconButton {{ background: transparent; border: 1px solid transparent;
        min-width: 30px; min-height: 30px; padding: 0; }}
    QToolButton#IconButton:hover {{ background: {hover}; border-color: {line}; }}
    QListWidget#ToolList {{ background: transparent; color: {text}; border: 0;
        outline: none; font-size: 12px; font-weight: 500; }}
    /* Custom ToolCardDelegate paints the backgrounds, not the stylesheet. */
    QListWidget#ToolList::item {{ background: transparent; padding: 0; margin: 0; border: 0; }}
    QListWidget#ToolList::item:selected {{ background: transparent; border: 0; }}
    QSplitter::handle {{ background: {line}; }}
    QDialog, QMessageBox, QMenu {{ background: {surface}; color: {text}; }}
    QMenu {{ border: 1px solid {line}; padding: 4px; }}
    QMenu::item {{ padding: 7px 18px; border-radius: 5px; }}
    QMenu::item:selected {{ background: {hover}; }}
    QScrollBar:vertical {{ background: transparent; width: 7px; }}
    QScrollBar::handle:vertical {{ background: {line}; border-radius: 3px; min-height: 24px; }}
    """
