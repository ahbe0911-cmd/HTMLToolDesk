"""Persian tool add/edit dialog."""
from __future__ import annotations

from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QFileDialog, QMessageBox,
)
from .models import Tool


class ToolDialog(QDialog):
    def __init__(self, parent=None, tool: Tool | None = None):
        super().__init__(parent)
        self.original = tool
        self.setWindowTitle("ویرایش ابزار" if tool else "افزودن ابزار جدید")
        self.setModal(True)
        self.setMinimumWidth(510)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 22)
        layout.setSpacing(11)

        title_label = QLabel("عنوان فارسی ابزار *")
        self.title_input = QLineEdit(tool.title if tool else "")
        self.title_input.setPlaceholderText("مثلاً: محاسبه‌گر پیشرفته")
        self.title_input.setMaxLength(120)
        layout.addWidget(title_label)
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("توضیح کوتاه (اختیاری)"))
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("این ابزار چه کاری انجام می‌دهد؟")
        self.description_input.setFixedHeight(88)
        self.description_input.setPlainText(tool.description if tool else "")
        layout.addWidget(self.description_input)

        layout.addWidget(QLabel("مسیر فایل HTML *"))
        path_row = QHBoxLayout()
        self.path_input = QLineEdit(tool.path if tool else "")
        self.path_input.setPlaceholderText("یک فایل .html یا .htm انتخاب کنید")
        self.path_input.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.path_input.setAlignment(Qt.AlignmentFlag.AlignLeft)
        browse_button = QPushButton("انتخاب فایل…")
        browse_button.clicked.connect(self.choose_file)
        path_row.addWidget(self.path_input, stretch=1)
        path_row.addWidget(browse_button)
        layout.addLayout(path_row)

        controls = QHBoxLayout()
        controls.addStretch(1)
        cancel = QPushButton("انصراف")
        cancel.clicked.connect(self.reject)
        save = QPushButton("ذخیره ابزار")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self.validate_and_accept)
        controls.addWidget(cancel)
        controls.addWidget(save)
        layout.addSpacing(10)
        layout.addLayout(controls)
        self.title_input.setFocus()

    def choose_file(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "انتخاب فایل HTML", self.path_input.text().strip() or str(Path.home()),
            "HTML Files (*.html *.htm);;All Files (*)",
        )
        if filename:
            self.path_input.setText(filename)

    def validate_and_accept(self) -> None:
        title = self.title_input.text().strip()
        path = Path(self.path_input.text().strip().strip('"')).expanduser()
        if not title:
            QMessageBox.warning(self, "اطلاعات ناقص", "لطفاً عنوان فارسی ابزار را وارد کنید.")
            return
        if path.suffix.lower() not in (".html", ".htm"):
            QMessageBox.warning(self, "فایل نامعتبر", "فایل انتخاب‌شده باید پسوند HTML یا HTM داشته باشد.")
            return
        # Existing broken paths are allowed when editing the title/description only.
        same_broken_path = self.original is not None and str(path) == self.original.path
        if not path.is_file() and not same_broken_path:
            QMessageBox.warning(self, "فایل پیدا نشد", "فایل HTML در مسیر انتخاب‌شده وجود ندارد.")
            return
        self.accept()

    def get_tool(self) -> Tool:
        title = self.title_input.text().strip()
        description = self.description_input.toPlainText().strip()
        path = str(Path(self.path_input.text().strip().strip('"')).expanduser().resolve())
        if self.original:
            return Tool(self.original.id, title, path, description)
        return Tool.create(title, path, description)
