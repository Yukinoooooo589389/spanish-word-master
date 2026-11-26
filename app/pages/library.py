"""词库页：搜索 + 等级/主题筛选 + 详情面板。"""
from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFrame, QListWidget, QListWidgetItem, QStyle,
    QStyledItemDelegate, QWidget,
)

from .. import theme, tts, widgets
from ..store import get_store
from ..theme import Theme, font
from .base import Page, hbox, page_header, vbox, wrap

BOX_LABEL = ["未开始", "第 1 层", "第 2 层", "第 3 层", "第 4 层", "已掌握"]


class WordDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index) -> QSize:
        return QSize(0, 62)

    def paint(self, painter: QPainter, option, index) -> None:
        word = index.data(Qt.ItemDataRole.UserRole)
        if word is None:
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        r = QRectF(option.rect).adjusted(2, 2, -6, -2)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hover = bool(option.state & QStyle.StateFlag.State_MouseOver)

        if selected:
            widgets.rounded(painter, r, 14, Theme.color("surface"), Theme.color("hairline"))
        elif hover:
            c = Theme.color("sunken")
            c.setAlphaF(0.75)
            widgets.rounded(painter, r, 14, c)

        painter.setFont(font(theme.EYEBROW, theme.W_SEMI, 0.6))
        painter.setPen(Theme.color("mist") if not selected else Theme.color("accent"))
        painter.drawText(QRectF(r.left() + 16, r.top(), 30, r.height()),
                         int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                         f"{index.row() + 1:02d}")

        painter.setFont(font(theme.BODY + 1, theme.W_SEMI, -0.1))
        painter.setPen(Theme.color("ink"))
        fm = QFontMetrics(painter.font())
        max_w = r.width() - 200
        es = fm.elidedText(word.es, Qt.TextElideMode.ElideRight, max_w)
        painter.drawText(QRectF(r.left() + 52, r.top() + 10, max_w, 20),
                         int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), es)

        painter.setFont(font(theme.CAPTION, theme.W_REGULAR, 0.1))
        painter.setPen(Theme.color("slate"))
        fm2 = QFontMetrics(painter.font())
        zh = fm2.elidedText(word.zh, Qt.TextElideMode.ElideRight, max_w)
        painter.drawText(QRectF(r.left() + 52, r.top() + 31, max_w, 18),
                         int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), zh)

        # 右侧：等级 + 掌握度
        painter.setFont(font(theme.EYEBROW, theme.W_SEMI, 0.4))
        painter.setPen(Theme.color("mist"))
        painter.drawText(QRectF(r.right() - 44, r.top(), 30, r.height()),
                         int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight), word.level)

        box = get_store().card(word.id).box
        for i in range(5):
            cx = r.right() - 78 + i * 9
            cy = r.center().y()
            filled = i < box
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(Theme.color("accent") if filled else Theme.color("hairline_strong"))
            painter.drawEllipse(QRectF(cx, cy - 2.5, 5, 5))
        painter.restore()


