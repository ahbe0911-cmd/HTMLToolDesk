"""Application models and Persian-friendly search normalization."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4


def normalize(text: str) -> str:
    return (text or "").strip().casefold().replace("ي", "ی").replace("ك", "ک")


@dataclass
class Tool:
    id: str
    title: str
    path: str
    description: str = ""

    @classmethod
    def create(cls, title: str, path: str, description: str = "") -> "Tool":
        return cls(str(uuid4()), title.strip(), str(Path(path).expanduser().resolve()), description.strip())

    @classmethod
    def from_dict(cls, data: dict) -> "Tool":
        if not isinstance(data, dict):
            raise ValueError("Tool must be an object")
        values = [data.get(key) for key in ("id", "title", "path")]
        if not all(isinstance(value, str) and value.strip() for value in values):
            raise ValueError("Invalid tool data")
        desc = data.get("description", "")
        return cls(values[0].strip(), values[1].strip(), values[2].strip(), desc if isinstance(desc, str) else "")

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title, "description": self.description, "path": self.path}

    def matches(self, query: str) -> bool:
        return normalize(query) in normalize(self.title)


@dataclass
class AppState:
    items: list[Tool] = field(default_factory=list)
    theme: str = "light"
    sidebar_width: int = 252

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "theme": self.theme,
            "sidebar_width": self.sidebar_width,
            "tools": [item.to_dict() for item in self.items],
        }
