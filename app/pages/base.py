"""页面基类与通用布局工具。

页面统一放进滚动容器：内容不足一屏时自动撑满（保留大留白），
内容超出一屏时出现极细的悬浮滚动条，避免任何控件被压缩变形。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget,
)

from .. import theme, widgets
from ..store import Store


class Ctx:
    """页面与主窗口之间的唯一接口，避免页面直接操作窗口。"""

    def __init__(self, store: Store, navigate, toast, refresh_theme):
        self.store = store
        self.navigate = navigate
        self.toast = toast
        self.refresh_theme = refresh_theme


class Page(QWidget):
    key = "page"
    title = ""

    def __init__(self, ctx: Ctx, scroll: bool = True):
        super().__init__()
        self.ctx = ctx
        self.store = ctx.store
        self.scroll_area: QScrollArea | None = None

        if scroll:
            area = QScrollArea(self)
            area.setWidgetResizable(True)
            area.setFrameShape(QFrame.Shape.NoFrame)
            area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            area.setAutoFillBackground(False)
            area.viewport().setAutoFillBackground(False)
            area.setStyleSheet("QScrollArea{background:transparent;border:none;}")
            area.viewport().setStyleSheet("background:transparent;")
            area.setFocusPolicy(Qt.FocusPolicy.NoFocus)

            inner = QWidget()
            inner.setAutoFillBackground(False)
            self.root = QVBoxLayout(inner)
            self.root.setContentsMargins(theme.CONTENT_PAD, 34, theme.CONTENT_PAD - 10, 30)
            self.root.setSpacing(0)
            area.setWidget(inner)

            outer = QVBoxLayout(self)
            outer.setContentsMargins(0, 0, 0, 0)
            outer.setSpacing(0)
            outer.addWidget(area)
            self.scroll_area = area
            self.content = inner
        else:
            self.root = QVBoxLayout(self)
            self.root.setContentsMargins(theme.CONTENT_PAD, 34, theme.CONTENT_PAD, 30)
            self.root.setSpacing(0)
            self.content = self

    def on_show(self) -> None:  # 页面被切换到前台时刷新
        pass

    def on_theme(self) -> None:
        self.update()

    def set_active(self, active: bool) -> None:
        """页面级的键盘快捷键只在页面处于前台时生效。"""
        for shortcut in getattr(self, "shortcuts", []):
            shortcut.setEnabled(active)
        if active and self.key in ("study", "quiz"):
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setFocus(Qt.FocusReason.OtherFocusReason)

    def scroll_to_top(self) -> None:
        if self.scroll_area is not None:
            self.scroll_area.verticalScrollBar().setValue(0)


# ---------------------------------------------------------------- 布局工具

def vbox(spacing: int = 0, margins: tuple[int, int, int, int] = (0, 0, 0, 0)) -> QVBoxLayout:
    lay = QVBoxLayout()
    lay.setContentsMargins(*margins)
    lay.setSpacing(spacing)
    return lay


def hbox(spacing: int = 0, margins: tuple[int, int, int, int] = (0, 0, 0, 0)) -> QHBoxLayout:
    lay = QHBoxLayout()
    lay.setContentsMargins(*margins)
    lay.setSpacing(spacing)
    return lay


def wrap(layout) -> QWidget:
    w = QWidget()
    w.setLayout(layout)
    return w


def page_header(kicker: str, title: str, subtitle: str = "", right: QWidget | None = None) -> QWidget:
    """统一页头：眉标 → 标题 → 说明，右侧可放操作区。"""
    left = vbox(0)
    left.addWidget(widgets.eyebrow(kicker))
    left.addSpacing(12)
    left.addWidget(widgets.h1(title))
    if subtitle:
        left.addSpacing(9)
        left.addWidget(widgets.body(subtitle, "slate"))
    row = hbox(0)
    row.addLayout(left, 1)
    if right is not None:
        row.addWidget(right, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
    return wrap(row)


def section_title(title: str, subtitle: str = "", right: QWidget | None = None) -> QWidget:
    left = vbox(0)
    left.addWidget(widgets.h3(title))
    if subtitle:
        left.addSpacing(6)
        left.addWidget(widgets.caption(subtitle, "slate"))
    row = hbox(0)
    row.addLayout(left, 1)
    if right is not None:
        row.addWidget(right, 0, Qt.AlignmentFlag.AlignVCenter)
    return wrap(row)