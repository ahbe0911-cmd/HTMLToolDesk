"""Compact, resolution-independent vector icons for navigation."""
from functools import lru_cache
from hashlib import blake2b

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

SHAPES = {
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "refresh": '<path d="M20 11a8 8 0 0 0-14-5L4 8m0-5v5h5M4 13a8 8 0 0 0 14 5l2-2m-5 0h5v5"/>',
    "external": '<path d="M14 4h6v6M20 4l-10 10"/><path d="M20 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h6"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32 1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>',
    "moon": '<path d="M20.5 15.5A8.5 8.5 0 0 1 8.5 3.5 8.5 8.5 0 1 0 20.5 15.5Z"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "code": '<path d="m8 8-4 4 4 4m8-8 4 4-4 4m-3-12-2 16"/><rect x="2" y="2" width="20" height="20" rx="4" stroke-opacity=".28"/>',
    "layout": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 9h18M10 9v12"/>',
    "calculator": '<rect x="5" y="2" width="14" height="20" rx="3"/><path d="M8 7h8M8 12h2m4 0h2m-8 4h2m4 0h2"/>',
    "chart": '<path d="M3 3v18h18M7 16l4-5 3 2 5-7"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    "note": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    "layers": '<path d="m12 2 9 5-9 5-9-5 9-5Zm-9 10 9 5 9-5M3 17l9 5 9-5"/>',
}

@lru_cache(maxsize=128)
def icon(name: str, color: str = "#5968F4", size: int = 24) -> QIcon:
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
           f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" '
           f'stroke-linecap="round" stroke-linejoin="round">{SHAPES.get(name, SHAPES["code"])}</svg>')
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

def tool_icon(identifier: str, dark: bool = False) -> QIcon:
    shapes = ("code", "layout", "calculator", "chart", "note", "layers", "grid")
    colors = ("#818CF8", "#06B6D4", "#A78BFA", "#F59E0B",
              "#10B981", "#F472B6", "#38BDF8")
    index = int.from_bytes(blake2b(identifier.encode("utf-8"), digest_size=2).digest(), "big") % len(shapes)
    return icon(shapes[index], colors[index], 25)
