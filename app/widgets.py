"""自绘控件库：按钮、卡片、分段控件、进度环、图表、翻卡、Toast。

全部使用 QPainter 绘制，保证在深浅两套主题下都能精确还原设计令牌，
并且不依赖系统控件的默认外观。
"""
from __future__ import annotations

import math

from PySide6.QtCore import (
    QAbstractAnimation, QEasingCurve, QPoint, QPointF, QPropertyAnimation,
    QRect, QRectF, QSize, Qt, QVariantAnimation, Signal,
)
from PySide6.QtGui import (
    QColor, QFontMetrics, QGuiApplication, QPainter, QPen, QRegion,
)
from PySide6.QtWidgets import (
    QAbstractButton, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QLineEdit,
    QSizePolicy, QVBoxLayout, QWidget,
)

from . import icons, theme
from .theme import Theme, font


# ---------------------------------------------------------------- 绘制工具

def rounded(p: QPainter, rect: QRectF, radius: float, fill: QColor | None,
            border: QColor | None = None, border_w: float = 1.0) -> None:
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    if fill is not None:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(fill)
        p.drawRoundedRect(rect, radius, radius)
    if border is not None:
        pen = QPen(border, border_w)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect.adjusted(border_w / 2, border_w / 2, -border_w / 2, -border_w / 2),
                          radius, radius)


def _flags(align: Qt.AlignmentFlag, wrap: bool) -> int:
    fl = int(align)
    if wrap:
        fl |= int(Qt.TextFlag.TextWordWrap)
    return fl


# ---------------------------------------------------------------- 排版文字

class ThemedLabel(QWidget):
    """随主题自动变色的文字控件，替代 QLabel，避免样式表散落各处。"""

    def __init__(self, text: str = "", size: int = theme.BODY, weight=theme.W_REGULAR,
                 color: str = "ink", align=Qt.AlignmentFlag.AlignLeft,
                 wrap: bool = False, tracking: float = 0.0, parent=None):
        super().__init__(parent)
        self._text = text
        self._size = size
        self._weight = weight
        self._color = color
        self._align = align
        self._wrap = wrap
        self._tracking = tracking
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        if wrap:
            sp = self.sizePolicy()
            sp.setHeightForWidth(True)
            sp.setVerticalPolicy(QSizePolicy.Policy.Preferred)
            self.setSizePolicy(sp)

    # -- 属性
    def text(self) -> str:
        return self._text

    def setText(self, value: str) -> None:
        self._text = value
        self.updateGeometry()
        self.update()

    def setColor(self, key: str) -> None:
        self._color = key
        self.update()

    def set_size(self, size: int) -> None:
        self._size = size
        self.updateGeometry()
        self.update()

    def qfont(self):
        return font(self._size, self._weight, self._tracking)

    # -- 布局
    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.qfont())
        if self._wrap:
            w = max(160, min(520, fm.horizontalAdvance(self._text) + 8))
            return QSize(w, self.heightForWidth(w))
        return QSize(fm.horizontalAdvance(self._text) + 4, fm.height() + 2)

    def minimumSizeHint(self) -> QSize:
        if self._wrap:
            return QSize(80, QFontMetrics(self.qfont()).height())
        return self.sizeHint()

    def hasHeightForWidth(self) -> bool:
        return self._wrap

    def heightForWidth(self, width: int) -> int:
        fm = QFontMetrics(self.qfont())
        br = fm.boundingRect(QRect(0, 0, max(1, width), 10000),
                             _flags(self._align, True), self._text)
        return br.height() + 2

    # -- 绘制
    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        p.setFont(self.qfont())
        p.setPen(Theme.color(self._color))
        p.drawText(self.rect(), _flags(self._align, self._wrap), self._text)
        p.end()


def h1(text: str, color: str = "ink", **kw) -> ThemedLabel:
    return ThemedLabel(text, theme.H1, theme.W_SEMI, color, tracking=-0.6, **kw)


def h2(text: str, color: str = "ink", **kw) -> ThemedLabel:
    return ThemedLabel(text, theme.H2, theme.W_SEMI, color, tracking=-0.3, **kw)


def h3(text: str, color: str = "ink", **kw) -> ThemedLabel:
    return ThemedLabel(text, theme.H3, theme.W_SEMI, color, tracking=-0.1, **kw)


def body(text: str, color: str = "ink2", **kw) -> ThemedLabel:
    return ThemedLabel(text, theme.BODY, theme.W_REGULAR, color, **kw)


def caption(text: str, color: str = "slate", **kw) -> ThemedLabel:
    return ThemedLabel(text, theme.CAPTION, theme.W_MEDIUM, color, tracking=0.2, **kw)


