"""主窗口：无边框外壳、自绘标题栏、侧栏导航与页面容器。"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, QRect, QRectF, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPen, QShortcut
from PySide6.QtWidgets import (
    QAbstractButton, QApplication, QGraphicsDropShadowEffect, QHBoxLayout, QStackedWidget,
    QVBoxLayout, QWidget,
)

from . import icons, theme, widgets
from .pages.base import Ctx, hbox, vbox, wrap
from .pages.dashboard import Dashboard
from .pages.library import Library
from .pages.quiz import Quiz
from .pages.settings import Settings
from .pages.stats import Stats
from .pages.study import Study
from .theme import Theme, font

NAV_ITEMS = [
    ("today", "今日", "today"),
    ("study", "学习", "study"),
    ("quiz", "测验", "quiz"),
    ("library", "词库", "library"),
    ("stats", "统计", "stats"),
]


class WinButton(QAbstractButton):
    def __init__(self, icon: str, danger: bool = False, parent=None):
        super().__init__(parent)
        self._icon = icon
        self._danger = danger
        self._hover = 0.0
        self.setFixedSize(34, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(theme.DUR_FAST)
        self._anim.valueChanged.connect(self._on_hover)

    def set_icon(self, icon: str) -> None:
        self._icon = icon
        self.update()

    def _on_hover(self, v) -> None:
        self._hover = float(v)
        self.update()

    def enterEvent(self, e) -> None:
        self._anim.stop(); self._anim.setStartValue(self._hover); self._anim.setEndValue(1.0); self._anim.start()
        super().enterEvent(e)

    def leaveEvent(self, e) -> None:
        self._anim.stop(); self._anim.setStartValue(self._hover); self._anim.setEndValue(0.0); self._anim.start()
        super().leaveEvent(e)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if self._hover > 0:
            fill = Theme.color("accent") if self._danger else Theme.color("sunken")
            fill.setAlphaF(min(1.0, self._hover))
            widgets.rounded(p, QRectF(self.rect()).adjusted(1, 3, -1, -3), 8, fill)
        if self._danger and self._hover > 0.4:
            color = QColor("#FFFFFF")
        else:
            color = Theme.color("slate") if not self._danger else Theme.color("slate")
        icons.paint(p, self._icon, QRectF(10, 8, 14, 14), color, 1.5)
        p.end()


class TitleBar(QWidget):
    def __init__(self, window: "MainWindow", parent=None):
        super().__init__(parent)
        self.window_ = window
        self.setFixedHeight(theme.TITLEBAR_H)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 0, 12, 0)
        lay.setSpacing(6)

        mark = widgets.ThemedLabel("PALABRA", theme.EYEBROW, theme.W_SEMI, "mist", tracking=3.2)
        lay.addWidget(mark)
        lay.addStretch(1)

        self.theme_btn = WinButton("moon")
        self.theme_btn.setToolTip("切换深浅外观")
        self.theme_btn.clicked.connect(window.toggle_theme)
        lay.addWidget(self.theme_btn)

        spacer = QWidget()
        spacer.setFixedWidth(10)
        lay.addWidget(spacer)

        self.min_btn = WinButton("minimize")
        self.min_btn.setToolTip("最小化")
        self.min_btn.clicked.connect(window.showMinimized)
        self.max_btn = WinButton("maximize")
        self.max_btn.setToolTip("最大化")
        self.max_btn.clicked.connect(window.toggle_max)
        self.close_btn = WinButton("close", danger=True)
        self.close_btn.setToolTip("关闭")
        self.close_btn.clicked.connect(window.close)
        for b in (self.min_btn, self.max_btn, self.close_btn):
            lay.addWidget(b)

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self.window_.start_drag(e.globalPosition().toPoint())
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e) -> None:
        self.window_.drag_to(e.globalPosition().toPoint())
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e) -> None:
        self.window_.end_drag()
        super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e) -> None:
        self.window_.toggle_max()
        super().mouseDoubleClickEvent(e)


class Sidebar(QWidget):
    def __init__(self, window: "MainWindow", parent=None):
        super().__init__(parent)
        self.window_ = window
        self.setFixedWidth(theme.SIDEBAR_W)
        self.items: dict[str, widgets.NavItem] = {}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 22, 18, 18)
        lay.setSpacing(2)

        brand = hbox(0)
        brand.addWidget(widgets.ThemedLabel("Palabra", 22, theme.W_SEMI, "ink", tracking=-0.5))
        brand.addWidget(widgets.ThemedLabel(".", 22, theme.W_SEMI, "accent", tracking=-0.5))
        brand.addStretch(1)
        lay.addWidget(wrap(brand))
        lay.addSpacing(2)
        lay.addWidget(widgets.caption("西班牙语 · 记忆训练", "mist"))
        lay.addSpacing(26)

        for key, label, icon in NAV_ITEMS:
            item = widgets.NavItem(key, label, icon)
            item.clicked.connect(lambda _=False, k=key: window.navigate(k))
            self.items[key] = item
            lay.addWidget(item)

        lay.addStretch(1)

        self.settings_item = widgets.NavItem("settings", "设置", "settings")
        self.settings_item.clicked.connect(lambda: window.navigate("settings"))
        self.items["settings"] = self.settings_item
        lay.addWidget(self.settings_item)
        lay.addSpacing(10)
        self.hint = widgets.caption("Ctrl 1–5 切换页面", "mist")
        lay.addWidget(self.hint)

    def set_active(self, key: str) -> None:
        for k, item in self.items.items():
            item.set_selected(k == key)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), Theme.color("surface"))
        p.setPen(QPen(Theme.color("hairline"), 1))
        p.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
        p.end()


class Shell(QWidget):
    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        widgets.rounded(p, r, theme.R_SHELL, Theme.color("canvas"), Theme.color("hairline"))
        p.end()


class MainWindow(QWidget):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.setWindowTitle("Palabra · 背西班牙语单词")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(1080, 720)
        self.resize(1320, 860)

        self._drag_offset: QPoint | None = None
        self._nav_shortcuts: list[QShortcut] = []
        self._resize_edge: str | None = None
        self._resize_start = QRect()
        self._resize_origin = QPoint()
        self._maximized = False
        self._normal_geom = QRect()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(0)

        self.shell = Shell()
        shadow = QGraphicsDropShadowEffect(self.shell)
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 14)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.shell.setGraphicsEffect(shadow)
        outer.addWidget(self.shell)

        shell_lay = QVBoxLayout(self.shell)
        shell_lay.setContentsMargins(0, 0, 0, 0)
        shell_lay.setSpacing(0)

        self.titlebar = TitleBar(self)
        shell_lay.addWidget(self.titlebar)

        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)
        self.sidebar = Sidebar(self)
        body_lay.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        body_lay.addWidget(self.stack, 1)
        shell_lay.addWidget(body, 1)

        self.ctx = Ctx(store, self.navigate, self.toast, self.toggle_theme)
        self.pages = {
            "today": Dashboard(self.ctx),
            "study": Study(self.ctx),
            "quiz": Quiz(self.ctx),
            "library": Library(self.ctx),
            "stats": Stats(self.ctx),
            "settings": Settings(self.ctx),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

        self.toast_widget = widgets.Toast(self.shell)
        self.shell.installEventFilter(self)

        self._install_shortcuts()
        Theme.mode = "dark" if store.settings.get("theme") == "dark" else "light"
        self.titlebar.theme_btn.set_icon("sun" if Theme.mode == "dark" else "moon")
        self.navigate("today")

    # ------------------------------------------------------------ 导航

    def navigate(self, key: str) -> None:
        page = self.pages.get(key)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        self.sidebar.set_active(key)
        for other in self.pages.values():
            if other is not page:
                other.set_active(False)
        page.set_active(True)
        page.scroll_to_top()
        page.on_show()

    def toast(self, text: str) -> None:
        self.toast_widget.show_message(text)

    def _install_shortcuts(self) -> None:
        for i, key in enumerate(["today", "study", "quiz", "library", "stats"], start=1):
            sc = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
            sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
            sc.activated.connect(lambda k=key: self.navigate(k))
            self._nav_shortcuts.append(sc)
        sc = QShortcut(QKeySequence("Ctrl+,"), self)
        sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        sc.activated.connect(lambda: self.navigate("settings"))
        self._nav_shortcuts.append(sc)
        sc = QShortcut(QKeySequence("Ctrl+K"), self)
        sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        sc.activated.connect(self._focus_search)
        self._nav_shortcuts.append(sc)

    def _focus_search(self) -> None:
        self.navigate("library")
        page = self.pages["library"]
        page.search.setFocus()
        page.search.selectAll()

    # ------------------------------------------------------------ 主题

    def toggle_theme(self) -> None:
        theme.Theme.toggle()
        self.store.set_setting("theme", Theme.mode)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.qss())
        self.titlebar.theme_btn.set_icon("sun" if Theme.mode == "dark" else "moon")
        for w in self.findChildren(QWidget):
            w.update()
        self.update()
        self.toast("深色外观" if Theme.mode == "dark" else "浅色外观")

    # ------------------------------------------------------------ 窗口尺寸

    def start_drag(self, pos: QPoint) -> None:
        if self.isMaximized() or self._maximized:
            return
        self._drag_offset = pos - self.frameGeometry().topLeft()

    def drag_to(self, pos: QPoint) -> None:
        if self._drag_offset is not None and not self._maximized:
            self.move(pos - self._drag_offset)

    def end_drag(self) -> None:
        self._drag_offset = None

    def toggle_max(self) -> None:
        if self._maximized:
            self.showNormal()
            if not self._normal_geom.isNull():
                self.setGeometry(self._normal_geom)
            self._maximized = False
            self.titlebar.max_btn.set_icon("maximize")
        else:
            self._normal_geom = self.geometry()
            self.showMaximized()
            self._maximized = True
            self.titlebar.max_btn.set_icon("restore")

    def _edge_at(self, pos: QPoint) -> str | None:
        m = 14
        x, y = pos.x(), pos.y()
        if self._maximized:
            return None
        left, right = x < m, x > self.width() - m
        top, bottom = y < m, y > self.height() - m
        if top and left:
            return "tl"
        if top and right:
            return "tr"
        if bottom and left:
            return "bl"
        if bottom and right:
            return "br"
        if left:
            return "l"
        if right:
            return "r"
        if top:
            return "t"
        if bottom:
            return "b"
        return None

    CURSORS = {
        "l": Qt.CursorShape.SizeHorCursor, "r": Qt.CursorShape.SizeHorCursor,
        "t": Qt.CursorShape.SizeVerCursor, "b": Qt.CursorShape.SizeVerCursor,
        "tl": Qt.CursorShape.SizeFDiagCursor, "br": Qt.CursorShape.SizeFDiagCursor,
        "tr": Qt.CursorShape.SizeBDiagCursor, "bl": Qt.CursorShape.SizeBDiagCursor,
    }

    def mousePressEvent(self, e) -> None:
        edge = self._edge_at(e.position().toPoint())
        if edge and e.button() == Qt.MouseButton.LeftButton:
            self._resize_edge = edge
            self._resize_start = self.geometry()
            self._resize_origin = e.globalPosition().toPoint()
            e.accept()
            return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e) -> None:
        if self._resize_edge:
            delta = e.globalPosition().toPoint() - self._resize_origin
            g = QRect(self._resize_start)
            if "l" in self._resize_edge:
                g.setLeft(g.left() + delta.x())
            if "r" in self._resize_edge:
                g.setRight(g.right() + delta.x())
            if "t" in self._resize_edge:
                g.setTop(g.top() + delta.y())
            if "b" in self._resize_edge:
                g.setBottom(g.bottom() + delta.y())
            if g.width() >= self.minimumWidth() and g.height() >= self.minimumHeight():
                self.setGeometry(g)
            e.accept()
            return
        edge = self._edge_at(e.position().toPoint())
        self.setCursor(self.CURSORS.get(edge, Qt.CursorShape.ArrowCursor) if edge else Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e) -> None:
        self._resize_edge = None
        super().mouseReleaseEvent(e)

    def eventFilter(self, obj, event):
        if obj is self.shell and event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            self.toast_widget.relocate()
        return super().eventFilter(obj, event)

    def closeEvent(self, e) -> None:
        self.store.save()
        super().closeEvent(e)