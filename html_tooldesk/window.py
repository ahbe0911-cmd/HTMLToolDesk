"""Modern RTL desktop UI with a resizable right sidebar and Chromium viewport."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication, QAbstractItemView, QDialog, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu,
    QMessageBox, QPushButton, QSplitter, QStackedWidget, QToolButton,
    QVBoxLayout, QWidget,
)

from .dialogs import ToolDialog
from .models import Tool
from .storage import Store, user_data_directory
from .theme import stylesheet

ROLE_ID = Qt.ItemDataRole.UserRole


class WelcomePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        body = QVBoxLayout(self)
        body.setContentsMargins(28, 28, 28, 28)
        body.addStretch(1)

        card = QWidget()
        card.setObjectName("WelcomeCard")
        card.setMaximumWidth(650)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(45, 48, 45, 48)
        layout.setSpacing(16)

        logo = QLabel("✦   HTML TOOL DESK")
        logo.setObjectName("MutedText")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        self.title = QLabel("میزکار ابزارهای HTML")
        self.title.setObjectName("WelcomeTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setWordWrap(True)
        layout.addWidget(self.title)

        self.message = QLabel("ابزار موردنظر را از فهرست سمت راست انتخاب کنید،\nیا اولین فایل HTML خود را به میزکار اضافه کنید.")
        self.message.setObjectName("MutedText")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        body.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        body.addStretch(1)

    def show_welcome(self) -> None:
        self.title.setText("میزکار ابزارهای HTML")
        self.message.setText("ابزار موردنظر را از فهرست سمت راست انتخاب کنید،\nیا اولین فایل HTML خود را به میزکار اضافه کنید.")

    def show_error(self, path: str) -> None:
        self.title.setText("فایل HTML در دسترس نیست")
        self.message.setText("فایل اصلی جابه‌جا یا حذف شده است.\nاز منوی ابزار، گزینهٔ «ویرایش» را انتخاب و مسیر جدید را ثبت کنید.\n\n" + path)


class MainWindow(QMainWindow):
    def __init__(self, store: Store):
        super().__init__()
        self.store = store
        self.active_id: str | None = None
        self.active_path: str | None = None
        self._rebuilding = False
        self._last_sidebar_width = store.state.sidebar_width
        self._configure_webengine()
        self._build_ui()
        self.apply_theme()
        self.populate_tools()
        self.setWindowTitle("میزکار ابزارهای HTML | HTMLToolDesk")
        self.resize(1300, 820)
        self.setMinimumSize(840, 520)
        self.splitter.setSizes([980, store.state.sidebar_width])
        QShortcut(QKeySequence("Ctrl+N"), self, self.add_tool)
        QShortcut(QKeySequence("Ctrl+F"), self, self.focus_search)
        QShortcut(QKeySequence("F5"), self, self.reload_current)
        if store.warning:
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, "بازیابی تنظیمات", store.warning))

    def _configure_webengine(self) -> None:
        """Named profile and explicit paths make localStorage persistent across runs."""
        storage_root = user_data_directory()
        (storage_root / "web_profile").mkdir(parents=True, exist_ok=True)
        (storage_root / "web_cache").mkdir(parents=True, exist_ok=True)
        self.profile = QWebEngineProfile("HTMLToolDesk", self)
        self.profile.setPersistentStoragePath(str(storage_root / "web_profile"))
        self.profile.setCachePath(str(storage_root / "web_cache"))
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )
        settings = self.profile.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        # Remote URLs accessed directly from local HTML may be needed for external CDNs.
        # Add only files you trust, as they may execute JavaScript with local file access.
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.profile.downloadRequested.connect(self.handle_download)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("AppRoot")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        # Force viewport on the left and the sidebar on the right, independently of RTL.
        self.splitter.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.splitter.setHandleWidth(5)
        outer.addWidget(self.splitter)

        self.main_area = QWidget()
        self.main_area.setObjectName("MainArea")
        viewport_layout = QVBoxLayout(self.main_area)
        viewport_layout.setContentsMargins(18, 18, 15, 18)
        viewport_layout.setSpacing(15)

        toolbar = QWidget()
        toolbar.setObjectName("TopBar")
        top_layout = QHBoxLayout(toolbar)
        top_layout.setContentsMargins(13, 9, 13, 9)
        top_layout.setSpacing(8)
        top_layout.setDirection(QHBoxLayout.Direction.RightToLeft)

        self.sidebar_toggle = self._button("☰", "جمع/باز کردن منوی ابزارها", self.toggle_sidebar)
        top_layout.addWidget(self.sidebar_toggle)
        self.viewport_title = QLabel("صفحه اصلی")
        self.viewport_title.setObjectName("SectionTitle")
        self.viewport_title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(self.viewport_title, 1)
        self.reload_button = self._button("↻", "بارگذاری مجدد (F5)", self.reload_current)
        self.open_button = self._button("↗", "باز کردن در مرورگر ویندوز", self.open_external)
        self.theme_button = self._button("☀", "تغییر تم روشن/تاریک", self.toggle_theme)
        for button in (self.reload_button, self.open_button, self.theme_button):
            top_layout.addWidget(button)
        viewport_layout.addWidget(toolbar)

        self.stack = QStackedWidget()
        self.welcome = WelcomePanel()
        self.browser = QWebEngineView()
        self.page = QWebEnginePage(self.profile, self.browser)
        self.browser.setPage(self.page)
        self.browser.loadFinished.connect(self.on_load_finished)
        self.page.newWindowRequested.connect(self.handle_new_window)
        self.stack.addWidget(self.welcome)
        self.stack.addWidget(self.browser)
        viewport_layout.addWidget(self.stack, stretch=1)
        self.splitter.addWidget(self.main_area)

        self.sidebar = QWidget()
        self.sidebar.setObjectName("SideBar")
        self.sidebar.setMinimumWidth(235)
        self.sidebar.setMaximumWidth(540)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(16, 23, 16, 21)
        side_layout.setSpacing(13)
        side_layout.setDirection(QVBoxLayout.Direction.TopToBottom)

        brand = QLabel("✦  میزکار ابزارها")
        brand.setObjectName("AppTitle")
        brand.setAlignment(Qt.AlignmentFlag.AlignRight)
        side_layout.addWidget(brand)
        note = QLabel("فایل‌های HTML شما، در یک مکان")
        note.setObjectName("MutedText")
        note.setAlignment(Qt.AlignmentFlag.AlignRight)
        side_layout.addWidget(note)

        self.search = QLineEdit()
        self.search.setPlaceholderText("⌕  جستجو در عنوان ابزارها…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.populate_tools)
        side_layout.addSpacing(8)
        side_layout.addWidget(self.search)

        self.list_widget = QListWidget()
        self.list_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.list_widget.setSpacing(2)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.open_item_menu)
        self.list_widget.itemClicked.connect(self.activate_item)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.model().rowsMoved.connect(self.on_rows_moved)
        side_layout.addWidget(self.list_widget, stretch=1)

        self.count = QLabel("")
        self.count.setObjectName("MutedText")
        self.count.setAlignment(Qt.AlignmentFlag.AlignRight)
        side_layout.addWidget(self.count)

        add = QPushButton("＋  افزودن ابزار جدید")
        add.setObjectName("PrimaryButton")
        add.setMinimumHeight(47)
        add.clicked.connect(self.add_tool)
        side_layout.addWidget(add)
        helper = QLabel("برای مدیریت، روی هر ابزار راست‌کلیک کنید.\nبرای تغییر ترتیب، ابزارها را بکشید.")
        helper.setObjectName("MutedText")
        helper.setAlignment(Qt.AlignmentFlag.AlignCenter)
        helper.setWordWrap(True)
        side_layout.addWidget(helper)

        self.splitter.addWidget(self.sidebar)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self._update_view_buttons()

    def _button(self, label: str, tooltip: str, handler) -> QToolButton:
        button = QToolButton()
        button.setText(label)
        button.setToolTip(tooltip)
        button.setMinimumSize(40, 38)
        button.clicked.connect(handler)
        return button

    def _update_view_buttons(self) -> None:
        usable = bool(self.active_path and Path(self.active_path).is_file())
        self.reload_button.setEnabled(usable)
        self.open_button.setEnabled(usable)

    def apply_theme(self) -> None:
        QApplication.instance().setStyleSheet(stylesheet(self.store.state.theme))
        self.theme_button.setText("☀" if self.store.state.theme == "dark" else "☾")

    def focus_search(self) -> None:
        if not self.sidebar.isVisible():
            self.toggle_sidebar()
        self.search.setFocus()
        self.search.selectAll()

    def toggle_theme(self) -> None:
        theme = "light" if self.store.state.theme == "dark" else "dark"
        try:
            self.store.set_theme(theme)
            self.apply_theme()
        except OSError as exc:
            self.storage_error(exc)

    def toggle_sidebar(self) -> None:
        if self.sidebar.isVisible():
            self._last_sidebar_width = max(240, self.sidebar.width())
            self.sidebar.hide()
        else:
            self.sidebar.show()
            width = self._last_sidebar_width
            self.splitter.setSizes([max(500, self.splitter.width() - width), width])

    def populate_tools(self, *_args) -> None:
        self._rebuilding = True
        try:
            self.list_widget.clear()
            query = self.search.text() if hasattr(self, "search") else ""
            visible = [item for item in self.store.state.items if item.matches(query)]
            for tool in visible:
                entry = QListWidgetItem(tool.title)
                entry.setData(ROLE_ID, tool.id)
                entry.setToolTip(tool.description or "برای ویرایش یا حذف، راست‌کلیک کنید")
                entry.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.list_widget.addItem(entry)
                if tool.id == self.active_id:
                    self.list_widget.setCurrentItem(entry)
            count = len(self.store.state.items)
            self.count.setText(f"{len(visible)} ابزار از {count} مورد" if query else f"تعداد ابزارها: {count}")
            self.list_widget.setDragDropMode(
                QAbstractItemView.DragDropMode.NoDragDrop if query
                else QAbstractItemView.DragDropMode.InternalMove
            )
        finally:
            self._rebuilding = False

    def find_tool(self, tool_id: str | None) -> Tool | None:
        return next((item for item in self.store.state.items if item.id == tool_id), None)

    def activate_item(self, entry: QListWidgetItem) -> None:
        tool = self.find_tool(entry.data(ROLE_ID))
        if tool:
            self.show_tool(tool)

    def show_tool(self, tool: Tool) -> None:
        self.active_id = tool.id
        self.active_path = tool.path
        self.viewport_title.setText(tool.title)
        self._update_view_buttons()
        if not Path(tool.path).is_file():
            self.welcome.show_error(tool.path)
            self.stack.setCurrentWidget(self.welcome)
            QMessageBox.warning(self, "فایل پیدا نشد", "فایل HTML مربوط به این ابزار در مسیر ثبت‌شده پیدا نشد.\nاز منوی راست‌کلیک، مسیر آن را اصلاح کنید.")
            return
        self.stack.setCurrentWidget(self.browser)
        self.browser.load(QUrl.fromLocalFile(str(Path(tool.path).resolve())))

    def clear_selection(self) -> None:
        self.active_id = None
        self.active_path = None
        self.viewport_title.setText("صفحه اصلی")
        self.welcome.show_welcome()
        self.stack.setCurrentWidget(self.welcome)
        self.list_widget.clearSelection()
        self._update_view_buttons()
        self.browser.setUrl(QUrl("about:blank"))

    def add_tool(self) -> None:
        dialog = ToolDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        tool = dialog.get_tool()
        try:
            self.store.with_items(self.store.state.items + [tool])
        except OSError as exc:
            self.storage_error(exc)
            return
        self.search.clear()
        self.populate_tools()
        self.show_tool(tool)
        self.select_active_item()

    def select_active_item(self) -> None:
        for index in range(self.list_widget.count()):
            entry = self.list_widget.item(index)
            if entry.data(ROLE_ID) == self.active_id:
                self.list_widget.setCurrentItem(entry)
                return

    def edit_tool(self, tool_id: str) -> None:
        current = self.find_tool(tool_id)
        if current is None:
            return
        dialog = ToolDialog(self, current)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        changed = dialog.get_tool()
        try:
            self.store.with_items([changed if item.id == tool_id else item for item in self.store.state.items])
        except OSError as exc:
            self.storage_error(exc)
            return
        self.populate_tools()
        if self.active_id == tool_id:
            self.show_tool(changed)

    def delete_tool(self, tool_id: str) -> None:
        item = self.find_tool(tool_id)
        if not item:
            return
        choice = QMessageBox.question(
            self, "حذف ابزار", f"«{item.title}» از فهرست حذف شود؟\nفایل اصلی HTML از رایانه پاک نخواهد شد.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        try:
            self.store.with_items([tool for tool in self.store.state.items if tool.id != tool_id])
        except OSError as exc:
            self.storage_error(exc)
            return
        if self.active_id == tool_id:
            self.clear_selection()
        self.populate_tools()

    def move_item(self, tool_id: str, offset: int) -> None:
        items = list(self.store.state.items)
        current = next((i for i, entry in enumerate(items) if entry.id == tool_id), -1)
        target = current + offset
        if current < 0 or not 0 <= target < len(items):
            return
        items[current], items[target] = items[target], items[current]
        try:
            self.store.with_items(items)
        except OSError as exc:
            self.storage_error(exc)
            return
        self.populate_tools()

    def open_item_menu(self, position) -> None:
        entry = self.list_widget.itemAt(position)
        if entry is None:
            return
        tool_id = entry.data(ROLE_ID)
        menu = QMenu(self)
        edit = menu.addAction("✎  ویرایش عنوان، توضیح یا مسیر")
        delete = menu.addAction("✕  حذف از فهرست")
        menu.addSeparator()
        up = menu.addAction("↑  انتقال به بالا")
        down = menu.addAction("↓  انتقال به پایین")
        tools = self.store.state.items
        index = next((i for i, item in enumerate(tools) if item.id == tool_id), -1)
        up.setEnabled(index > 0)
        down.setEnabled(0 <= index < len(tools) - 1)
        choice = menu.exec(self.list_widget.mapToGlobal(position))
        if choice == edit:
            self.edit_tool(tool_id)
        elif choice == delete:
            self.delete_tool(tool_id)
        elif choice == up:
            self.move_item(tool_id, -1)
        elif choice == down:
            self.move_item(tool_id, +1)

    def on_rows_moved(self, *_args) -> None:
        # Delay until the Qt model has completed its internal drag/drop update.
        if not self._rebuilding:
            QTimer.singleShot(0, self.persist_drag_order)

    def persist_drag_order(self) -> None:
        if self.search.text() or self._rebuilding:
            return
        ids = [self.list_widget.item(i).data(ROLE_ID) for i in range(self.list_widget.count())]
        existing = {item.id: item for item in self.store.state.items}
        if len(ids) != len(existing) or set(ids) != set(existing):
            return
        try:
            self.store.with_items([existing[item_id] for item_id in ids])
        except OSError as exc:
            self.storage_error(exc)
            self.populate_tools()

    def reload_current(self) -> None:
        if not self.active_id:
            return
        tool = self.find_tool(self.active_id)
        if tool is None:
            return
        if not Path(tool.path).is_file():
            self.show_tool(tool)
        else:
            self.stack.setCurrentWidget(self.browser)
            # Re-load original file even if the page navigated to another URL.
            self.browser.load(QUrl.fromLocalFile(tool.path))

    def open_external(self) -> None:
        if self.active_path and Path(self.active_path).is_file():
            ok = QDesktopServices.openUrl(QUrl.fromLocalFile(self.active_path))
            if not ok:
                QMessageBox.warning(self, "باز کردن مرورگر", "سیستم نتوانست مرورگر پیش‌فرض را باز کند.")

    def on_load_finished(self, ok: bool) -> None:
        if not ok and self.stack.currentWidget() == self.browser:
            self.welcome.show_error("نمایش این صفحه با خطا روبه‌رو شد. فایل و منابع وابسته به آن را بررسی کنید.")
            self.stack.setCurrentWidget(self.welcome)

    def handle_new_window(self, request) -> None:
        # target="_blank" links open in the user's default browser.
        if request.requestedUrl().isValid():
            QDesktopServices.openUrl(request.requestedUrl())

    def handle_download(self, download) -> None:
        suggested = download.downloadFileName()
        path, _ = QFileDialog.getSaveFileName(self, "ذخیره فایل", str(Path.home() / "Downloads" / suggested))
        if not path:
            download.cancel()
            return
        dest = Path(path)
        download.setDownloadDirectory(str(dest.parent))
        download.setDownloadFileName(dest.name)
        download.accept()

    def storage_error(self, exc: Exception) -> None:
        QMessageBox.critical(self, "خطای ذخیره‌سازی", f"ذخیره اطلاعات انجام نشد.\nلطفاً مجوز نوشتن روی پوشه تنظیمات را بررسی کنید.\n\n{exc}")

    def closeEvent(self, event) -> None:
        if self.sidebar.isVisible():
            self._last_sidebar_width = self.sidebar.width()
        try:
            self.store.set_sidebar_width(self._last_sidebar_width)
        except OSError:
            pass  # Existing saved configuration remains safe due to atomic writes.
        super().closeEvent(event)