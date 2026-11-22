"""Offscreen GUI smoke test: no Chromium startup is necessary."""
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtWidgets import QApplication, QWidget
from main import create_application
from html_tooldesk.models import Tool
from html_tooldesk.storage import Store
from html_tooldesk.window import MainWindow
from html_tooldesk.tool_cards import ToolCardDelegate, color_for_tool
from html_tooldesk.jalali import format_jalali_date


class TestMainWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or create_application([])

    def test_webengine_can_be_imported_after_qapplication_is_created(self):
        """Reproduce the reported crash without spinning up a Chromium process."""
        self.assertTrue(
            QCoreApplication.testAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts),
            "Qt shared OpenGL contexts must be enabled BEFORE creating QApplication",
        )
        # The 2026-11-22 build crashed exactly on this late module import.
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        self.assertIsNotNone(QWebEngineView)

    def test_returning_to_cached_html_never_reloads_file(self):
        """Switching between saved tools reuses pages rather than creating tabs."""
        class FakeView(QWidget):
            def __init__(self):
                super().__init__()
                self.loads = []
                self.zooms = []
            def setZoomFactor(self, value):
                self.zooms.append(value)
            def load(self, url):
                self.loads.append(url.toLocalFile())
            def page(self):
                return self
            def scripts(self):
                return self
            def clear(self):
                pass
            def insert(self, script):
                pass

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = [root / "first.html", root / "second.html"]
            for file in paths:
                file.write_text("<html><body>ready</body></html>", encoding="utf-8")
            tools = [Tool.create("اول", str(paths[0])), Tool.create("دوم", str(paths[1]))]
            store = Store(root / "settings.json")
            store.with_items(tools)
            window = MainWindow(Store(root / "settings.json"))
            first, second = FakeView(), FakeView()
            first.setParent(window.stack)
            second.setParent(window.stack)
            window.stack.addWidget(first)
            window.stack.addWidget(second)
            window._ensure_browser = lambda: None
            window._view_cache = {tools[0].id: first, tools[1].id: second}
            window._view_order = [tools[0].id, tools[1].id]
            window._get_view_for_tool = lambda tool_id: window._view_cache[tool_id]
            try:
                window.show_tool(tools[0])
                window.show_tool(tools[1])
                window.show_tool(tools[0])
                self.assertEqual(len(first.loads), 1)
                self.assertEqual(len(second.loads), 1)
                self.assertIs(window.stack.currentWidget(), first)
                window.zoom_in()
                window.zoom_in()
                self.assertAlmostEqual(first.zooms[-1], 1.2)
                self.assertEqual(window.zoom_reset_button.text(), "۱۲۰٪")
                self.assertEqual(len(first.loads), 1, "Zoom must not reload HTML")
                window.show_tool(tools[1])
                self.assertAlmostEqual(second.zooms[-1], 1.0, "Each tool gets its own zoom")
                window.zoom_out()
                self.assertAlmostEqual(second.zooms[-1], 0.9)
                window.show_tool(tools[0])
                self.assertAlmostEqual(first.zooms[-1], 1.2)
                window.zoom_reset()
                self.assertAlmostEqual(first.zooms[-1], 1.0)
                self.assertEqual(window.zoom_reset_button.text(), "۱۰۰٪")
                self.assertEqual(window.list_widget.count(), 2)
            finally:
                window.close()

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
                self.assertIsInstance(window.list_widget.itemDelegate(), ToolCardDelegate)
                self.assertEqual(window.date_label.text(), format_jalali_date())
                self.assertTrue(window.zoom_in_button is not None)
                self.assertEqual(window.list_widget.item(0).text(), "ابزار یک")
                self.assertFalse(window.list_widget.item(0).icon().isNull())
                bg, border, accent = color_for_tool(store.state.items[0].id)
                self.assertTrue(bg.startswith("#"))
                self.assertNotEqual(bg, border)
                self.assertNotEqual(border, accent)
                self.assertIsNone(window.browser, "Chromium should be lazy-loaded")
                self.assertIsNone(window.profile, "No Chromium profile should be created at startup")
                self.assertIn("روی ابزار موردنظر", window.welcome.message.text())
                self.assertEqual(window.welcome.arrow.text(), "↗")
                # Even after Qt processes startup events, no WebEngine preload may run.
                from PyQt6.QtTest import QTest
                QTest.qWait(600)
                self.assertIsNone(window.profile, "No hidden background Chromium warm-up")
                self.assertEqual(window.splitter.widget(1), window.sidebar)
                window.search.setText("دوم")
                self.assertEqual(window.list_widget.count(), 1)
                self.assertEqual(window.list_widget.item(0).text(), "ابزار دوم")
            finally:
                window.close()


if __name__ == "__main__":
    unittest.main()
