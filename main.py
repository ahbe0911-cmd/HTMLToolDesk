"""Application entry point. Run with: python main.py"""
import sys
from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtWidgets import QApplication, QMessageBox
from html_tooldesk.storage import Store
from html_tooldesk.theme import install_font
from html_tooldesk.window import MainWindow


def create_application(argv: list[str] | None = None) -> QApplication:
    """Prepare Qt WebEngine before QApplication, keeping Chromium lazy-loaded."""
    # QtWebEngineWidgets can only be imported after QApplication exists when
    # this attribute was explicitly set BEFORE QApplication construction.
    # Without it the first HTML selection raises an ImportError on Windows.
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    return QApplication(sys.argv if argv is None else argv)


def main() -> int:
    app = create_application(sys.argv)
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
