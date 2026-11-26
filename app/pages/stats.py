"""统计页：把学习数据讲成三句话 —— 学了多少、记得怎样、接下来学什么。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from .. import theme, widgets
from ..store import MAX_BOX
from .base import Page, hbox, page_header, section_title, vbox, wrap


class Swatch(QWidget):
    """热力图图例色块。"""

    def __init__(self, alpha: float, size: int = 12, parent=None):
        super().__init__(parent)
        self.alpha = alpha
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        color = QColor(theme.Theme.color("accent"))
        color.setAlphaF(self.alpha)
        widgets.rounded(p, self.rect().adjusted(0, 0, -1, -1), 3, color)
        p.end()


class Stats(Page):
    key = "stats"
    title = "统计"

    def __init__(self, ctx):
        super().__init__(ctx)
        self.build()

    def on_show(self) -> None:
        self.build()
        widgets.fade_in(self, 200)

    def build(self) -> None:
        widgets.clear_layout(self.root)
        s = self.store.summary()

        self.root.addWidget(page_header(
            "数据", "学习统计",
            f"共 {s['total']} 个词 · 已开始 {s['seen']} 个 · 到期 {s['due']} 个",
        ))
        self.root.addSpacing(16)

        tiles = hbox(18)
        for label, value, hint, tone in (
            ("累计词汇", str(s["total"]), "词库总量", "ink"),
            ("已掌握", str(s["mastered"]), f"记忆层级 {MAX_BOX - 1} 以上", "ink"),
            ("今日正确率", f"{round(s['today_accuracy'] * 100)}%", f"答对 {s['today_correct']} 次", "accent"),
        ):
            tiles.addWidget(self._tile(label, value, hint, tone), 1)
        self.root.addWidget(wrap(tiles))
        self.root.addSpacing(12)

        row = hbox(18)
        row.addWidget(self._week_card(), 3)
        row.addWidget(self._memory_card(s), 2)
        self.root.addWidget(wrap(row))
        self.root.addSpacing(12)

        row2 = hbox(18)
        row2.addWidget(self._level_card(), 3)
        row2.addWidget(self._heat_card(), 2)
        self.root.addWidget(wrap(row2))
        self.root.addStretch(1)

    # ------------------------------------------------------------ 组件

    def _tile(self, label: str, value: str, hint: str, tone: str) -> QWidget:
        card = widgets.Card(padding=20)
        card.body().addWidget(widgets.caption(label, "slate"))
        card.body().addSpacing(6)
        card.body().addWidget(widgets.ThemedLabel(value, 28, theme.W_SEMI, tone, tracking=-0.6))
        card.body().addSpacing(2)
        card.body().addWidget(widgets.caption(hint, "mist"))
        return card

    def _week_card(self) -> QWidget:
        data = self.store.week_activity()
        total = sum(v for _, v in data)
        card = widgets.Card(padding=20)
        card.body().addWidget(section_title("七日学习量", f"共 {total} 个词"))
        card.body().addSpacing(10)
        card.body().addWidget(widgets.BarChart(data), 1)
        return card

    def _memory_card(self, s: dict) -> QWidget:
        card = widgets.Card(padding=20)
        card.body().addWidget(section_title("记忆分布", "按记忆层级"))
        card.body().addSpacing(10)
        rows = [
            ("已掌握", s["mastered"], "accent"),
            ("学习中", s["learning"], "ink"),
            ("未开始", s["fresh"], "mist"),
        ]
        total = max(1, s["total"])
        for i, (label, value, tone) in enumerate(rows):
            if i:
                card.body().addSpacing(10)
            head = hbox(0)
            head.addWidget(widgets.body(label, "ink2"), 1)
            head.addWidget(widgets.caption(f"{value} 个", "slate"))
            card.body().addWidget(wrap(head))
            card.body().addSpacing(6)
            card.body().addWidget(widgets.ProgressBar(value / total, 6, tone))
        card.body().addStretch(1)
        return card

    def _level_card(self) -> QWidget:
        card = widgets.Card(padding=20)
        card.body().addWidget(section_title("等级进度", "CEFR A1 → B1"))
        card.body().addSpacing(10)
        for lv, (done, total) in self.store.level_distribution().items():
            t = max(1, total)
            head = hbox(8)
            head.addWidget(widgets.ThemedLabel(lv, theme.CAPTION, theme.W_SEMI, "ink"))
            head.addStretch(1)
            head.addWidget(widgets.caption(f"{round(done / t * 100)}% · {done}/{total}", "slate"))
            card.body().addWidget(wrap(head))
            card.body().addSpacing(6)
            card.body().addWidget(widgets.ProgressBar(done / t, 4))
            card.body().addSpacing(8)
        card.body().addStretch(1)
        return card

    def _heat_card(self) -> QWidget:
        card = widgets.Card(padding=20)
        card.body().addWidget(section_title("学习热度", "最近 28 天 · 越深越多"))
        card.body().addSpacing(10)
        card.body().addWidget(widgets.Heatmap(self.store.heatmap(28), cell=20, gap=6),
                              0, Qt.AlignmentFlag.AlignLeft)
        card.body().addStretch(1)
        return card