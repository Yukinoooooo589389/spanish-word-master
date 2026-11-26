"""学习页：一张卡片，三个自评档位，其余全部留白。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from .. import theme, tts, widgets
from ..store import RATING_AGAIN, RATING_GOOD, RATING_HARD
from .base import Page, hbox, page_header, vbox, wrap


class Study(Page):
    key = "study"
    title = "学习"

    def __init__(self, ctx):
        super().__init__(ctx)
        self.queue: list = []
        self.index = 0
        self.stats = {"good": 0, "hard": 0, "again": 0}
        self.stack = QStackedWidget()
        self.root.addWidget(self.stack, 1)
        self._build_frame()
        self._build_done()
        self.stack.setCurrentIndex(0)

        self.shortcuts = []
        for key, fn in (
            ("Space", self._reveal_or_rate),
            ("Return", self._reveal_or_rate),
            ("1", lambda: self._rate(RATING_AGAIN)),
            ("2", lambda: self._rate(RATING_HARD)),
            ("3", lambda: self._rate(RATING_GOOD)),
            ("Left", self._skip),
            ("Right", self._skip),
            ("Escape", lambda: self.ctx.navigate("today")),
        ):
            sc = QShortcut(QKeySequence(key), self)
            sc.setContext(Qt.ShortcutContext.WindowShortcut)
            sc.activated.connect(fn)
            sc.setEnabled(False)
            self.shortcuts.append(sc)

    # ------------------------------------------------------------ 会话

    def start(self) -> None:
        self.queue = self.store.build_session()
        self.index = 0
        self.stats = {"good": 0, "hard": 0, "again": 0}
        self.stack.setCurrentIndex(0)
        self._load_card()

    def on_show(self) -> None:
        self.start()
        widgets.fade_in(self, 200)

    # ------------------------------------------------------------ 静态骨架

    def _build_frame(self) -> None:
        view = QWidget()
        lay = QVBoxLayout(view)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.speaker = widgets.IconButton("speaker", 36, 18, "slate")
        self.speaker.setToolTip("朗读这个单词")
        self.speaker.clicked.connect(self._speak)
        self.goal_chip = widgets.Chip("", "sunken", "slate")
        right = wrap(hbox(10))
        right.layout().addWidget(self.goal_chip, 0, Qt.AlignmentFlag.AlignVCenter)
        right.layout().addWidget(self.speaker, 0, Qt.AlignmentFlag.AlignVCenter)

        self.header = page_header("学习", "", "准备中", right)
        lay.addWidget(self.header)
        lay.addSpacing(22)

        self.progress = widgets.ProgressBar(0.0, 3)
        lay.addWidget(self.progress)
        lay.addStretch(1)

        self.card = widgets.FlipCard()
        self.card.setFixedSize(600, 350)
        self.card.flipped.connect(self._on_flip)
        lay.addWidget(self.card, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(30)

        # 操作区：未翻面时只有一个动作
        self.action_area = QWidget()
        alay = QVBoxLayout(self.action_area)
        alay.setContentsMargins(0, 0, 0, 0)
        alay.setSpacing(14)

        self.rate_row = QWidget()
        rlay = hbox(12)
        rlay.setContentsMargins(0, 0, 0, 0)
        self.rate_row.setLayout(rlay)
        self.btn_again = widgets.AnimButton("不认识", "outline", 52, theme.R_CTRL)
        self.btn_hard = widgets.AnimButton("模糊", "outline", 52, theme.R_CTRL)
        self.btn_good = widgets.AnimButton("认识", "primary", 52, theme.R_CTRL)
        for b, fn in ((self.btn_again, lambda: self._rate(RATING_AGAIN)),
                      (self.btn_hard, lambda: self._rate(RATING_HARD)),
                      (self.btn_good, lambda: self._rate(RATING_GOOD))):
            b.setFixedWidth(148)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.clicked.connect(fn)
            rlay.addWidget(b)
        self.rate_row.hide()

        self.hint = widgets.caption("1 不认识 · 2 模糊 · 3 认识", "mist",
                                    align=Qt.AlignmentFlag.AlignHCenter)
        self.hint.hide()

        self.reveal_row = QWidget()
        rvl = hbox(12)
        rvl.setContentsMargins(0, 0, 0, 0)
        self.reveal_row.setLayout(rvl)
        self.btn_reveal = widgets.AnimButton("查看释义", "primary", 52, theme.R_CTRL)
        self.btn_reveal.setFixedWidth(168)
        self.btn_reveal.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_reveal.clicked.connect(self._reveal)
        self.btn_skip = widgets.AnimButton("跳过", "ghost", 52, theme.R_CTRL)
        self.btn_skip.setFixedWidth(96)
        self.btn_skip.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_skip.clicked.connect(self._skip)
        rvl.addStretch(1)
        rvl.addWidget(self.btn_skip)
        rvl.addWidget(self.btn_reveal)
        rvl.addStretch(1)

        alay.addWidget(self.hint)
        alay.addWidget(self.reveal_row, 0, Qt.AlignmentFlag.AlignHCenter)
        alay.addWidget(self.rate_row, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self.action_area, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch(1)

        self.stack.addWidget(view)

    def _build_done(self) -> None:
        view = QWidget()
        lay = QVBoxLayout(view)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addSpacing(40)
        lay.addWidget(page_header("本轮完成", "今天的词，收好了。", "记忆曲线已经帮你排好下一次复习。"))
        lay.addStretch(1)

        card = widgets.Card(padding=36)
        card.setFixedWidth(560)
        row = hbox(32)
        self.done_ring = widgets.ProgressRing(1.0, size=150, center="100%", subtitle="完成度")
        row.addWidget(self.done_ring, 0, Qt.AlignmentFlag.AlignVCenter)

        self.done_stats = vbox(12)
        row.addLayout(self.done_stats, 1)
        card.body().addLayout(row)
        lay.addWidget(card, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(28)

        buttons = hbox(12)
        again = widgets.AnimButton("再来一组", "primary", 50)
        again.setFixedWidth(148)
        again.clicked.connect(self.start)
        back = widgets.AnimButton("回到今日", "outline", 50)
        back.setFixedWidth(148)
        back.clicked.connect(lambda: self.ctx.navigate("today"))
        buttons.addStretch(1)
        buttons.addWidget(back)
        buttons.addWidget(again)
        buttons.addStretch(1)
        lay.addWidget(wrap(buttons), 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch(1)
        self.stack.addWidget(view)

    # ------------------------------------------------------------ 单卡

    def _current(self):
        if 0 <= self.index < len(self.queue):
            return self.queue[self.index]
        return None

    def _load_card(self) -> None:
        word = self._current()
        if word is None:
            self._show_done()
            return
        self.stack.setCurrentIndex(0)
        self.card.set_word(word, f"{self.index + 1} / {len(self.queue)}")
        self.rate_row.hide()
        self.reveal_row.show()
        self.hint.hide()
        self.hint.setText("1 不认识 · 2 模糊 · 3 认识")
        self.progress.set_value(self.index / max(1, len(self.queue)))

        # 更新页头（标题行在每次载入时重建文字）
        self._refresh_header()
        self.goal_chip.setText(f"今日目标 {self.store.daily_goal} 词")

    def _refresh_header(self) -> None:
        # 页头由 page_header 生成，这里仅替换标题与说明文本
        left = self.header.layout().itemAt(0).layout()
        title = left.itemAt(2).widget()
        sub = left.itemAt(4).widget() if left.count() > 4 else None
        if title is not None:
            title.setText(f"第 {min(self.index + 1, len(self.queue))} / {len(self.queue)} 张")
        if sub is not None:
            word = self._current()
            sub.setText(f"{word.level} · {word.theme} · {word.pos}" if word else "")

    def _reveal(self) -> None:
        if self._current() is None:
            return
        self.card.reveal()

    def _reveal_or_rate(self) -> None:
        if self.stack.currentIndex() == 0 and not self.card.is_revealed():
            self._reveal()

    def _on_flip(self, revealed: bool) -> None:
        if revealed:
            self.reveal_row.hide()
            self.rate_row.show()
            self.hint.show()
            word = self._current()
            if word and self.store.settings.get("tts", True):
                tts.speak(word.es)

    def _speak(self) -> None:
        word = self._current()
        if word:
            tts.speak(word.es)

    def _skip(self) -> None:
        if self.stack.currentIndex() != 0:
            return
        self.index += 1
        self._load_card()

    def _rate(self, rating: int) -> None:
        if self.stack.currentIndex() != 0:
            return
        word = self._current()
        if word is None:
            return
        if not self.card.is_revealed():
            self._reveal()
            return
        self.store.rate(word.id, rating)
        if rating == RATING_GOOD:
            self.stats["good"] += 1
        elif rating == RATING_HARD:
            self.stats["hard"] += 1
        else:
            self.stats["again"] += 1
        self.index += 1
        self._load_card()
        widgets.fade_in(self.card, 160)

    # ------------------------------------------------------------ 完成

    def _show_done(self) -> None:
        total = max(1, self.stats["good"] + self.stats["hard"] + self.stats["again"])
        widgets.clear_layout(self.done_stats)
        for label, value, tone in (
            ("认识", self.stats["good"], "ink"),
            ("模糊", self.stats["hard"], "ink"),
            ("不认识", self.stats["again"], "accent"),
        ):
            row = hbox(0)
            row.addWidget(widgets.body(label, "slate"), 1)
            row.addWidget(widgets.ThemedLabel(str(value), theme.H3, theme.W_SEMI, tone))
            self.done_stats.addWidget(wrap(row))
        acc = self.stats["good"] / total
        self.done_ring.set_value(acc, center=f"{round(acc * 100)}%", subtitle="一次记住")
        self.stack.setCurrentIndex(1)
        widgets.fade_in(self.stack.currentWidget(), 220)

    def _show_done_fallback(self) -> None:
        self._show_done()