def eyebrow(text: str, color: str = "mist") -> ThemedLabel:
    return ThemedLabel(text.upper(), theme.EYEBROW, theme.W_SEMI, color, tracking=1.6)


# ---------------------------------------------------------------- 容器

class Card(QWidget):
    """基础纸面：圆角 + 1px 描边，无阴影。"""

    def __init__(self, radius: int = theme.R_CARD, fill: str = "surface",
                 border: str | None = "hairline", padding: int = 28, parent=None):
        super().__init__(parent)
        self._radius = radius
        self._fill = fill
        self._border = border
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(padding, padding, padding, padding)
        self.layout_.setSpacing(0)
        if radius >= 20:
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

    def body(self) -> QVBoxLayout:
        return self.layout_

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        rounded(p, QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), self._radius,
                Theme.color(self._fill),
                Theme.color(self._border) if self._border else None)
        p.end()


class Divider(QWidget):
    def __init__(self, vertical: bool = False, color: str = "hairline", parent=None):
        super().__init__(parent)
        self._vertical = vertical
        self._color = color
        if vertical:
            self.setFixedWidth(1)
        else:
            self.setFixedHeight(1)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), Theme.color(self._color))
        p.end()


class Chip(QWidget):
    """小标签：词性、等级、主题。"""

    def __init__(self, text: str, tone: str = "sunken", color: str = "slate", parent=None):
        super().__init__(parent)
        self._text = text
        self._tone = tone
        self._color = color
        fm = QFontMetrics(font(theme.EYEBROW, theme.W_SEMI, 0.6))
        self.setFixedHeight(22)
        self.setMinimumWidth(fm.horizontalAdvance(text) + 18)

    def setText(self, text: str) -> None:
        self._text = text
        fm = QFontMetrics(font(theme.EYEBROW, theme.W_SEMI, 0.6))
        self.setMinimumWidth(fm.horizontalAdvance(text) + 18)
        self.update()

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(font(theme.EYEBROW, theme.W_SEMI, 0.6))
        return QSize(fm.horizontalAdvance(self._text) + 18, 22)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        rounded(p, QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 7,
                Theme.color(self._tone))
        p.setFont(font(theme.EYEBROW, theme.W_SEMI, 0.6))
        p.setPen(Theme.color(self._color))
        p.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), self._text)
        p.end()


# ---------------------------------------------------------------- 按钮

