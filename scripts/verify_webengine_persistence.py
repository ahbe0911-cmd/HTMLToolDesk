"""Windows CI end-to-end storage test across TWO application processes.

This reproduces a user importing a backup into an HTML app, quitting, and
opening the same HTML from its saved sidebar entry in the next process.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Running a script by path makes scripts/ the first import root, not the repo.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def child(mode: str, base: Path) -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --no-sandbox")

    from PyQt6.QtCore import QTimer
    from main import create_application
    from html_tooldesk.models import Tool
    from html_tooldesk.storage import Store
    import html_tooldesk.window as window_module
    import html_tooldesk.web_state as state_module

    print(f"Qt WebEngine child phase={mode}, Python={sys.version}", flush=True)
    appdata = base / "appdata"
    window_module.user_data_directory = lambda: appdata
    state_module.user_data_directory = lambda: appdata

    source = base / "restored.html"
    source.write_text(
        '<!doctype html><html><meta charset="utf-8"><body>'
        '<h1>Storage persistence test</h1></body></html>',
        encoding="utf-8",
    )
    config = base / "config.json"
    store = Store(config)
    if not store.state.items:
        store.with_items([Tool.create("نسخه پشتیبان", str(source))])

    app = create_application([])
    win = window_module.MainWindow(Store(config))
    print("MainWindow created", flush=True)
    win.show()
    outcome = {"ok": False, "error": "timeout"}
    fired = {"value": False}

    def on_complete(ok):
        if fired["value"]:
            return
        fired["value"] = True
        if not ok:
            outcome["error"] = "HTML page load returned false"
            win.close()
            return
        if mode == "write":
            # Emulate the actual HTML tool importing its JSON backup.
            code = """(() => {
              localStorage.setItem('restored_rows', JSON.stringify([{id: 7, name: 'Persian'}]));
              sessionStorage.setItem('recovered_filter', 'recent');
              return localStorage.getItem('restored_rows');
            })()"""
        else:
            code = """(() => ({
              rows: localStorage.getItem('restored_rows'),
              filter: sessionStorage.getItem('recovered_filter')
            }))()"""

        def js_done(value):
            if mode == "write":
                outcome["ok"] = isinstance(value, str) and "Persian" in value
                outcome["error"] = "" if outcome["ok"] else f"JS write failed: {value!r}"
            else:
                outcome["ok"] = (isinstance(value, dict)
                                 and isinstance(value.get("rows"), str)
                                 and "Persian" in value["rows"]
                                 and value.get("filter") == "recent")
                outcome["error"] = "" if outcome["ok"] else f"Lost restored data: {value!r}"
            if outcome["ok"]:
                # Give the native mirror enough time to capture the updated state.
                QTimer.singleShot(900 if mode == "write" else 250, win.close)
            else:
                win.close()

        win.page.runJavaScript(code, js_done)

    def begin():
        win.show_tool(win.store.state.items[0])
        if win.browser is None:
            outcome["error"] = "WebEngine failed to create"
            win.close()
            return
        win.browser.loadFinished.connect(on_complete)

    def deadline():
        if not outcome["ok"]:
            print("WebEngine check timed out:", outcome["error"], flush=True)
        win.close()
        QTimer.singleShot(2000, app.quit)

    QTimer.singleShot(0, begin)
    QTimer.singleShot(20_000, deadline)
    app.exec()
    print(f"WebEngine {mode}: {'OK' if outcome['ok'] else outcome['error']}", flush=True)
    return 0 if outcome["ok"] else 1


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] in ("write", "read"):
        return child(sys.argv[1], Path(sys.argv[2]))
    with tempfile.TemporaryDirectory(prefix="htmltool-webtest-") as tmp:
        for phase in ("write", "read"):
            env = os.environ.copy()
            env["QT_QPA_PLATFORM"] = "offscreen"
            env["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox"
            result = subprocess.run(
                [sys.executable, __file__, phase, tmp],
                env=env, timeout=35, check=False,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                errors="replace",
            )
            print("WebEngine child return code:", result.returncode, flush=True)
            print("WebEngine stdout:", result.stdout[-4000:], flush=True)
            print("WebEngine stderr:", result.stderr[-4000:], flush=True)
            if result.returncode != 0:
                return result.returncode
        print("Two-process HTML backup recovery validated.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
