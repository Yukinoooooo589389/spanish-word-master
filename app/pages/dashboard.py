"""今日（Dashboard）：一屏交代「现在该做什么」与「我走到哪了」。"""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QVBoxLayout, QWidget

from .. import theme, widgets
from .base import Page, hbox, page_header, section_title, vbox, wrap

WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]


class Dashboard(Page):
    key = "today"
    title = "今日"

    def __init__(self, ctx):
        super().__init__(ctx)
        self.build()

    def on_show(self) -> None:
        self.build()
        widgets.fade_in(self, 200)

    # ------------------------------------------------------------ 构建

    def build(self) -> None:
        widgets.clear_layout(self.root)
        s = self.store.summary()
        goal = max(1, s["goal"])
        ratio = min(1.0, s["today_studied"] / goal)

        # 操作区
        start = widgets.AnimButton("开始学习", "primary", 48, icon="arrow_right", size=theme.BODY)
        start.clicked.connect(lambda: self.ctx.navigate("study"))
        quiz = widgets.AnimButton("快速测验", "outline", 48, size=theme.BODY)
        quiz.clicked.connect(lambda: self.ctx.navigate("quiz"))
        actions = wrap(hbox(10, (0, 6, 0, 0)))
        actions.layout().addWidget(quiz)
        actions.layout().addWidget(start)

        today = date.today()
        self.root.addWidget(page_header(
            f"{today.month}月{today.day}日  星期{WEEKDAYS[today.weekday()]}",
            f"今天，学 {goal} 个词。",
            f"今日已完成 {s['today_studied']} / {goal} 个词 · 连续 {s['streak']} 天",
            actions,
        ))
        self.root.addSpacing(30)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(24)
        grid.addWidget(self._progress_card(s, ratio), 0, 0)
        grid.addWidget(self._week_card(), 0, 1)
        grid.addWidget(self._recent_card(), 1, 0)
        grid.addWidget(self._level_card(), 1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(2, 1)
        holder = wrap(grid)
        self.root.addWidget(holder, 1)

    # ------------------------------------------------------------ 卡片

    def _progress_card(self, s: dict, ratio: float) -> QWidget:
        card = widgets.Card(padding=26)
        ring = widgets.ProgressRing(
            ratio,
            size=172,
            center=f"{round(ratio * 100)}%",
            subtitle="今日进度",
        )
        row = hbox(28)
        row.addWidget(ring, 0, Qt.AlignmentFlag.AlignVCenter)

        stats = vbox(16)
        for label, value, tone in (
            ("累计词汇", f"{s['total']}", "ink"),
            ("已掌握", f"{s['mastered']}", "ink"),
            ("学习连续", f"{s['streak']} 天", "ink"),
        ):
            item = vbox(2)
            item.addWidget(widgets.caption(label, "slate"))
            item.addWidget(widgets.ThemedLabel(value, theme.H2, theme.W_SEMI, tone, tracking=-0.3))
            stats.addLayout(item)
        row.addLayout(stats, 1)
        card.body().addLayout(row)
        return card

    def _week_card(self) -> QWidget:
        data = self.store.week_activity()
        total = sum(v for _, v in data)
        card = widgets.Card(padding=26)
        card.body().addWidget(section_title("本周学习", f"共 {total} 个词"))
        card.body().addSpacing(18)
        chart = widgets.BarChart(data)
        card.body().addWidget(chart, 1)
        return card

    def _recent_card(self) -> QWidget:
        card = widgets.Card(padding=26)
        recent = self.store.recent(3)
        card.body().addWidget(section_title("最近学习", "按最后一次复习排序"))
        card.body().addSpacing(16)
        if not recent:
            empty = widgets.body("还没有学习记录，先从第一张卡片开始。", "slate")
            card.body().addWidget(empty)
            card.body().addStretch(1)
            return card
        for i, w in enumerate(recent):
            if i:
                card.body().addWidget(widgets.Divider())
            row = hbox(14, (0, 7, 0, 7))
            left = vbox(3)
            left.addWidget(widgets.ThemedLabel(w.es, theme.H3, theme.W_SEMI, "ink"))
            left.addWidget(widgets.caption(w.zh, "slate"))
            row.addLayout(left, 1)
            chip = widgets.Chip(w.level, "sunken", "slate")
            row.addWidget(chip, 0, Qt.AlignmentFlag.AlignVCenter)
            dots = widgets.MasteryDots(self.store.card(w.id).box, 6)
            row.addWidget(dots, 0, Qt.AlignmentFlag.AlignVCenter)
            card.body().addWidget(wrap(row))
        card.body().addStretch(1)
        return card

    def _level_card(self) -> QWidget:
        card = widgets.Card(padding=26)
        card.body().addWidget(section_title("词库进度", "按 CEFR 等级"))
        card.body().addSpacing(18)
        dist = self.store.level_distribution()
        for lv, (done, total) in dist.items():
            total = max(1, total)
            head = hbox(8)
            head.addWidget(widgets.ThemedLabel(lv, theme.BODY_S, theme.W_SEMI, "ink"))
            head.addStretch(1)
            head.addWidget(widgets.caption(f"{done} / {total}", "slate"))
            card.body().addWidget(wrap(head))
            card.body().addSpacing(8)
            bar = widgets.ProgressBar(done / total, 4)
            card.body().addWidget(bar)
            card.body().addSpacing(16)
        card.body().addStretch(1)
        return card