class AnimButton(QAbstractButton):
    """四态按钮：default / hover / pressed / disabled，带 140ms 颜色过渡。"""

    VARIANTS = {
        # variant: (底色, 文字色, 描边)
        "primary": ("ink", "on_ink", None),
        "accent": ("accent", "on_accent", None),
        "ghost": (None, "ink", None),
        "outline": (None, "ink", "hairline"),
        "danger": (None, "accent", None),
    }

    def __init__(self, text: str = "", variant: str = "primary", height: int = 48,
                 radius: int = theme.R_CTRL, parent=None, icon: str | None = None,
                 icon_side: str = "right", size: int = theme.BODY):
        super().__init__(parent)
        self.setText(text)
        self.variant = variant
        self._text = text
        self._height = height
        self._radius = radius
        self._icon = icon
        self._icon_side = icon_side
        self._font_size = size
        self._hover = 0.0
        self._pressed = False
        self._busy = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedHeight(height)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(theme.DUR_FAST)
        self._anim.setEasingCurve(theme.EASE_STANDARD)
        self._anim.valueChanged.connect(self._on_hover)
        fm = QFontMetrics(font(size, theme.W_SEMI))
        pad = 26 if not icon else 22
        width = fm.horizontalAdvance(text) + pad * 2 + (24 if icon else 0)
        self.setMinimumWidth(max(48, width))
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

    # -- 交互
    def _on_hover(self, v) -> None:
        self._hover = float(v)
        self.update()

    def _animate(self, target: float) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._hover)
        self._anim.setEndValue(target)
        self._anim.start()

    def enterEvent(self, e) -> None:
        if self.isEnabled():
            self._animate(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e) -> None:
        self._animate(0.0)
        super().leaveEvent(e)

    def mousePressEvent(self, e) -> None:
        self._pressed = True
        self.update()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e) -> None:
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(e)

    def setText(self, text: str) -> None:  # noqa: N802
        self._text = text
        self.update()

    def text(self) -> str:
        return self._text

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.update()

    # -- 绘制
    def paintEvent(self, event) -> None:
        if self._height <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        base, text_key, border = self.VARIANTS[self.variant]
        radius = self._radius if self._radius < 900 else r.height() / 2

        hover = self._hover if self.isEnabled() else 0.0
        fill: QColor | None = None
        if base:
            if base == "ink":
                fill = Theme.mix("ink", "ink2", 0.22 + (0.16 if self._pressed else 0.0))
                fill = Theme.color("ink").lighter(int(100 + 12 * hover + (10 if self._pressed else 0)))
                if Theme.mode == "dark":
                    fill = Theme.color("ink").darker(int(100 + 10 * hover + (8 if self._pressed else 0)))
            else:
                fill = Theme.color(base)
                if hover > 0:
                    fill = Theme.mix(base, "ink", 0.10 * hover)
                if self._pressed:
                    fill = Theme.mix(base, "ink", 0.20)
        else:
            if hover > 0 or self._pressed:
                tone = "accent_soft" if self.variant == "danger" else "sunken"
                fill = Theme.color(tone)
                fill.setAlphaF(min(1.0, 0.35 + 0.65 * max(hover, 0.6 if self._pressed else 0)))

        border_color = Theme.color(border) if border else None
        if border and hover > 0:
            border_color = Theme.mix(border, "mist", 0.5 * hover)

        rounded(p, r, radius, fill, border_color)

        color = Theme.color(text_key)
        if not self.isEnabled():
            color.setAlphaF(0.38)
        p.setFont(font(self._font_size, theme.W_SEMI))
        fm = QFontMetrics(p.font())
        text = self._text
        if self._busy:
            text = "载入中" if not text else text
        tw = fm.horizontalAdvance(text)
        icon_w = 16 if self._icon else 0
        gap = 8 if self._icon else 0
        total = tw + icon_w + gap
        x = (self.width() - total) / 2
        baseline = (self.height() + fm.ascent() - fm.descent()) / 2

        if self._icon and self._icon_side == "left":
            icons.paint(p, self._icon, QRectF(x, (self.height() - 16) / 2, 16, 16), color, 1.7)
            x += icon_w + gap
        p.setPen(color)
        p.drawText(QPointF(x, baseline), text)
        if self._icon and self._icon_side == "right":
            x += tw + gap
            icons.paint(p, self._icon, QRectF(x, (self.height() - 16) / 2, 16, 16), color, 1.7)

        if self.hasFocus() and self.isEnabled():
            focus = QColor(Theme.hex("accent"))
            focus.setAlphaF(0.75)
            p.setPen(QPen(focus, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(r.adjusted(1.5, 1.5, -1.5, -1.5), radius, radius)
        p.end()


class IconButton(QAbstractButton):
    """纯图标按钮，圆形 hover 底，必须有 tooltip。"""

    def __init__(self, icon: str, size: int = 36, icon_size: int = 18,
                 tone: str = "slate", parent=None, hover: str = "sunken"):
        super().__init__(parent)
        self._icon = icon
        self._size = size
        self._icon_size = icon_size
        self._tone = tone
        self._hover_tone = hover
        self._hover = 0.0
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(theme.DUR_FAST)
        self._anim.valueChanged.connect(self._set_hover)

    def _set_hover(self, v) -> None:
        self._hover = float(v)
        self.update()

    def enterEvent(self, e) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._hover)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().enterEvent(e)

    def leaveEvent(self, e) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._hover)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(e)

    def set_icon(self, icon: str) -> None:
        self._icon = icon
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(self.rect())
        if self._hover > 0:
            c = Theme.color(self._hover_tone)
            c.setAlphaF(0.9 * self._hover)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(c)
            p.drawEllipse(r.adjusted(1, 1, -1, -1))
        color = Theme.color(self._tone)
        if not self.isEnabled():
            color.setAlphaF(0.3)
        inner = (self.width() - self._icon_size) / 2
        icons.paint(p, self._icon, QRectF(inner, inner, self._icon_size, self._icon_size), color, 1.6)
        p.end()


class NavItem(QAbstractButton):
    """侧栏导航项：图标 + 文字，选中态为浅色实底 + 强调色圆点。"""

    def __init__(self, key: str, label: str, icon: str, parent=None):
        super().__init__(parent)
        self.key = key
        self._label = label
        self._icon = icon
        self._selected = False
        self._hover = 0.0
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(theme.DUR_FAST)
        self._anim.valueChanged.connect(self._on_hover)

    def _on_hover(self, v) -> None:
        self._hover = float(v)
        self.update()

    def enterEvent(self, e) -> None:
        self._anim.stop(); self._anim.setStartValue(self._hover); self._anim.setEndValue(1.0); self._anim.start()
        super().enterEvent(e)

    def leaveEvent(self, e) -> None:
        self._anim.stop(); self._anim.setStartValue(self._hover); self._anim.setEndValue(0.0); self._anim.start()
        super().leaveEvent(e)

    def set_selected(self, value: bool) -> None:
        if self._selected != value:
            self._selected = value
            self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        r = QRectF(self.rect()).adjusted(4, 1, -4, -1)
        if self._selected:
            rounded(p, r, 12, Theme.color("surface"), Theme.color("hairline"))
        elif self._hover > 0:
            c = Theme.color("sunken")
            c.setAlphaF(0.9 * self._hover)
            rounded(p, r, 12, c)

        icon_color = Theme.color("ink") if self._selected else Theme.color("slate")
        icons.paint(p, self._icon, QRectF(16, (self.height() - 17) / 2, 17, 17), icon_color, 1.6)

        f = font(theme.BODY, theme.W_SEMI if self._selected else theme.W_MEDIUM, 0.1)
        p.setFont(f)
        p.setPen(Theme.color("ink") if self._selected else Theme.color("slate"))
        fm = QFontMetrics(f)
        p.drawText(QPointF(44, (self.height() + fm.ascent() - fm.descent()) / 2), self._label)

        if self._selected:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(Theme.color("accent"))
            p.drawEllipse(QPointF(self.width() - 22, self.height() / 2), 2.6, 2.6)
        p.end()


