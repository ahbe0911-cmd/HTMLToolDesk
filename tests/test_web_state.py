"""Regression tests for native HTML web-storage recovery.

A restored backup often exists in localStorage or sessionStorage. The native
mirror must not be overwritten by invalid JS results and must survive a full
application restart using the same persistent AppData location.
"""
import json
import tempfile
import unittest
from pathlib import Path

from html_tooldesk.web_state import (
    CAPTURE_SCRIPT, MAX_SNAPSHOT_BYTES,
    read_snapshot, restore_script, save_snapshot, snapshot_path,
)


class TestWebState(unittest.TestCase):
    def test_backup_restore_survives_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "tool.html"
            source.write_text("<html></html>", encoding="utf-8")
            loaded = {
                "local": {"data": '{"customers":[{"name":"سارا"}]}', "saved": "بازیابی"},
                "session": {"open_tab": "۴۲"},
                "url": source.as_uri(),
            }
            self.assertTrue(save_snapshot("tool-1", str(source), loaded, root))
            # Simulates the next process reading its own on-disk backup.
            result = read_snapshot("tool-1", str(source), root)
            self.assertEqual(result["local"]["saved"], "بازیابی")
            self.assertEqual(result["session"]["open_tab"], "۴۲")
            script = restore_script(result)
            self.assertIn("localStorage", script)
            self.assertIn("sessionStorage", script)
            self.assertIn("setItem", script)
            self.assertIn("getItem(k) === null", script)
            self.assertTrue(CAPTURE_SCRIPT.startswith("(() =>"))

    def test_separation_and_safe_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            a = root / "first.html"
            b = root / "second.html"
            self.assertTrue(save_snapshot("../../unsafe", str(a), {
                "local": {"x": "1"}, "session": {}
            }, root))
            self.assertEqual(read_snapshot("../../unsafe", str(a), root)["local"]["x"], "1")
            self.assertEqual(read_snapshot("../../unsafe", str(b), root), {})
            self.assertEqual(read_snapshot("another-tool", str(a), root), {})
            self.assertEqual(snapshot_path("../../unsafe", root).parent, root)
            self.assertNotIn("..", snapshot_path("../../unsafe", root).name)

    def test_invalid_js_response_never_overwrites_good_data(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = str(root / "sample.html")
            self.assertTrue(save_snapshot("one", source, {
                "local": {"value": "saved"}, "session": {}
            }, root))
            self.assertFalse(save_snapshot("one", source, {"local": None}, root))
            self.assertFalse(save_snapshot("one", source, None, root))
            self.assertFalse(save_snapshot("one", source, {
                "local": {"value": 42}, "session": {}
            }, root))
            self.assertEqual(read_snapshot("one", source, root)["local"]["value"], "saved")

    def test_reject_large_snapshots(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = str(root / "sample.html")
            self.assertFalse(save_snapshot("one", source, {
                "local": {"large": "x" * (MAX_SNAPSHOT_BYTES + 1)},
                "session": {},
            }, root))
            self.assertFalse(snapshot_path("one", root).exists())

    def test_missing_or_corrupt_file_is_not_fatal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = str(root / "sample.html")
            self.assertEqual(read_snapshot("one", source, root), {})
            target = snapshot_path("one", root)
            target.write_text("{bad json", encoding="utf-8")
            self.assertEqual(read_snapshot("one", source, root), {})


if __name__ == "__main__":
    unittest.main()
