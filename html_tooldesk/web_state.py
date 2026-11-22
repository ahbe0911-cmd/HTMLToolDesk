"""Fail-safe local web-storage snapshots for registered local HTML tools.

Qt WebEngine normally persists HTML5 LocalStorage in the profile directory.
This separate native snapshot is a recovery layer for local-file origins
and application restarts. It is NOT a database dump: IndexedDB, CacheStorage,
and in-memory JavaScript variables cannot be captured through this API.
Only files stored under the application-specific user data directory are used.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from .storage import user_data_directory

MAX_SNAPSHOT_BYTES = 8 * 1024 * 1024

CAPTURE_SCRIPT = r"""(() => {
  const out = {local: {}, session: {}, url: location.href};
  for (const [label, store] of [['local', window.localStorage], ['session', window.sessionStorage]]) {
    try {
      for (let i=0; i < store.length; i++) {
        const key = store.key(i);
        if (key !== null) out[label][key] = store.getItem(key);
      }
    } catch (_) {}
  }
  return out;
})()"""


def snapshot_path(tool_id: str, root: Path | None = None) -> Path:
    name = hashlib.sha256(tool_id.encode("utf-8")).hexdigest()[:32] + ".json"
    return (Path(root) if root is not None else user_data_directory() / "web_snapshots") / name


def read_snapshot(tool_id: str, path: str, root: Path | None = None) -> dict:
    dest = snapshot_path(tool_id, root)
    try:
        if not dest.is_file() or dest.stat().st_size > MAX_SNAPSHOT_BYTES:
            return {}
        data = json.loads(dest.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("path") != str(Path(path).resolve()):
            return {}
        return {
            "local": data.get("local", {}) if isinstance(data.get("local"), dict) else {},
            "session": data.get("session", {}) if isinstance(data.get("session"), dict) else {},
        }
    except (OSError, ValueError, TypeError):
        return {}


def save_snapshot(tool_id: str, path: str, result: object, root: Path | None = None) -> bool:
    """Atomically store a verified snapshot. Never overwrite valid data on JS errors."""
    if not isinstance(result, dict):
        return False
    if not all(isinstance(result.get(k), dict) for k in ("local", "session")):
        return False
    if not all(
        isinstance(k, str) and isinstance(v, str)
        for name in ("local", "session")
        for k, v in result[name].items()
    ):
        return False
    payload = {
        "version": 1,
        "path": str(Path(path).resolve()),
        "local": result["local"],
        "session": result["session"],
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_SNAPSHOT_BYTES:
        return False
    dest = snapshot_path(tool_id, root)
    try:
        # Avoid repeated writes when the HTML has not changed.
        if dest.exists() and dest.read_bytes() == encoded:
            return True
        dest.parent.mkdir(parents=True, exist_ok=True)
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(dir=dest.parent, prefix="web_state_", suffix=".tmp",
                                             delete=False) as tmp:
                temp_name = tmp.name
                tmp.write(encoded)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(temp_name, dest)
            return True
        finally:
            if temp_name:
                Path(temp_name).unlink(missing_ok=True)
    except OSError:
        return False


def restore_script(snapshot: dict) -> str:
    """Return JS for document-creation time: before the HTML app initializes.

    Do not overwrite existing browser data. Backups only fill missing keys,
    so a normally persisted browser profile remains authoritative.
    """
    safe = {
        name: {
            key: value for key, value in (snapshot.get(name) or {}).items()
            if isinstance(key, str) and isinstance(value, str)
        }
        for name in ("local", "session")
    }
    payload = json.dumps(safe, ensure_ascii=True)
    return (
        "(() => { try { const saved = " + payload + ";"
        " for (const [key, store] of [['local',window.localStorage],"
        " ['session',window.sessionStorage]]) {"
        " try { for (const [k,v] of Object.entries(saved[key]))"
        " if (store.getItem(k) === null) store.setItem(k,v); } catch (_) {}"
        " } } catch (_) {} })();"
    )