# ---------------------------------------------------------------- 分段控件

class Segmented(QWidget):
    """iOS 风分段控件：底槽 + 可滑动滑块，切换 220ms。"""

    changed = Signal(int)

    def __init__(self, options: list[str], index: int = 0, height: int = 36, parent=None):
        super().__init__(parent)
        self.options = options
        self.index = index
        self._pos = float(index)
        self._hover_index = -1
        self.setFixedHeight(height)
        self.setMinimumWidth(120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(theme.EASE_STANDARD)
        self._anim.valueChanged.connect(self._on_pos)

    def _on_pos(self, v) -> None:
        self._pos = float(v)
        self.update()

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(font(theme.CAPTION, theme.W_SEMI))
        w = max(fm.horizontalAdvance(o) + 34 for o in self.options) * len(self.options) + 8
        return QSize(int(w), self.height())

    def seg_width(self) -> float:
        return (self.width() - 8) / max(1, len(self.options))

    def set_index(self, index: int, animate: bool = True) -> None:
        index = max(0, min(len(self.options) - 1, index))
        if index == self.index:
            return
        self.index = index
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._pos)
            self._anim.setEndValue(float(index))
            self._anim.start()
        else:
            self._pos = float(index)
            self.update()
        self.changed.emit(index)

    def mousePressEvent(self, e) -> None:
        w = self.seg_width()
        idx = int((e.position().x() - 4) // w)
        idx = max(0, min(len(self.options) - 1, idx))
        self.set_index(idx)

    def mouseMoveEvent(self, e) -> None:
        w = self.seg_width()
        idx = int((e.position().x() - 4) // w)
        idx = max(0, min(len(self.options) - 1, idx))
        if idx != self._hover_index:
            self._hover_index = idx
            self.update()

    def leaveEvent(self, e) -> None:
        self._hover_index = -1
        self.update()
        super().leaveEvent(e)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        outer = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        rounded(p, outer, outer.height() / 2, Theme.color("sunken"))

        w = self.seg_width()
        left = 4 + self._pos * w
        slider = QRectF(left, 3, w, self.height() - 6)
        rounded(p, slider, slider.height() / 2, Theme.color("surface"), Theme.color("hairline"))

        for i, opt in enumerate(self.options):
            seg = QRectF(4 + i * w, 3, w, self.height() - 6)
            selected = i == self.index
            f = font(theme.CAPTION, theme.W_SEMI if selected else theme.W_MEDIUM, 0.2)
            p.setFont(f)
            if selected:
                p.setPen(Theme.color("ink"))
            elif i == self._hover_index:
                p.setPen(Theme.color("ink2"))
            else:
                p.setPen(Theme.color("slate"))
            p.drawText(seg, int(Qt.AlignmentFlag.AlignCenter), opt)
        p.end()


# ---------------------------------------------------------------- 开关

class Switch(QAbstractButton):
    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self._pos = 1.0 if checked else 0.0
        self.setFixedSize(46, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(theme.DUR_BASE)
        self._anim.setEasingCurve(theme.EASE_STANDARD)
        self._anim.valueChanged.connect(self._on_pos)
        self.toggled.connect(self._animate)

    def _on_pos(self, v) -> None:
        self._pos = float(v)
        self.update()

    def _animate(self, checked: bool) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._pos)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        track = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        off = Theme.color("hairline_strong")
        color = QColor(
            round(off.red() + (Theme.color("accent").red() - off.red()) * self._pos),
            round(off.green() + (Theme.color("accent").green() - off.green()) * self._pos),
            round(off.blue() + (Theme.color("accent").blue() - off.blue()) * self._pos),
        )
        rounded(p, track, track.height() / 2, color)
        knob_x = 3 + self._pos * (self.width() - 6 - 22)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QRectF(knob_x, 3, 22, 22))
        p.end()


# ---------------------------------------------------------------- 进度

class ProgressRing(QWidget):
    def __init__(self, value: float = 0.0, thickness: int = 7, size: int = 168,
                 center: str = "", subtitle: str = "", parent=None):
        super().__init__(parent)
        self._value = value
        self._shown = value
        self._thickness = thickness
        self._center = center
        self._subtitle = subtitle
        self.setFixedSize(size, size)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(theme.DUR_BASE)
        self._anim.setEasingCurve(theme.EASE_STANDARD)
        self._anim.valueChanged.connect(self._on_value)

    def _on_value(self, v) -> None:
        self._shown = float(v)
        self.update()

    def set_value(self, value: float, center: str | None = None, subtitle: str | None = None,
                  animate: bool = True) -> None:
        value = max(0.0, min(1.0, value))
        if center is not None:
            self._center = center
        if subtitle is not None:
            self._subtitle = subtitle
        self._value = value
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._shown)
            self._anim.setEndValue(value)
            self._anim.start()
        else:
            self._shown = value
            self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        t = self._thickness
        rect = QRectF(t / 2 + 1, t / 2 + 1, self.width() - t - 2, self.height() - t - 2)
        pen = QPen(Theme.color("hairline"), t)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 90 * 16, -360 * 16)

        if self._shown > 0.001:
            pen.setColor(Theme.color("accent"))
            p.setPen(pen)
            p.drawArc(rect, 90 * 16, int(-360 * 16 * self._shown))

        if self._center:
            p.setFont(font(theme.H2, theme.W_SEMI, -0.4))
            p.setPen(Theme.color("ink"))
            p.drawText(rect.adjusted(0, -14, 0, -14), int(Qt.AlignmentFlag.AlignCenter), self._center)
        if self._subtitle:
            p.setFont(font(theme.CAPTION, theme.W_MEDIUM, 0.2))
            p.setPen(Theme.color("slate"))
            p.drawText(rect.adjusted(0, 30, 0, 30), int(Qt.AlignmentFlag.AlignCenter), self._subtitle)
        p.end()


