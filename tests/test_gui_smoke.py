"""Offscreen GUI smoke test: no Chromium startup is necessary."""
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication
from html_tooldesk.models import Tool
from html_tooldesk.storage import Store
from html_tooldesk.window import MainWindow


class TestMainWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_saved_tools_render_in_right_sidebar_without_browser_startup(self):
        with tempfile.TemporaryDirectory() as temp:
            statefile = Path(temp) / "config.json"
            store = Store(statefile)
            store.with_items([
                Tool.create("ابزار یک", str(Path(temp) / "first.html")),
                Tool.create("ابزار دوم", str(Path(temp) / "second.html")),
            ])
            window = MainWindow(Store(statefile))
            try:
                self.assertEqual(window.list_widget.count(), 2)
                self.assertEqual(window.list_widget.item(0).text(), "ابزار یک")
                self.assertFalse(window.list_widget.item(0).icon().isNull())
                self.assertIsNone(window.browser, "Chromium should be lazy-loaded")
                self.assertEqual(window.splitter.widget(1), window.sidebar)
                window.search.setText("دوم")
                self.assertEqual(window.list_widget.count(), 1)
                self.assertEqual(window.list_widget.item(0).text(), "ابزار دوم")
            finally:
                window.close()


if __name__ == "__main__":
    unittest.main()
