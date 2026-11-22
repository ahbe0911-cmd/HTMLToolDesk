"""Modern, colorful framed sidebar cards without per-item QWidget overhead.

A single QStyledItemDelegate paints all cards. Drag/drop sorting, text search,
keyboard selection and context menus continue to work with QListWidget.
"""
from __future__ import annotations

from hashlib import blake2b

from PyQt6.QtCore import Qt, QRect, QRectF, QSize
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QIcon
from PyQt6.QtWidgets import QStyledItemDelegate, QStyle

ROLE_ID = Qt.ItemDataRole.UserRole

# Each card has a cheerful, legible surface even in a compact 252px sidebar.
LIGHT_PALETTE = (
    ("#EEEAFE", "#D9D0FD", "#7662EB"),
    ("#E5F8FD", "#C6EEF5", "#0599BB"),
    ("#FFF1E2", "#F9DEC3", "#E18C26"),
    ("#E8F9F0", "#C9EDD9", "#15966C"),
    ("#FEEAF2", "#F8CFE0", "#D64B83"),
    ("#E8F0FF", "#D0DFFF", "#477BE6"),
)
DARK_PALETTE = (
    ("#292747", "#484071", "#B4A2FF"),
    ("#173541", "#275566", "#82D9EC"),
    ("#3C3026", "#69503A", "#FFD092"),
    ("#1F3A32", "#335B4B", "#89E0BB"),
    ("#3A2938", "#63445A", "#FF9EC5"),
    ("#25344D", "#425776", "#A7C2FF"),
)


def color_for_tool(tool_id: str, dark: bool = False) -> tuple[str, str, str]:
    idx = int.from_bytes(
        blake2b(str(tool_id).encode("utf-8"), digest_size=2).digest(), "big"
    ) % len(LIGHT_PALETTE)
    return (DARK_PALETTE if dark else LIGHT_PALETTE)[idx]


class ToolCardDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, dark: bool = False):
        super().__init__(parent)
        self.dark = dark

    def sizeHint(self, option, index):
        return QSize(215, 54)

    def paint(self, painter: QPainter, option, index) -> None:
        tool_id = index.data(ROLE_ID) or ""
        bg, border, accent = color_for_tool(str(tool_id), self.dark)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        rect = option.rect.adjusted(2, 3, -2, -3)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rounded = QPainterPath()
        rounded.addRoundedRect(QRectF(rect), 11, 11)
        fill = QColor(bg)
        if hovered:
            fill = fill.lighter(106)
        painter.fillPath(rounded, fill)
        painter.setPen(QPen(QColor(accent if selected else border), 1.5 if selected else 1.0))
        painter.drawPath(rounded)

        # A vertical accent on the right edge makes each tool easy to scan.
        strip = QRectF(rect.right() - 4, rect.top() + 11, 3, rect.height() - 22)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(accent))
        painter.drawRoundedRect(strip, 1.5, 1.5)

        # Icon badge, with the item's stable-colored SVG.
        icon_size = 20
        badge = QRect(rect.right() - 41, rect.center().y() - 16, 31, 32)
        badge_color = QColor(accent)
        badge_color.setAlpha(29 if not self.dark else 65)
        painter.setBrush(badge_color)
        painter.drawRoundedRect(QRectF(badge), 8, 8)
        tool_icon = index.data(Qt.ItemDataRole.DecorationRole)
        if isinstance(tool_icon, QIcon):
            icon_rect = QRect(
                badge.left() + (badge.width() - icon_size) // 2,
                badge.top() + (badge.height() - icon_size) // 2,
                icon_size, icon_size,
            )
            tool_icon.paint(painter, icon_rect)

        label_rect = QRect(rect.left() + 10, rect.top() + 3, rect.width() - 61, rect.height() - 6)
        font = QFont(option.font)
        font.setWeight(QFont.Weight.DemiBold if selected else QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(QColor("#F7FAFF" if self.dark else "#25344E"))
        title = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        title = painter.fontMetrics().elidedText(title, Qt.TextElideMode.ElideLeft, label_rect.width())
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, title)
        painter.restore()
