"""Modern RTL desktop UI with a resizable right sidebar and Chromium viewport."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QUrl, QTimer, QSize
from PyQt6.QtGui import QDesktopServices, QKeySequence, QShortcut
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
from .icons import icon, tool_icon
from .jalali import format_jalali_date, persian_digits
from .tool_cards import ToolCardDelegate
from .web_state import CAPTURE_SCRIPT, read_snapshot, restore_script, save_snapshot

ROLE_ID = Qt.ItemDataRole.UserRole


class WelcomePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        body = QVBoxLayout(self)
        body.setContentsMargins(28, 28, 28, 28)
        body.addStretch(1)

        card = QWidget()
        card.setObjectName("WelcomeCard")
        card.setMaximumWidth(530)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 32, 30, 32)
        layout.setSpacing(11)

        emblem = QLabel()
        emblem.setPixmap(icon("grid", "#626EFF", 32).pixmap(32, 32))
        emblem.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(emblem)
        logo = QLabel("HTML  /  TOOL DESK")
        logo.setObjectName("BrandCaption")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        self.title = QLabel("ابزارهای شما آماده‌اند")
        self.title.setObjectName("WelcomeTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setWordWrap(True)
        layout.addWidget(self.title)

        self.arrow = QLabel("↗")
        self.arrow.setObjectName("WelcomeArrow")
        self.arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.arrow)

        self.message = QLabel("روی ابزار موردنظر در ستون سمت راست کلیک کنید")
        
        self.message.setObjectName("MutedText")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        body.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        body.addStretch(1)

    def show_welcome(self) -> None:
        self.title.setText("ابزارهای شما آماده‌اند")
        self.arrow.show()
        self.message.setText("روی ابزار موردنظر در ستون سمت راست کلیک کنید")

    def show_error(self, path: str) -> None:
        self.title.setText("فایل HTML در دسترس نیست")
        self.arrow.hide()
        self.message.setText("فایل اصلی جابه‌جا یا حذف شده است.\nاز منوی ابزار، گزینهٔ «ویرایش» را انتخاب و مسیر جدید را ثبت کنید.\n\n" + path)


class MainWindow(QMainWindow):
    def __init__(self, store: Store):
        super().__init__()
        self.store = store
        self.active_id: str | None = None
        self.active_path: str | None = None
        self._rebuilding = False
        self._last_sidebar_width = store.state.sidebar_width
        self.browser = None
        self.profile = None
        self.page = None
        self._loaded_tool_path = None
        self._view_cache = {}  # tool id -> live QWebEngineView (bounded)
        self._view_paths = {}  # tool id -> last loaded HTML path
        self._view_order = []  # least recently selected first
        self._standby_browser = None
        self._max_cached_tools = 2
        self._is_finishing_close = False
        self._snapshot_pending_close = False
        self._zoom_by_tool: dict[str, float] = {}
        self._build_ui()
        self.apply_theme()
        self.populate_tools()
        self.setWindowTitle("میزکار ابزارهای HTML | HTMLToolDesk")
        self.resize(1320, 790)
        self.setMinimumSize(840, 520)
        self.splitter.setSizes([1050, min(store.state.sidebar_width, 256)])
        QShortcut(QKeySequence("Ctrl+N"), self, self.add_tool)
        QShortcut(QKeySequence("Ctrl+F"), self, self.focus_search)
        QShortcut(QKeySequence("F5"), self, self.reload_current)
        QShortcut(QKeySequence("Ctrl+="), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl++"), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.zoom_reset)
        # The local date may change while the app stays open overnight.
        self.date_timer = QTimer(self)
        self.date_timer.setInterval(60_000)
        self.date_timer.timeout.connect(self.refresh_shamsi_date)
        self.date_timer.start()
        # No Chromium work on startup: the welcome screen must never freeze.
        self.snapshot_timer = QTimer(self)
        self.snapshot_timer.setInterval(1800)
        self.snapshot_timer.timeout.connect(self.capture_active_storage)
        self.snapshot_timer.start()
        if store.warning:
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, "بازیابی تنظیمات", store.warning))

    def _ensure_browser(self) -> None:
        """Create one persistent Chromium profile and warm an invisible first view."""
        if self.profile is not None:
            return

        from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings

        storage_root = user_data_directory()
        (storage_root / "web_profile").mkdir(parents=True, exist_ok=True)
        (storage_root / "web_cache").mkdir(parents=True, exist_ok=True)
        profile = QWebEngineProfile("HTMLToolDesk", self)
        profile.setPersistentStoragePath(str(storage_root / "web_profile"))
        profile.setCachePath(str(storage_root / "web_cache"))
        profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )
        settings = profile.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        profile.downloadRequested.connect(self.handle_download)
        self.profile = profile
        # Avoid spawning Chromium or loading blank pages until a user picks a tool.

    def _new_web_view(self):
        """Create one isolated page sharing the same disk cache and LocalStorage."""
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtWebEngineCore import QWebEnginePage

        view = QWebEngineView(self.stack)
        page = QWebEnginePage(self.profile, view)
        view.setPage(page)
        view.loadStarted.connect(self.on_load_started)
        view.loadFinished.connect(self.on_load_finished)
        page.newWindowRequested.connect(
            lambda request, owner=view: self.handle_new_window(request, owner)
        )
        return view

    def _install_restore_script(self, tool_id: str, path: str, view) -> None:
        """Restore native snapshots before the HTML's own initialization JS runs."""
        from PyQt6.QtWebEngineCore import QWebEngineScript

        snapshot = read_snapshot(tool_id, path)
        collection = view.page().scripts()
        collection.clear()
        if not snapshot:
            return
        script = QWebEngineScript()
        script.setName("HTMLToolDeskStorageRecovery")
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(False)
        script.setSourceCode(restore_script(snapshot))
        collection.insert(script)

    def _capture_view_storage(self, tool_id: str, view, finished=None) -> None:
        """Request a small, asynchronous snapshot; never block Qt's GUI event loop."""
        path = self._view_paths.get(tool_id)
        try:
            if not path or not hasattr(view, "page"):
                if finished:
                    finished()
                return
            page = view.page()
            url = page.url()
            if not url.isLocalFile() or Path(url.toLocalFile()).resolve() != Path(path).resolve():
                if finished:
                    finished()
                return

            def received(data):
                try:
                    save_snapshot(tool_id, path, data)
                finally:
                    if finished:
                        finished()

            page.runJavaScript(CAPTURE_SCRIPT, received)
        except (RuntimeError, AttributeError, OSError):
            if finished:
                finished()

    def capture_active_storage(self) -> None:
        """Periodic crash-resistant mirror of local/session storage after HTML changes."""
        if self.active_id and self.active_id in self._view_cache:
            self._capture_view_storage(self.active_id, self._view_cache[self.active_id])

    def _forget_view(self, tool_id: str) -> None:
        """Release an inactive cached page while retaining data on disk."""
        view = self._view_cache.pop(tool_id, None)
        self._view_paths.pop(tool_id, None)
        if tool_id in self._view_order:
            self._view_order.remove(tool_id)
        if view is None:
            return
        if view is self.browser:
            self.browser = None
            self.page = None
        if self.stack.currentWidget() is view:
            self.stack.setCurrentWidget(self.welcome)
        view.stop()
        self.stack.removeWidget(view)
        view.deleteLater()

    def _get_view_for_tool(self, tool_id: str):
        """LRU cache: revisiting up to three tools does not reload HTML/JavaScript."""
        if tool_id in self._view_cache:
            self._view_order.remove(tool_id)
            self._view_order.append(tool_id)
            return self._view_cache[tool_id]

        if len(self._view_cache) >= self._max_cached_tools:
            self._forget_view(self._view_order[0])

        view = self._new_web_view()
        self.stack.addWidget(view)

        self._view_cache[tool_id] = view
        self._view_order.append(tool_id)
        return view

    def on_load_started(self) -> None:
        if self.sender() is not self.browser or self.stack.currentWidget() is not self.browser:
            return
        self.loading_label.setText("در حال بارگذاری…")
        self.loading_label.show()

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
        self.splitter.setHandleWidth(3)
        outer.addWidget(self.splitter)

        self.main_area = QWidget()
        self.main_area.setObjectName("MainArea")
        viewport_layout = QVBoxLayout(self.main_area)
        viewport_layout.setContentsMargins(11, 9, 11, 9)
        viewport_layout.setSpacing(7)

        toolbar = QWidget()
        toolbar.setObjectName("TopBar")
        top_layout = QHBoxLayout(toolbar)
        top_layout.setContentsMargins(10, 4, 10, 4)
        top_layout.setSpacing(5)
        top_layout.setDirection(QHBoxLayout.Direction.RightToLeft)

        self.sidebar_toggle = self._button("☰", "جمع/باز کردن منوی ابزارها", self.toggle_sidebar)
        top_layout.addWidget(self.sidebar_toggle)
        self.viewport_title = QLabel("صفحه اصلی")
        self.viewport_title.setObjectName("SectionTitle")
        self.viewport_title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(self.viewport_title, 1)
        self.date_label = QLabel()
        self.date_label.setObjectName("ShamsiDate")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setToolTip("تاریخ شمسی امروز مطابق ساعت سیستم")
        self.refresh_shamsi_date()
        top_layout.addWidget(self.date_label)
        top_layout.addSpacing(7)
        self.reload_button = self._button("↻", "بارگذاری مجدد (F5)", self.reload_current)
        self.open_button = self._button("↗", "باز کردن در مرورگر ویندوز", self.open_external)
        self.theme_button = self._button("☀", "تغییر تم روشن/تاریک", self.toggle_theme)
        self.loading_label = QLabel("در حال بارگذاری…")
        self.loading_label.setObjectName("MutedText")
        self.loading_label.hide()
        top_layout.addWidget(self.loading_label)
        for button in (self.reload_button, self.open_button, self.theme_button):
            top_layout.addWidget(button)
        top_layout.addSpacing(9)
        self.zoom_in_button = self._button("+", "بزرگ‌نمایی HTML (Ctrl++)", self.zoom_in)
        self.zoom_reset_button = self._button("۱۰۰٪", "بازگشت به زوم ۱۰۰٪ (Ctrl+0)", self.zoom_reset)
        self.zoom_reset_button.setFixedWidth(60)
        self.zoom_out_button = self._button("−", "کوچک‌نمایی HTML (Ctrl+-)", self.zoom_out)
        for button in (self.zoom_in_button, self.zoom_reset_button, self.zoom_out_button):
            top_layout.addWidget(button)
        viewport_layout.addWidget(toolbar)

        self.stack = QStackedWidget()
        self.welcome = WelcomePanel()
        self.stack.addWidget(self.welcome)
        viewport_layout.addWidget(self.stack, stretch=1)
        self.splitter.addWidget(self.main_area)

        self.sidebar = QWidget()
        self.sidebar.setObjectName("SideBar")
        self.sidebar.setMinimumWidth(210)
        self.sidebar.setMaximumWidth(345)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(12, 17, 12, 12)
        side_layout.setSpacing(8)
        side_layout.setDirection(QVBoxLayout.Direction.TopToBottom)

        brand_mark = QLabel("HTML  /  WORKSPACE")
        brand_mark.setObjectName("BrandCaption")
        brand_mark.setAlignment(Qt.AlignmentFlag.AlignRight)
        side_layout.addWidget(brand_mark)
        brand = QLabel("کتابخانه ابزارها")
        brand.setObjectName("AppTitle")
        brand.setAlignment(Qt.AlignmentFlag.AlignRight)
        side_layout.addWidget(brand)
        note = QLabel("دسترسی سریع به فایل‌های HTML")
        note.setObjectName("MutedText")
        note.setAlignment(Qt.AlignmentFlag.AlignRight)
        side_layout.addWidget(note)
        rule = QFrame()
        rule.setObjectName("SideRule")
        side_layout.addWidget(rule)

        self.search = QLineEdit()
        self.search.setPlaceholderText("جستجو بین ابزارهای ذخیره‌شده…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.populate_tools)
        side_layout.addSpacing(2)
        side_layout.addWidget(self.search)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("ToolList")
        self.list_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.list_widget.setIconSize(QSize(20, 20))
        self.list_widget.setUniformItemSizes(True)
        self.list_widget.setSpacing(1)
        self.tool_card_delegate = ToolCardDelegate(self.list_widget, self.store.state.theme == "dark")
        self.list_widget.setItemDelegate(self.tool_card_delegate)
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

        add = QPushButton("افزودن ابزار جدید")
        add.setObjectName("PrimaryButton")
        add.setIcon(icon("plus", "#FFFFFF", 18))
        add.setIconSize(QSize(18, 18))
        add.setMinimumHeight(41)
        add.clicked.connect(self.add_tool)
        side_layout.addWidget(add)
        helper = QLabel("راست‌کلیک: ویرایش، حذف یا مرتب‌سازی")
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
        icon_name = {"☰": "menu", "↻": "refresh", "↗": "external", "☀": "sun"}.get(label)
        if icon_name:
            button.setIcon(icon(icon_name, "#6B7D9A", 19))
            button.setIconSize(QSize(19, 19))
        else:
            button.setText(label)
        button.setObjectName("IconButton")
        button.setToolTip(tooltip)
        button.setFixedSize(34, 34)
        button.clicked.connect(handler)
        return button

    def _update_view_buttons(self) -> None:
        usable = bool(self.active_path and Path(self.active_path).is_file())
        self.reload_button.setEnabled(usable)
        self.open_button.setEnabled(usable)
        for control in (self.zoom_in_button, self.zoom_reset_button, self.zoom_out_button):
            control.setEnabled(usable)
        self.update_zoom_label()

    def apply_theme(self) -> None:
        QApplication.instance().setStyleSheet(stylesheet(self.store.state.theme))
        dark = self.store.state.theme == "dark"
        if hasattr(self, "tool_card_delegate"):
            self.tool_card_delegate.dark = dark
            self.list_widget.viewport().update()
        color = "#AEC0DB" if dark else "#53647D"
        for control, name in (
            (self.sidebar_toggle, "menu"),
            (self.reload_button, "refresh"),
            (self.open_button, "external"),
            (self.theme_button, "sun" if dark else "moon"),
        ):
            control.setIcon(icon(name, color, 19))
        self.populate_tools()

    def refresh_shamsi_date(self) -> None:
        """Use the user's local Windows calendar date; update after midnight."""
        self.date_label.setText(format_jalali_date())

    def update_zoom_label(self) -> None:
        factor = self._zoom_by_tool.get(self.active_id or "", 1.0)
        self.zoom_reset_button.setText(f"{persian_digits(round(factor * 100))}٪")

    def _set_zoom_for_active(self, factor: float) -> None:
        """Apply page zoom without reloading the HTML or changing other tools."""
        if not self.active_id:
            return
        view = self._view_cache.get(self.active_id)
        if view is None:
            return
        bounded = round(min(2.5, max(0.5, factor)), 2)
        self._zoom_by_tool[self.active_id] = bounded
        # Fake views used by GUI regression tests expose setZoomFactor too.
        view.setZoomFactor(bounded)
        self.update_zoom_label()

    def zoom_in(self) -> None:
        if self.active_id:
            factor = self._zoom_by_tool.get(self.active_id, 1.0)
            self._set_zoom_for_active(factor + 0.1)

    def zoom_out(self) -> None:
        if self.active_id:
            factor = self._zoom_by_tool.get(self.active_id, 1.0)
            self._set_zoom_for_active(factor - 0.1)

    def zoom_reset(self) -> None:
        self._set_zoom_for_active(1.0)

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
            self._last_sidebar_width = max(210, self.sidebar.width())
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
                entry.setIcon(tool_icon(tool.id, self.store.state.theme == "dark"))
                entry.setSizeHint(QSize(0, 54))
                entry.setData(ROLE_ID, tool.id)
                entry.setToolTip(tool.description or "برای ویرایش یا حذف، راست‌کلیک کنید")
                entry.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.list_widget.addItem(entry)
                if tool.id == self.active_id:
                    self.list_widget.setCurrentItem(entry)
            count = len(self.store.state.items)
            self.count.setText(f"{len(visible)} ابزار از {count} مورد" if query else f"{count} ابزار ذخیره‌شده")
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
        if self.active_id and self.active_id != tool.id:
            self.capture_active_storage()
        self.active_id = tool.id
        self.active_path = tool.path
        self.viewport_title.setText(tool.title)
        self._update_view_buttons()
        if not Path(tool.path).is_file():
            self.welcome.show_error(tool.path)
            self.stack.setCurrentWidget(self.welcome)
            QMessageBox.warning(
                self, "فایل پیدا نشد",
                "فایل HTML مربوط به این ابزار در مسیر ثبت‌شده پیدا نشد.\n"
                "از منوی راست‌کلیک، مسیر آن را اصلاح کنید."
            )
            return

        path = str(Path(tool.path).resolve())
        try:
            self._ensure_browser()
            view = self._get_view_for_tool(tool.id)
        except Exception as exc:
            self.welcome.show_error(str(exc))
            self.stack.setCurrentWidget(self.welcome)
            QMessageBox.critical(self, "خطای نمایش", f"نمایشگر HTML راه‌اندازی نشد:\n{exc}")
            return

        # Switching to an already-loaded page is immediate and keeps HTML state.
        self.browser = view
        self.page = view.page()
        self.stack.setCurrentWidget(view)
        self._set_zoom_for_active(self._zoom_by_tool.get(tool.id, 1.0))
        if self._view_paths.get(tool.id) == path:
            self.loading_label.hide()
            return

        self._view_paths[tool.id] = path
        self._loaded_tool_path = path
        self.loading_label.setText("در حال بارگذاری…")
        self.loading_label.show()
        self._install_restore_script(tool.id, path, view)
        view.load(QUrl.fromLocalFile(path))

    def clear_selection(self) -> None:
        self.active_id = None
        self.active_path = None
        self.viewport_title.setText("صفحه اصلی")
        self.welcome.show_welcome()
        self.stack.setCurrentWidget(self.welcome)
        self.list_widget.clearSelection()
        self._update_view_buttons()
        self.loading_label.hide()
        # Do not unload cached pages: revisit without another Chromium reload.

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
        self._forget_view(tool_id)
        self._zoom_by_tool.pop(tool_id, None)
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
        """Explicit refresh reloads the selected file; regular clicks do not."""
        if not self.active_id:
            return
        tool = self.find_tool(self.active_id)
        if tool is None:
            return
        if not Path(tool.path).is_file():
            self.show_tool(tool)
            return
        if self.active_id not in self._view_cache:
            self.show_tool(tool)
            return
        view = self._view_cache[self.active_id]
        self.browser, self.page = view, view.page()
        self.stack.setCurrentWidget(view)
        path = str(Path(tool.path).resolve())
        self._view_paths[self.active_id] = path
        self._install_restore_script(self.active_id, path, view)
        self.loading_label.setText("در حال بارگذاری مجدد…")
        self.loading_label.show()
        view.load(QUrl.fromLocalFile(path))

    def open_external(self) -> None:
        if self.active_path and Path(self.active_path).is_file():
            ok = QDesktopServices.openUrl(QUrl.fromLocalFile(self.active_path))
            if not ok:
                QMessageBox.warning(self, "باز کردن مرورگر", "سیستم نتوانست مرورگر پیش‌فرض را باز کند.")

    def on_load_finished(self, ok: bool) -> None:
        # Inactive cached HTML pages can finish after switching; never disturb UI.
        if self.sender() is not self.browser or self.stack.currentWidget() is not self.browser:
            return
        self.loading_label.hide()
        if ok and self.active_id:
            self.capture_active_storage()
        if not ok and self.active_id:
            self._view_paths.pop(self.active_id, None)
            self.loading_label.setText("بارگذاری ناموفق؛ دوباره تلاش کنید")
            self.loading_label.show()

    def handle_new_window(self, request, owner=None) -> None:
        """Use the originating viewport instead of opening an external window."""
        url = request.requestedUrl()
        target = owner if owner is not None else self.browser
        if target is not None and url.isValid() and url.scheme() in ("file", "http", "https"):
            target.load(url)

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