class ProgressBar(QWidget):
    def __init__(self, value: float = 0.0, height: int = 4, color: str = "accent", parent=None):
        super().__init__(parent)
        self._value = value
        self._shown = value
        self._color = color
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(theme.DUR_BASE)
        self._anim.setEasingCurve(theme.EASE_STANDARD)
        self._anim.valueChanged.connect(self._on_value)

    def _on_value(self, v) -> None:
        self._shown = float(v)
        self.update()

    def set_value(self, value: float, animate: bool = True) -> None:
        value = max(0.0, min(1.0, value))
        self._value = value
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._shown)
            self._anim.setEndValue(value)
            self._anim.start()
        else:
            self._shown = value
            self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        h = self.height()
        rounded(p, QRectF(0, 0, self.width(), h), h / 2, Theme.color("hairline"))
        if self._shown > 0:
            rounded(p, QRectF(0, 0, max(h, self.width() * self._shown), h), h / 2, Theme.color(self._color))
        p.end()


class MasteryDots(QWidget):
    """五个圆点表示 Leitner 盒子等级。"""

    def __init__(self, box: int = 0, count: int = 5, parent=None):
        super().__init__(parent)
        self.box = box
        self.count = count
        self.setFixedSize(count * 12, 10)

    def set_box(self, box: int) -> None:
        self.box = box
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        for i in range(self.count):
            x = i * 12 + 3
            filled = i < self.box
            color = Theme.color("accent") if filled else Theme.color("hairline_strong")
            if filled and self.box <= 1:
                color = Theme.color("accent")
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            p.drawEllipse(QPointF(x, 5), 3, 3)
        p.end()


