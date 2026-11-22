"""Pure-Python tests; PyQt6 is not required to run these tests."""
import json
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
