"""Application entry point. Run with: python main.py"""
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox
from html_tooldesk.storage import Store
from html_tooldesk.theme import install_font
from html_tooldesk.window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("میزکار ابزارهای HTML")
    app.setOrganizationName("HTMLToolDesk")
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    install_font(app)
    try:
        store = Store()
        window = MainWindow(store)
        window.show()
        return app.exec()
    except Exception as exc:
        QMessageBox.critical(None, "خطا در اجرای برنامه", f"برنامه نتوانست اجرا شود:\n{exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