class BarChart(QWidget):
    """七日学习量柱状图，柱体依次生长；今天用强调色。"""

    def __init__(self, data: list[tuple[str, int]] | None = None, parent=None):
        super().__init__(parent)
        self.data = data or []
        self._grow = 0.0
        self.setMinimumHeight(124)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(theme.DUR_CHART)
        self._anim.setEasingCurve(theme.EASE_CHART)
        self._anim.valueChanged.connect(self._on_grow)

    def _on_grow(self, v) -> None:
        self._grow = float(v)
        self.update()

    def set_data(self, data: list[tuple[str, int]]) -> None:
        self.data = data
        self.play()

    def play(self) -> None:
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def showEvent(self, e) -> None:
        super().showEvent(e)
        self.play()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        if not self.data:
            return
        pad_bottom = 26
        pad_top = 22
        h = self.height() - pad_bottom - pad_top
        n = len(self.data)
        gap = 18
        bar_w = min(34, (self.width() - gap * (n - 1)) / n)
        total_w = bar_w * n + gap * (n - 1)
        x0 = (self.width() - total_w) / 2
        max_val = max(1, max(v for _, v in self.data))

        # 基线
        p.setPen(QPen(Theme.color("hairline"), 1))
        base_y = pad_top + h
        p.drawLine(QPointF(0, base_y + 0.5), QPointF(self.width(), base_y + 0.5))

        for i, (label, value) in enumerate(self.data):
            phase = max(0.0, min(1.0, self._grow * 1.35 - i * 0.05))
            ratio = value / max_val
            bh = max(3.0, h * ratio * phase)
            x = x0 + i * (bar_w + gap)
            y = base_y - bh
            is_today = i == n - 1
            if value == 0:
                color = Theme.color("hairline")
                rounded(p, QRectF(x, base_y - 3, bar_w, 3), 1.5, color)
            else:
                color = Theme.color("accent") if is_today else Theme.color("ink")
                if not is_today:
                    color.setAlphaF(0.86)
                rounded(p, QRectF(x, y, bar_w, bh), 6, color)

            p.setFont(font(theme.CAPTION, theme.W_MEDIUM, 0.2))
            p.setPen(Theme.color("ink") if is_today else Theme.color("mist"))
            if value:
                p.drawText(QRectF(x - 10, y - 20, bar_w + 20, 16),
                           int(Qt.AlignmentFlag.AlignCenter), str(value))
            p.setPen(Theme.color("ink2") if is_today else Theme.color("mist"))
            p.drawText(QRectF(x - 10, base_y + 6, bar_w + 20, 16),
                       int(Qt.AlignmentFlag.AlignCenter), label)
        p.end()


class Heatmap(QWidget):
    """最近 28 天学习热力格（7 列 × 4 行）。"""

    def __init__(self, values: list[int] | None = None, cell: int = 24, gap: int = 6, parent=None):
        super().__init__(parent)
        self.values = values or []
        self.cell = cell
        self.gap = gap
        self.setFixedHeight(4 * cell + 3 * gap)
        self.setMinimumWidth(7 * cell + 6 * gap)

    def set_values(self, values: list[int]) -> None:
        self.values = values
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        cell, gap = self.cell, self.gap
        if len(self.values) == 28:
            for i, v in enumerate(self.values):
                row, col = i // 7, i % 7
                x = col * (cell + gap)
                y = row * (cell + gap)
                if v == 0:
                    color = Theme.color("hairline")
                else:
                    ratio = 1.0 if v >= 20 else (0.72 if v >= 12 else (0.5 if v >= 6 else 0.28))
                    color = QColor(Theme.color("accent"))
                    color.setAlphaF(ratio)
                rounded(p, QRectF(x, y, cell, cell), 7, color)
        p.end()


# ---------------------------------------------------------------- 输入

class SearchField(QLineEdit):
    def __init__(self, placeholder: str = "搜索单词、释义或主题", parent=None):
        super().__init__(parent)
        self._hint = placeholder
        self.setPlaceholderText("")
        self.setFixedHeight(44)
        self.setClearButtonEnabled(False)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        p = QPainter(self)
        icons.paint(p, "search", QRectF(15, (self.height() - 16) / 2, 16, 16),
                    Theme.color("mist"), 1.7)
        if not self.text():
            p.setFont(font(theme.BODY, theme.W_REGULAR))
            p.setPen(Theme.color("mist"))
            p.drawText(QRect(44, 0, self.width() - 56, self.height()),
                       int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                       self._hint)
        p.end()


# ---------------------------------------------------------------- 测验选项

