"""Pure-Python tests; PyQt6 is not required to run these tests."""
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from html_tooldesk.models import Tool
from html_tooldesk.storage import Store


class TestStore(unittest.TestCase):
    def test_persists_unicode_and_order(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "config.json"
            store = Store(path)
            first = Tool.create("محاسبه‌گر", str(Path(folder) / "a.html"), "تست")
            second = Tool.create("صفحه دوم", str(Path(folder) / "b.htm"))
            store.with_items([first, second])
            self.assertEqual([t.title for t in Store(path).state.items], ["محاسبه‌گر", "صفحه دوم"])
            store.with_items([second, first])
            self.assertEqual([t.id for t in Store(path).state.items], [second.id, first.id])
            self.assertIn("محاسبه‌گر", path.read_text(encoding="utf-8"))

    def test_corrupted_config_is_backed_up(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "config.json"
            path.write_text("{not json", encoding="utf-8")
            store = Store(path)
            self.assertEqual([], store.state.items)
            self.assertTrue(store.warning)
            self.assertEqual(1, len(list(Path(folder).glob("config.broken.*.json"))))

    def test_invalid_rows_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "config.json"
            path.write_text(json.dumps({"tools": [{"id": "1", "title": "کار", "path": "a.html"}, {"path": "bad"}]}), encoding="utf-8")
            self.assertEqual(1, len(Store(path).state.items))

    def test_search_normalizes_arabic_persian_letters(self):
        item = Tool.create("كاربردي", "test.html")
        self.assertTrue(item.matches("کاربردی"))
        self.assertFalse(item.matches("فهرست"))


    def test_default_config_stays_in_appdata_after_executable_moves(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            appdata = root / "appdata"
            old_exe = root / "old-version"
            new_exe = root / "new-version"
            old_exe.mkdir()
            new_exe.mkdir()
            with patch.dict(os.environ, {"LOCALAPPDATA": str(appdata)}):
                with patch("html_tooldesk.storage.executable_directory", return_value=old_exe):
                    first = Store()
                    first.with_items([Tool.create("ابزار ماندگار", str(root / "first.html"))])
                with patch("html_tooldesk.storage.executable_directory", return_value=new_exe):
                    second = Store()
                    self.assertEqual([x.title for x in second.state.items], ["ابزار ماندگار"])
                    self.assertEqual(second.path, appdata / "HTMLToolDesk" / "config.json")
                    self.assertFalse((new_exe / "config.json").exists())

    def test_migrates_older_exe_side_config_once(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            appdata = root / "appdata"
            portable = root / "previous"
            portable.mkdir()
            legacy = portable / "config.json"
            legacy.write_text(json.dumps({"tools": [
                {"id": "older", "title": "ابزار قدیمی", "path": "C:/tools/old.html"}
            ], "theme": "light"}), encoding="utf-8")
            with patch.dict(os.environ, {"LOCALAPPDATA": str(appdata)}):
                with patch("html_tooldesk.storage.executable_directory", return_value=portable):
                    first = Store()
                    self.assertEqual(first.state.items[0].title, "ابزار قدیمی")
                    first.with_items([Tool.create("ابزار جدید", "C:/tools/new.html")])
                    second = Store()
                    self.assertEqual(second.state.items[0].title, "ابزار جدید")
                    self.assertEqual(len(second.state.items), 1)
                    self.assertTrue(legacy.exists())


if __name__ == "__main__":
    unittest.main()
