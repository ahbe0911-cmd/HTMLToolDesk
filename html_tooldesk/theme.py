"""Application typography and dark/light QSS themes."""
from __future__ import annotations

from PyQt6.QtGui import QFont, QFontDatabase
from .paths import resource_path


def install_font(app) -> str:
    for filename in ("Vazirmatn-Regular.ttf", "Vazirmatn.ttf"):
        path = resource_path(f"assets/fonts/{filename}")
        if path.is_file():
            fid = QFontDatabase.addApplicationFont(str(path))
            if fid >= 0:
                names = QFontDatabase.applicationFontFamilies(fid)
                if names:
                    app.setFont(QFont(names[0], 10))
                    return names[0]
    fallback = "Tahoma" if __import__("sys").platform == "win32" else "Sans Serif"
    app.setFont(QFont(fallback, 10))
    return fallback


def stylesheet(mode: str) -> str:
    dark = mode == "dark"
    bg = "#0C1425" if dark else "#F3F6FB"
    sidebar = "#111D33" if dark else "#FFFFFF"
    surface = "#16243C" if dark else "#FFFFFF"
    raised = "#1E3050" if dark else "#EDF2FA"
    text = "#EEF4FF" if dark else "#1B2B46"
    muted = "#A5B6D2" if dark else "#687992"
    line = "#2C405F" if dark else "#E0E7F0"
    hover = "#273D60" if dark else "#E6EEFD"
    selected = "#264A7B" if dark else "#DCE9FF"
    accent = "#5C8DFF" if dark else "#336DE6"
    return f"""
    QWidget#AppRoot {{ background: {bg}; color: {text}; }}
    QWidget#SideBar {{ background: {sidebar}; border-left: 1px solid {line}; }}
    QWidget#MainArea {{ background: {bg}; }}
    QWidget#TopBar {{ background: {surface}; border: 1px solid {line}; border-radius: 13px; }}
    QWidget#WelcomeCard {{ background: {surface}; border: 1px solid {line}; border-radius: 24px; }}
    QLabel {{ color: {text}; background: transparent; }}
    QLabel#MutedText {{ color: {muted}; }}
    QLabel#AppTitle {{ font-size: 19px; font-weight: 700; }}
    QLabel#SectionTitle {{ font-size: 18px; font-weight: 700; }}
    QLabel#WelcomeTitle {{ font-size: 27px; font-weight: 700; }}
    QLineEdit, QTextEdit {{ color: {text}; background: {raised}; border: 1px solid {line};
                           border-radius: 10px; padding: 10px 12px; selection-background-color: {accent}; }}
    QLineEdit:focus, QTextEdit:focus {{ border: 1px solid {accent}; }}
    QPushButton, QToolButton {{ color: {text}; background: {raised}; border: 1px solid {line};
                                border-radius: 10px; padding: 9px 13px; font-weight: 600; }}
    QPushButton:hover, QToolButton:hover {{ background: {hover}; }}
    QPushButton:disabled, QToolButton:disabled {{ color: {muted}; }}
    QPushButton#PrimaryButton {{ color: #FFFFFF; background: {accent}; border: 0;
                                 font-weight: 700; padding: 12px; }}
    QPushButton#PrimaryButton:hover {{ background: #477FF2; }}
    QListWidget {{ background: transparent; color: {text}; border: 0; outline: none; }}
    QListWidget::item {{ padding: 13px 12px; margin: 3px 0; border-radius: 11px; }}
    QListWidget::item:hover {{ background: {hover}; }}
    QListWidget::item:selected {{ background: {selected}; color: {text}; border: 1px solid {accent}; }}
    QSplitter::handle {{ background: {line}; width: 4px; }}
    QMenu, QDialog, QMessageBox {{ background: {surface}; color: {text}; }}
    QMenu {{ border: 1px solid {line}; padding: 6px; }}
    QMenu::item {{ padding: 9px 28px; border-radius: 7px; }}
    QMenu::item:selected {{ background: {hover}; }}
    QScrollBar:vertical {{ background: transparent; width: 9px; }}
    QScrollBar::handle:vertical {{ background: {line}; border-radius: 4px; min-height: 24px; }}
    """