class OptionRow(QAbstractButton):
    """四选一答题行。"""

    def __init__(self, letter: str, text: str, parent=None):
        super().__init__(parent)
        self.letter = letter
        self._text = text
        self.state_ = "idle"     # idle | correct | wrong | muted
        self._hover = 0.0
        self.setFixedHeight(52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(theme.DUR_FAST)
        self._anim.valueChanged.connect(self._on_hover)

    def text(self) -> str:
        return self._text

    def _on_hover(self, v) -> None:
        self._hover = float(v)
        self.update()

    def enterEvent(self, e) -> None:
        if self.state_ == "idle":
            self._anim.stop(); self._anim.setStartValue(self._hover); self._anim.setEndValue(1.0); self._anim.start()
        super().enterEvent(e)

    def leaveEvent(self, e) -> None:
        self._anim.stop(); self._anim.setStartValue(self._hover); self._anim.setEndValue(0.0); self._anim.start()
        super().leaveEvent(e)

    def set_state(self, state: str) -> None:
        self.state_ = state
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        fill = None
        border = Theme.color("hairline")
        if self.state_ == "correct":
            fill = Theme.color("surface")
            border = Theme.color("ink")
        elif self.state_ == "wrong":
            fill = Theme.color("accent_soft")
            border = Theme.color("accent")
        elif self._hover > 0 and self.state_ == "idle":
            fill = Theme.color("sunken")
            border = Theme.color("hairline_strong")
        rounded(p, r, 16, fill, border)

        # 字母徽标
        badge = QRectF(16, (self.height() - 28) / 2, 28, 28)
        bcolor = Theme.color("sunken")
        tcolor = Theme.color("slate")
        if self.state_ == "correct":
            bcolor = Theme.color("ink")
            tcolor = Theme.color("on_ink")
        elif self.state_ == "wrong":
            bcolor = Theme.color("accent")
            tcolor = Theme.color("on_accent")
        rounded(p, badge, 14, bcolor)
        p.setFont(font(theme.CAPTION, theme.W_SEMI, 0.4))
        p.setPen(tcolor)
        p.drawText(badge, int(Qt.AlignmentFlag.AlignCenter), self.letter)

        alpha = 1.0
        if self.state_ == "muted":
            alpha = 0.42
        text_color = Theme.color("ink")
        text_color.setAlphaF(alpha)
        p.setFont(font(theme.BODY + 1, theme.W_MEDIUM))
        fm = QFontMetrics(p.font())
        p.setPen(text_color)
        p.drawText(QRectF(58, 0, self.width() - 92, self.height()),
                   int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), self._text)

        if self.state_ == "correct":
            icons.paint(p, "check", QRectF(self.width() - 42, (self.height() - 18) / 2, 18, 18),
                        Theme.color("ink"), 1.9)
        elif self.state_ == "wrong":
            icons.paint(p, "close", QRectF(self.width() - 42, (self.height() - 18) / 2, 18, 18),
                        Theme.color("accent"), 1.9)
        p.end()


# ---------------------------------------------------------------- 单词卡

