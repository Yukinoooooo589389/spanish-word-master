"""Palabra · 设计令牌（design tokens）。

所有颜色、字号、圆角、动效时长都在这里定义，页面只允许引用令牌，不写死数值。
参考 DESIGN_SYSTEM.md。
"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve
from PySide6.QtGui import QColor, QFont

# ---------------------------------------------------------------- 色彩令牌

LIGHT: dict[str, str] = {
    "canvas": "#F6F6F8",
    "surface": "#FFFFFF",
    "surface2": "#FBFBFC",
    "sunken": "#F0F0F3",
    "hairline": "#E7E7EA",
    "hairline_strong": "#D6D6DA",
    "ink": "#0B0B0C",
    "ink2": "#3A3A3C",
    "slate": "#6E6E73",
    "mist": "#A1A1A6",
    "accent": "#C8362B",
    "accent_soft": "#FBEDEB",
    "accent_press": "#A72B21",
    "on_accent": "#FFFFFF",
    "on_ink": "#FFFFFF",
}

DARK: dict[str, str] = {
    "canvas": "#0A0A0B",
    "surface": "#131315",
    "surface2": "#17171A",
    "sunken": "#1D1D20",
    "hairline": "#26262A",
    "hairline_strong": "#3A3A3F",
    "ink": "#F5F5F7",
    "ink2": "#D2D2D6",
    "slate": "#A1A1A6",
    "mist": "#6E6E73",
    "accent": "#E45B4D",
    "accent_soft": "#2A1A18",
    "accent_press": "#F0705F",
    "on_accent": "#FFFFFF",
    "on_ink": "#0B0B0C",
}

# ---------------------------------------------------------------- 尺寸令牌

R_SHELL = 18
R_CARD = 22
R_CTRL = 14
R_PILL = 999

SIDEBAR_W = 232
TITLEBAR_H = 52
CONTENT_PAD = 48

# ---------------------------------------------------------------- 排版令牌

DISPLAY = 46
H1 = 30
H2 = 22
H3 = 17
BODY = 14
BODY_S = 13
CAPTION = 12
EYEBROW = 11

W_REGULAR = QFont.Weight.Normal      # 400
W_MEDIUM = QFont.Weight.Medium       # 500
W_SEMI = QFont.Weight.DemiBold       # 600
W_BOLD = QFont.Weight.Bold           # 700

# ---------------------------------------------------------------- 动效令牌

DUR_FAST = 140
DUR_BASE = 260
DUR_PAGE = 240
DUR_FLIP = 420
DUR_CHART = 520

EASE_STANDARD = QEasingCurve.Type.OutCubic
EASE_PAGE = QEasingCurve.Type.OutQuint
EASE_FLIP = QEasingCurve.Type.InOutCubic
EASE_CHART = QEasingCurve.Type.OutQuart

FONT_FAMILIES = ["Segoe UI", "Microsoft YaHei UI", "PingFang SC", "Noto Sans CJK SC"]


class Theme:
    """全局主题状态。深浅色切换时 emit 由 main 处理 QSS 重建。"""

    mode = "light"

    @classmethod
    def tokens(cls) -> dict[str, str]:
        return DARK if cls.mode == "dark" else LIGHT

    @classmethod
    def color(cls, key: str) -> QColor:
        return QColor(cls.tokens()[key])

    @classmethod
    def hex(cls, key: str) -> str:
        return cls.tokens()[key]

    @classmethod
    def alpha(cls, key: str, a: float) -> QColor:
        c = cls.color(key)
        c.setAlphaF(max(0.0, min(1.0, a)))
        return c

    @classmethod
    def mix(cls, key: str, other: str, t: float) -> QColor:
        """在令牌与另一颜色之间插值，用于 hover / press 态。"""
        c1, c2 = cls.color(key), cls.color(other)
        t = max(0.0, min(1.0, t))
        return QColor(
            round(c1.red() + (c2.red() - c1.red()) * t),
            round(c1.green() + (c2.green() - c1.green()) * t),
            round(c1.blue() + (c2.blue() - c1.blue()) * t),
        )

    @classmethod
    def toggle(cls) -> None:
        cls.mode = "dark" if cls.mode == "light" else "light"


def font(size: int = BODY, weight: QFont.Weight = W_REGULAR, spacing: float = 0.0) -> QFont:
    f = QFont()
    f.setFamilies(FONT_FAMILIES)
    f.setPixelSize(size)
    f.setWeight(weight)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
    f.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return f


def qss() -> str:
    """原生控件（输入、下拉、滚动条、提示）的样式表。自绘控件不在此处。"""
    t = Theme.tokens()
    return f"""
    * {{
        font-family: "Segoe UI", "Microsoft YaHei UI";
        outline: none;
    }}
    QWidget {{
        color: {t['ink']};
    }}
    QToolTip {{
        background: {t['ink']};
        color: {t['on_ink']};
        border: none;
        border-radius: 8px;
        padding: 7px 10px;
        font-size: 12px;
    }}
    QLineEdit {{
        background: {t['surface']};
        border: 1px solid {t['hairline']};
        border-radius: {R_CTRL}px;
        padding: 0 16px 0 44px;
        color: {t['ink']};
        font-size: 14px;
        selection-background-color: {t['accent']};
        selection-color: #FFFFFF;
    }}
    QLineEdit:hover {{
        border-color: {t['hairline_strong']};
    }}
    QLineEdit:focus {{
        border-color: {t['ink']};
        background: {t['surface']};
    }}
    QComboBox {{
        background: {t['surface']};
        border: 1px solid {t['hairline']};
        border-radius: {R_CTRL}px;
        padding: 0 14px;
        color: {t['ink']};
        font-size: 13px;
        min-width: 96px;
    }}
    QComboBox:hover {{ border-color: {t['hairline_strong']}; }}
    QComboBox::drop-down {{ border: none; width: 26px; }}
    QComboBox::down-arrow {{ image: none; }}
    QComboBox QAbstractItemView {{
        background: {t['surface']};
        border: 1px solid {t['hairline']};
        border-radius: 12px;
        padding: 6px;
        color: {t['ink']};
        selection-background-color: {t['sunken']};
        selection-color: {t['ink']};
        outline: none;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 11px;
        margin: 6px 3px 6px 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {t['hairline_strong']};
        border-radius: 3px;
        min-height: 40px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {t['mist']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    QScrollBar:horizontal {{ height: 0; }}
    QListWidget {{ background: transparent; border: none; outline: none; }}
    """