"""测验页：四选一，答完立刻给例句与解释，节奏由用户控制。

版面刻意拆成「题卡 + 卡外反馈」：题卡高度稳定，反馈在下方淡入，
翻页时画面不会跳动。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from .. import theme, tts, widgets
from .base import Page, hbox, page_header, vbox, wrap

LETTERS = ["A", "B", "C", "D"]


class Quiz(Page):
    key = "quiz"
    title = "测验"

    def __init__(self, ctx):
        super().__init__(ctx)
        self.questions: list = []
        self.index = 0
        self.score = 0
        self.answered = False
        self.correct_index = -1
        self.started = False
        self.finished = False
        self.rows: list[widgets.OptionRow] = []
        self.target = None
        self.shortcuts = []

        self.stack = QStackedWidget()
        self.root.addWidget(self.stack, 1)
        self._build_question_view()
        self._build_result_view()

        for key, fn in (
            ("1", lambda: self._answer(0)),
            ("2", lambda: self._answer(1)),
            ("3", lambda: self._answer(2)),
            ("4", lambda: self._answer(3)),
            ("Return", self._next),
            ("Space", self._next),
        ):
            sc = QShortcut(QKeySequence(key), self)
            sc.setContext(Qt.ShortcutContext.WindowShortcut)
            sc.activated.connect(fn)
            sc.setEnabled(False)
            self.shortcuts.append(sc)

    # ------------------------------------------------------------ 生命周期

    def start(self) -> None:
        self.questions = self.store.build_quiz(10)
        self.index = 0
        self.score = 0
        self.started = True
        self.finished = False
        self.stack.setCurrentIndex(0)
        self._load_question()

    def on_show(self) -> None:
        if not self.started or self.finished:
            self.start()
        widgets.fade_in(self, 200)

    # ------------------------------------------------------------ 视图

    def _build_question_view(self) -> None:
        view = QWidget()
        lay = QVBoxLayout(view)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        quit_btn = widgets.AnimButton("退出测验", "ghost", 40, theme.R_CTRL)
        quit_btn.clicked.connect(lambda: self.ctx.navigate("today"))
        right = wrap(hbox(0))
        right.layout().addWidget(quit_btn, 0, Qt.AlignmentFlag.AlignTop)

        self.q_header = page_header("测验", "", "选出正确的中文释义", right)
        lay.addWidget(self.q_header)
        lay.addSpacing(14)

        self.q_progress = widgets.ProgressBar(0.0, 3)
        lay.addWidget(self.q_progress)
        lay.addSpacing(16)

        card = widgets.Card(padding=26)
        card.setFixedWidth(660)
        self.eyebrow = widgets.eyebrow("A1 · 生活")
        card.body().addWidget(self.eyebrow)
        card.body().addSpacing(12)
        self.word_label = widgets.ThemedLabel("", 36, theme.W_SEMI, "ink", tracking=-0.8)
        card.body().addWidget(self.word_label)
        card.body().addSpacing(8)
        self.chip_row = wrap(hbox(8))
        card.body().addWidget(self.chip_row)
        card.body().addSpacing(16)
        card.body().addWidget(widgets.Divider())
        card.body().addSpacing(16)
        self.options_box = vbox(8)
        card.body().addLayout(self.options_box)

        holder = wrap(hbox(0))
        holder.layout().addStretch(1)
        holder.layout().addWidget(card)
        holder.layout().addStretch(1)
        lay.addWidget(holder)

        # 卡外反馈区
        self.footer_host = QWidget()
        self.footer_host.setFixedWidth(660)
        self.footer_box = vbox(10)
        self.footer_host.setLayout(self.footer_box)
        fh = wrap(hbox(0))
        fh.layout().addStretch(1)
        fh.layout().addWidget(self.footer_host)
        fh.layout().addStretch(1)
        lay.addSpacing(18)
        lay.addWidget(fh)
        lay.addStretch(1)
        self.footer_host.hide()

        self.stack.addWidget(view)

    def _build_result_view(self) -> None:
        view = QWidget()
        lay = QVBoxLayout(view)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(page_header("测验结果", "这一轮结束了。", "错的词已经自动回到今日队列。"))
        lay.addStretch(1)

        card = widgets.Card(padding=36)
        card.setFixedWidth(560)
        row = hbox(32)
        self.result_ring = widgets.ProgressRing(0.0, size=150, center="0%", subtitle="正确率")
        row.addWidget(self.result_ring, 0, Qt.AlignmentFlag.AlignVCenter)
        self.result_stats = vbox(14)
        row.addLayout(self.result_stats, 1)
        card.body().addLayout(row)
        lay.addWidget(card, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(26)

        buttons = hbox(12)
        back = widgets.AnimButton("回到今日", "outline", 50)
        back.setFixedWidth(148)
        back.clicked.connect(lambda: self.ctx.navigate("today"))
        again = widgets.AnimButton("再测一次", "primary", 50)
        again.setFixedWidth(148)
        again.clicked.connect(self.start)
        buttons.addStretch(1)
        buttons.addWidget(back)
        buttons.addWidget(again)
        buttons.addStretch(1)
        lay.addWidget(wrap(buttons), 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch(1)
        self.stack.addWidget(view)

    # ------------------------------------------------------------ 单题

    def _load_question(self) -> None:
        widgets.clear_layout(self.options_box)
        widgets.clear_layout(self.footer_box)
        self.footer_host.hide()
        self.rows = []
        self.answered = False

        if not self.questions or self.index >= len(self.questions):
            self._show_result()
            return

        target, options = self.questions[self.index]
        self.target = target
        self.options = options
        self.correct_index = next(i for i, w in enumerate(options) if w.id == target.id)

        self.eyebrow.setText(f"第 {self.index + 1} 题 · {target.level} · {target.theme}")
        self.word_label.setText(target.es)

        chip_layout = self.chip_row.layout()
        widgets.clear_layout(chip_layout)
        chip_layout.addWidget(widgets.Chip(target.pos, "sunken", "slate"))
        chip_layout.addWidget(widgets.Chip(target.theme, "sunken", "slate"))
        chip_layout.addStretch(1)

        for i, w in enumerate(options):
            row = widgets.OptionRow(LETTERS[i], w.zh)
            row.clicked.connect(lambda _=False, idx=i: self._answer(idx))
            row.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.rows.append(row)
            self.options_box.addWidget(row)

        total = len(self.questions)
        left = self.q_header.layout().itemAt(0).layout()
        if left.count() > 2:
            left.itemAt(2).widget().setText(f"第 {self.index + 1} 题 / 共 {total} 题")
        self.q_progress.set_value(self.index / max(1, total))

    def _answer(self, idx: int) -> None:
        if self.answered or not self.rows or idx >= len(self.rows):
            return
        self.answered = True
        correct = idx == self.correct_index
        if correct:
            self.score += 1

        for i, row in enumerate(self.rows):
            if i == self.correct_index:
                row.set_state("correct")
            elif i == idx:
                row.set_state("wrong")
            else:
                row.set_state("muted")

        # 答错 → 立刻回到今日队列，交给记忆曲线
        if not correct:
            self.store.review_later(self.target.id)

        self._build_footer(correct)

    def _build_footer(self, correct: bool) -> None:
        widgets.clear_layout(self.footer_box)
        verdict = hbox(10)
        verdict.addWidget(widgets.ThemedLabel(
            "答对了" if correct else "再看一遍",
            theme.BODY_S, theme.W_SEMI, "accent" if not correct else "ink"))
        verdict.addWidget(widgets.caption(self.target.zh, "slate"))
        verdict.addStretch(1)
        speak_btn = widgets.IconButton("speaker", 32, 17, "slate")
        speak_btn.setToolTip("朗读单词")
        speak_btn.clicked.connect(lambda: tts.speak(self.target.es))
        verdict.addWidget(speak_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        last = self.index + 1 >= len(self.questions)
        nxt = widgets.AnimButton("查看结果" if last else "下一题", "primary", 44, theme.R_CTRL,
                                 icon="arrow_right", size=theme.BODY_S)
        nxt.clicked.connect(self._next)
        verdict.addWidget(nxt, 0, Qt.AlignmentFlag.AlignVCenter)
        self.footer_box.addWidget(wrap(verdict))

        if self.target.ex_es:
            self.footer_box.addWidget(widgets.ThemedLabel(
                self.target.ex_es, theme.BODY_S, theme.W_REGULAR, "ink2", wrap=True))
            self.footer_box.addWidget(widgets.ThemedLabel(
                self.target.ex_zh, theme.CAPTION + 1, theme.W_REGULAR, "slate", wrap=True))

        self.footer_host.show()
        widgets.fade_in(self.footer_host, 200)

    def _next(self) -> None:
        if not self.answered:
            return
        self.index += 1
        if self.index >= len(self.questions):
            self._show_result()
        else:
            self._load_question()
            widgets.fade_in(self.stack.currentWidget(), 160)

    # ------------------------------------------------------------ 结果

    def _show_result(self) -> None:
        self.finished = True
        total = max(1, len(self.questions))
        ratio = self.score / total
        widgets.clear_layout(self.result_stats)
        wrong_count = total - self.score
        for label, value, tone in (
            ("答对", f"{self.score} 题", "ink"),
            ("答错", f"{wrong_count} 题", "accent" if wrong_count else "slate"),
            ("本轮题量", f"{total} 题", "ink"),
        ):
            row = hbox(0)
            row.addWidget(widgets.body(label, "slate"), 1)
            row.addWidget(widgets.ThemedLabel(value, theme.H3, theme.W_SEMI, tone))
            self.result_stats.addWidget(wrap(row))
        self.result_ring.set_value(ratio, center=f"{round(ratio * 100)}%", subtitle="正确率")
        self.stack.setCurrentIndex(1)
        widgets.fade_in(self.stack.currentWidget(), 220)