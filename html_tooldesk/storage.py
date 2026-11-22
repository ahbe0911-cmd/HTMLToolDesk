"""Atomic config.json storage; portable folder with AppData fallback."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from .models import AppState, Tool

APP_DIRNAME = "HTMLToolDesk"


def executable_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def user_data_directory() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / APP_DIRNAME
    if os.name == "nt":
        return Path.home() / "AppData" / "Local" / APP_DIRNAME
    return Path.home() / ".local" / "share" / APP_DIRNAME


def is_writable_directory(folder: Path) -> bool:
    try:
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=folder):
            pass
        return True
    except OSError:
        return False


def choose_config_path() -> Path:
    """Use a stable user directory even when an EXE runs from a temporary ZIP folder."""
    return user_data_directory() / "config.json"


class Store:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else choose_config_path()
        self.warning = ""
        if path is None:
            self._migrate_legacy_portable()
        self.state = self.load()

    def _migrate_legacy_portable(self) -> None:
        """Import an older config saved next to an EXE, without overwriting AppData."""
        old_path = executable_directory() / "config.json"
        if self.path.exists() or not old_path.is_file() or old_path == self.path:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old_path, self.path)
        except OSError as exc:
            self.warning = f"انتقال اطلاعات نسخه قبلی انجام نشد: {exc}"

    def load(self) -> AppState:
        if not self.path.exists():
            return AppState()
        try:
            content = json.loads(self.path.read_text(encoding="utf-8-sig"))
            if not isinstance(content, dict):
                raise ValueError("config.json must be an object")
            raw = content.get("tools", [])
            if not isinstance(raw, list):
                raise ValueError("tools must be an array")
            items: list[Tool] = []
            seen: set[str] = set()
            for entry in raw:
                try:
                    item = Tool.from_dict(entry)
                    if item.id not in seen:
                        items.append(item)
                        seen.add(item.id)
                except (TypeError, ValueError):
                    continue
            return AppState(
                items=items,
                theme=content.get("theme") if content.get("theme") in ("dark", "light") else "light",
                sidebar_width=max(240, min(520, int(content.get("sidebar_width", 320)))),
            )
        except (OSError, ValueError, TypeError, OverflowError) as exc:
            suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = self.path.with_name(f"config.broken.{suffix}.json")
            try:
                self.path.replace(backup)
                self.warning = f"فایل تنظیمات آسیب‌دیده بود و در این مسیر پشتیبان‌گیری شد:\n{backup}"
            except OSError:
                self.warning = f"خواندن تنظیمات ممکن نشد: {exc}"
            return AppState()

    def save_state(self, next_state: AppState) -> None:
        """Save first, then replace in-memory state to avoid partial mutations."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".tmp",
                                             prefix="config_", dir=self.path.parent,
                                             delete=False) as handle:
                tmp_path = Path(handle.name)
                json.dump(next_state.to_dict(), handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, self.path)
            self.state = next_state
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)

    def with_items(self, items: list[Tool]) -> None:
        self.save_state(AppState(list(items), self.state.theme, self.state.sidebar_width))

    def set_theme(self, theme: str) -> None:
        self.save_state(AppState(list(self.state.items), theme, self.state.sidebar_width))

    def set_sidebar_width(self, width: int) -> None:
        self.save_state(AppState(list(self.state.items), self.state.theme, max(240, min(520, width))))