class FlipCard(QWidget):
    """可翻面的单词卡：3D 感用水平缩放模拟，420ms InOutCubic。"""

    flipped = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._word = None
        self._flip = 0.0
        self._revealed = False
        self._index_text = ""
        self.setMinimumSize(520, 330)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(theme.DUR_FLIP)
        self._anim.setEasingCurve(theme.EASE_FLIP)
        self._anim.valueChanged.connect(self._on_flip)

    def set_word(self, word, index_text: str = "") -> None:
        self._word = word
        self._index_text = index_text
        self._flip = 0.0
        self._revealed = False
        self.update()

    def reveal(self) -> None:
        if self._revealed or self._word is None:
            return
        self._revealed = True
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()
        self.flipped.emit(True)

    def reset_flip(self) -> None:
        self._revealed = False
        self._flip = 0.0
        self.update()
        self.flipped.emit(False)

    def is_revealed(self) -> bool:
        return self._revealed

    def _on_flip(self, v) -> None:
        self._flip = float(v)
        self.update()

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self.reveal()
        super().mousePressEvent(e)

    def _draw_text(self, p: QPainter, rect: QRectF, text: str, px: int, weight,
                   color_key: str, align=Qt.AlignmentFlag.AlignCenter, wrap: bool = True,
                   tracking: float = 0.0) -> None:
        p.setFont(font(px, weight, tracking))
        p.setPen(Theme.color(color_key))
        p.drawText(rect, _flags(align, wrap), text)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        w, h = self.width(), self.height()
        cx = w / 2
        s = abs(math.cos(math.pi * self._flip))
        s = max(0.03, s)

        p.save()
        p.translate(cx, 0)
        p.scale(s, 1.0)
        p.translate(-cx, 0)

        card = QRectF(0.5, 0.5, w - 1, h - 1)
        rounded(p, card, theme.R_CARD, Theme.color("surface"), Theme.color("hairline"))

        if self._word is None:
            p.restore()
            return

        wd = self._word
        front = self._flip < 0.5

        if front:
            # 顶部元信息
            p.setFont(font(theme.EYEBROW, theme.W_SEMI, 1.4))
            p.setPen(Theme.color("mist"))
            p.drawText(QRectF(32, 26, w - 64, 16),
                       int(Qt.AlignmentFlag.AlignLeft), f"{wd.level}   ·   {wd.pos}")
            if self._index_text:
                p.drawText(QRectF(32, 26, w - 64, 16),
                           int(Qt.AlignmentFlag.AlignRight), self._index_text)

            # 单词本体：自动缩字号以适配长词
            size = 44
            fm = QFontMetrics(font(size, theme.W_SEMI, -1.0))
            while fm.horizontalAdvance(wd.es) > w - 96 and size > 22:
                size -= 2
                fm = QFontMetrics(font(size, theme.W_SEMI, -1.0))
            self._draw_text(p, QRectF(48, h / 2 - 44, w - 96, 88), wd.es, size,
                            theme.W_SEMI, "ink", tracking=-1.0, wrap=False)

            p.setFont(font(theme.CAPTION, theme.W_MEDIUM, 0.3))
            p.setPen(Theme.color("mist"))
            p.drawText(QRectF(32, h - 44, w - 64, 18),
                       int(Qt.AlignmentFlag.AlignCenter), "轻点卡片 / 空格  查看释义")
        else:
            p.setFont(font(theme.CAPTION, theme.W_MEDIUM, 0.3))
            p.setPen(Theme.color("mist"))
            p.drawText(QRectF(32, 24, w - 64, 16),
                       int(Qt.AlignmentFlag.AlignLeft), wd.es)

            self._draw_text(p, QRectF(40, 94, w - 80, 14), "释义", theme.EYEBROW,
                            theme.W_SEMI, "mist", tracking=1.6,
                            align=Qt.AlignmentFlag.AlignLeft, wrap=False)
            self._draw_text(p, QRectF(40, 114, w - 80, 84), wd.zh, 26, theme.W_SEMI, "ink",
                            tracking=-0.3, wrap=True,
                            align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

            if wd.ex_es:
                p.setPen(QPen(Theme.color("hairline"), 1))
                p.drawLine(QPointF(40, h - 128), QPointF(w - 40, h - 128))
                self._draw_text(p, QRectF(40, h - 116, w - 80, 44), wd.ex_es,
                                theme.BODY + 1, theme.W_REGULAR, "ink2",
                                align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                self._draw_text(p, QRectF(40, h - 70, w - 80, 24), wd.ex_zh,
                                theme.BODY_S, theme.W_REGULAR, "slate",
                                align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            p.restore()
            return
        p.restore()
        p.end()


# ---------------------------------------------------------------- Toast

class Toast(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hide()
        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(0.0)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setDuration(theme.DUR_BASE)
        self._anim.setEasingCurve(theme.EASE_STANDARD)

    def show_message(self, text: str, msec: int = 1800) -> None:
        self._text = text
        fm = QFontMetrics(font(theme.BODY_S, theme.W_MEDIUM))
        width = fm.horizontalAdvance(text) + 44
        self.resize(max(120, width), 42)
        self.relocate()
        self.show()
        self.raise_()
        self._anim.stop()
        self._anim.setStartValue(self._effect.opacity())
        self._anim.setEndValue(1.0)
        self._anim.start()
        self._timer_id = self.startTimer(msec)

    def timerEvent(self, event) -> None:
        self.killTimer(event.timerId())
        self._anim.stop()
        self._anim.setStartValue(self._effect.opacity())
        self._anim.setEndValue(0.0)
        self._anim.start()
        self._anim.finished.connect(self._maybe_hide)

    def _maybe_hide(self) -> None:
        if self._effect.opacity() <= 0.02:
            self.hide()
        try:
            self._anim.finished.disconnect(self._maybe_hide)
        except (RuntimeError, TypeError):
            pass

    def relocate(self) -> None:
        if self.parentWidget():
            pw = self.parentWidget()
            self.move(int((pw.width() - self.width()) / 2), int(pw.height() - self.height() - 36))

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        fill = Theme.color("ink")
        rounded(p, QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 21, fill)
        p.setFont(font(theme.BODY_S, theme.W_MEDIUM, 0.2))
        p.setPen(Theme.color("on_ink"))
        p.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), self._text)
        p.end()


# ---------------------------------------------------------------- 动效工具

def fade_in(widget: QWidget, duration: int = theme.DUR_PAGE, offset: int = 0) -> None:
    """页面切换：淡入 + 轻微上移。"""
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0.0)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(theme.EASE_PAGE)

    def _end() -> None:
        effect.setEnabled(False)

    anim.finished.connect(_end)
    widget._fade = anim  # 保活
    anim.start(QAbstractAnimation.DeletionPolicy.KeepWhenStopped)


def make_row(*widgets: QWidget, spacing: int = 12, stretch_last: bool = False) -> QWidget:
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(spacing)
    for i, item in enumerate(widgets):
        lay.addWidget(item)
    if stretch_last:
        lay.addStretch(1)
    return w


def clear_layout(layout) -> None:
    """清空布局并销毁子控件。

    关键点：先 hide() 再 setParent(None)。否则一个正在显示的控件被解除父子关系后
    会短暂变成顶层窗口（屏幕上闪一下的小窗），交给 deleteLater() 才消失。
    """
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.hide()
            w.setParent(None)
            w.deleteLater()
        elif item.layout() is not None:
            clear_layout(item.layout())