class Library(Page):
    key = "library"
    title = "词库"

    def __init__(self, ctx):
        super().__init__(ctx, scroll=False)
        self.level = "全部"
        self.theme_name = "全部"
        self.query = ""
        self.words: list = []
        self._updating = False
        self._build()

    def on_show(self) -> None:
        self._refresh_list()
        widgets.fade_in(self, 200)

    # ------------------------------------------------------------ 视图

    def _build(self) -> None:
        self.search = widgets.SearchField("搜索单词、释义或主题")
        self.search.setFixedWidth(260)
        self.search.textChanged.connect(self._on_search)
        self.root.addWidget(page_header(
            "词库", "全部词汇",
            f"{len(self.store.words)} 个词 · {len(self.store.themes)} 个主题",
            self.search,
        ))
        self.root.addSpacing(24)

        self.level_seg = widgets.Segmented(["全部", "A1", "A2", "B1"], 0)
        self.level_seg.changed.connect(self._on_level)
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("全部主题")
        for t in self.store.themes:
            self.theme_combo.addItem(t)
        self.theme_combo.setFixedHeight(36)
        self.theme_combo.setFixedWidth(132)
        self.theme_combo.currentTextChanged.connect(self._on_theme)

        self.count_label = widgets.caption("", "slate")
        filters = hbox(12)
        filters.addWidget(self.level_seg)
        filters.addWidget(self.theme_combo)
        filters.addStretch(1)
        filters.addWidget(self.count_label)
        self.root.addWidget(wrap(filters))
        self.root.addSpacing(18)

        body = hbox(24)
        self.list = QListWidget()
        self.list.setItemDelegate(WordDelegate(self.list))
        self.list.setMouseTracking(True)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list.setFrameShape(QFrame.Shape.NoFrame)
        self.list.setSpacing(0)
        self.list.currentRowChanged.connect(self._on_row_changed)
        list_card = widgets.Card(padding=8)
        list_card.body().addWidget(self.list)
        body.addWidget(list_card, 5)

        self.detail_card = widgets.Card(padding=28)
        self.detail_card.setFixedWidth(368)
        self.detail_box = vbox(0)
        self.detail_card.body().addLayout(self.detail_box)
        body.addWidget(self.detail_card, 0)
        self.root.addWidget(wrap(body), 1)

        self._refresh_list()

    # ------------------------------------------------------------ 筛选

    def _on_search(self, text: str) -> None:
        self.query = text
        self._refresh_list()

    def _on_level(self, index: int) -> None:
        self.level = ["全部", "A1", "A2", "B1"][index]
        self._refresh_list()

    def _on_theme(self, text: str) -> None:
        self.theme_name = "全部" if text in ("", "全部主题") else text
        self._refresh_list()

    def _refresh_list(self) -> None:
        self.words = self.store.search(self.query, self.level, self.theme_name)
        current = self.list.currentRow()
        self._updating = True
        self.list.clear()
        for w in self.words:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, w)
            self.list.addItem(item)
        if self.words:
            self.list.setCurrentRow(min(max(0, current), len(self.words) - 1))
        self._updating = False
        self.count_label.setText(f"{len(self.words)} 个词")
        self._refresh_detail()

    # ------------------------------------------------------------ 详情

    def _on_row_changed(self, row: int) -> None:
        if not getattr(self, "_updating", False):
            self._refresh_detail()

    def _refresh_detail(self) -> None:
        widgets.clear_layout(self.detail_box)
        row = self.list.currentRow()
        if row < 0 or row >= len(self.words):
            self.detail_box.addStretch(1)
            self.detail_box.addWidget(widgets.body("从左侧选择一个词。", "mist",
                                                   align=Qt.AlignmentFlag.AlignCenter))
            self.detail_box.addStretch(1)
            return

        w = self.words[row]
        card = self.store.card(w.id)

        chips = hbox(8)
        chips.addWidget(widgets.Chip(w.level, "sunken", "slate"))
        chips.addWidget(widgets.Chip(w.pos, "sunken", "slate"))
        chips.addWidget(widgets.Chip(w.theme, "sunken", "slate"))
        chips.addStretch(1)
        self.detail_box.addWidget(wrap(chips))
        self.detail_box.addSpacing(18)

        size = 30
        fm = QFontMetrics(font(size, theme.W_SEMI, -0.6))
        while fm.horizontalAdvance(w.es) > 300 and size > 18:
            size -= 2
            fm = QFontMetrics(font(size, theme.W_SEMI, -0.6))
        self.detail_box.addWidget(widgets.ThemedLabel(w.es, size, theme.W_SEMI, "ink", tracking=-0.6))
        self.detail_box.addSpacing(10)
        self.detail_box.addWidget(widgets.ThemedLabel(w.zh, theme.H3, theme.W_REGULAR, "ink2", wrap=True))

        speak = widgets.AnimButton("朗读", "ghost", 40, theme.R_CTRL, icon="speaker",
                                   icon_side="left", size=theme.BODY_S)
        speak.clicked.connect(lambda: tts.speak(w.es))
        self.detail_box.addSpacing(12)
        self.detail_box.addWidget(speak, 0, Qt.AlignmentFlag.AlignLeft)

        if w.ex_es:
            self.detail_box.addSpacing(20)
            self.detail_box.addWidget(widgets.Divider())
            self.detail_box.addSpacing(16)
            self.detail_box.addWidget(widgets.ThemedLabel(w.ex_es, theme.BODY_S, theme.W_REGULAR,
                                                          "ink2", wrap=True))
            self.detail_box.addSpacing(6)
            self.detail_box.addWidget(widgets.ThemedLabel(w.ex_zh, theme.CAPTION + 1, theme.W_REGULAR,
                                                          "slate", wrap=True))

        self.detail_box.addSpacing(20)
        self.detail_box.addWidget(widgets.Divider())
        self.detail_box.addSpacing(16)

        head = hbox(0)
        head.addWidget(widgets.caption("记忆层级", "slate"), 1)
        head.addWidget(widgets.caption(BOX_LABEL[min(card.box, 5)], "ink"))
        self.detail_box.addWidget(wrap(head))
        self.detail_box.addSpacing(10)
        self.detail_box.addWidget(widgets.MasteryDots(card.box, 6))
        self.detail_box.addSpacing(14)

        for label, value in (
            ("复习次数", f"{card.seen} 次"),
            ("记得 / 忘记", f"{card.correct} / {card.wrong}"),
            ("下次复习", card.due or "—"),
        ):
            r = hbox(0)
            r.addWidget(widgets.caption(label, "mist"), 1)
            r.addWidget(widgets.caption(value, "slate"))
            self.detail_box.addWidget(wrap(r))
            self.detail_box.addSpacing(6)

        self.detail_box.addStretch(1)
        later = widgets.AnimButton("加入今日复习", "primary", 44, theme.R_CTRL)
        later.clicked.connect(lambda: self._review_later(w.id))
        self.detail_box.addWidget(later)

    def _review_later(self, wid: str) -> None:
        self.store.review_later(wid)
        self.ctx.toast("已加入今日复习队列")
        self._refresh_detail()
        self.list.viewport().update()