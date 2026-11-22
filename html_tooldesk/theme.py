"""Premium light/dark palette and local Vazirmatn typography."""
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
    bg = "#0B1220" if dark else "#F5F7FC"
    sidebar = "#101D32" if dark else "#FFFFFF"
    surface = "#15233A" if dark else "#FFFFFF"
    raised = "#1B2A43" if dark else "#F0F4FC"
    text = "#EDF3FD" if dark else "#1B2940"
    muted = "#A2B5CF" if dark else "#6E7F99"
    line = "#263A55" if dark else "#E3E9F3"
    hover = "#243653" if dark else "#EDF2FC"
    selected = "#283C64" if dark else "#E7EDFF"
    accent = "#878FFF" if dark else "#525FF5"
    return f"""
    QWidget#AppRoot {{ background: {bg}; color: {text}; }}
    QWidget#SideBar {{ background: {sidebar}; border-left: 1px solid {line}; }}
    QWidget#MainArea {{ background: {bg}; }}
    QWidget#TopBar {{ background: {surface}; border: 1px solid {line}; border-radius: 16px; }}
    QWidget#WelcomeCard {{ background: {surface}; border: 1px solid {line}; border-radius: 24px; }}
    QWidget#HeroBadge {{ background: {selected}; border-radius: 18px; }}
    QFrame#SideRule {{ background: {line}; max-height: 1px; min-height: 1px; }}
    QLabel {{ color: {text}; background: transparent; }}
    QLabel#MutedText {{ color: {muted}; font-size: 12px; }}
    QLabel#AppTitle {{ font-size: 20px; font-weight: 750; }}
    QLabel#SectionTitle {{ font-size: 18px; font-weight: 700; }}
    QLabel#WelcomeTitle {{ font-size: 29px; font-weight: 750; }}
    QLabel#BrandCaption {{ color: {accent}; letter-spacing: 2px; font-size: 11px; font-weight: 700; }}
    QLabel#SectionCaption {{ color: {muted}; font-size: 12px; font-weight: 600; }}
    QLineEdit, QTextEdit {{ color: {text}; background: {raised}; border: 1px solid {line};
        border-radius: 12px; padding: 11px 13px; selection-background-color: {accent}; }}
    QLineEdit:focus, QTextEdit:focus {{ border-color: {accent}; }}
    QPushButton, QToolButton {{ color: {text}; background: {raised}; border: 1px solid {line};
        border-radius: 11px; padding: 9px 12px; font-weight: 600; }}
    QPushButton:hover, QToolButton:hover {{ background: {hover}; border-color: {accent}; }}
    QPushButton:pressed, QToolButton:pressed {{ background: {selected}; }}
    QPushButton:disabled, QToolButton:disabled {{ color: {muted}; }}
    QPushButton#PrimaryButton {{ color: #FFFFFF; background: {accent}; border: 0;
        border-radius: 13px; font-weight: 700; padding: 13px; font-size: 13px; }}
    QPushButton#PrimaryButton:hover {{ background: #6673FA; }}
    QToolButton#IconButton {{ min-width: 40px; min-height: 38px; }}
    QListWidget#ToolList {{ background: transparent; color: {text}; border: 0;
        outline: none; font-size: 13px; font-weight: 600; }}
    QListWidget#ToolList::item {{ padding: 4px 13px; margin: 3px 0;
        border: 1px solid transparent; border-radius: 13px; }}
    QListWidget#ToolList::item:hover {{ background: {hover}; }}
    QListWidget#ToolList::item:selected {{ background: {selected}; color: {text}; border-color: {accent}; }}
    QSplitter::handle {{ background: {line}; width: 3px; }}
    QMenu, QDialog, QMessageBox {{ background: {surface}; color: {text}; }}
    QMenu {{ border: 1px solid {line}; padding: 7px; border-radius: 11px; }}
    QMenu::item {{ padding: 11px 28px; border-radius: 7px; }}
    QMenu::item:selected {{ background: {hover}; }}
    QScrollBar:vertical {{ background: transparent; width: 8px; }}
    QScrollBar::handle:vertical {{ background: {line}; border-radius: 4px; min-height: 24px; }}
    """
