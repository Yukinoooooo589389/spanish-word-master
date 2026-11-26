"""设置页：目标、外观、数据。所有改动即时生效并落盘。"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from .. import theme, widgets
from ..store import STATE_FILE, USER_DIR
from .base import Page, hbox, page_header, vbox, wrap

GOALS = [10, 20, 30, 50]


class Settings(Page):
    key = "settings"
    title = "设置"

    def __init__(self, ctx):
        super().__init__(ctx)
        self._reset_confirming = False
        self.build()

    def on_show(self) -> None:
        self.build()
        widgets.fade_in(self, 200)

    # ------------------------------------------------------------ 构建

    def build(self) -> None:
        widgets.clear_layout(self.root)
        self.root.addWidget(page_header("偏好", "设置", "改动会立刻保存，不需要确认按钮。"))
        self.root.addSpacing(24)

        column = vbox(14)
        column.addWidget(self._goal_card())
        column.addWidget(self._appearance_card())
        column.addWidget(self._data_card())
        column.addWidget(self._about_card())

        holder = wrap(column)
        holder.setMaximumWidth(760)
        self.root.addWidget(holder, 0, Qt.AlignmentFlag.AlignLeft)
        self.root.addStretch(1)

    def _row(self, title: str, desc: str, control: QWidget) -> QWidget:
        left = vbox(4)
        left.addWidget(widgets.ThemedLabel(title, theme.BODY + 1, theme.W_MEDIUM, "ink"))
        left.addWidget(widgets.caption(desc, "slate"))
        row = hbox(24)
        row.addLayout(left, 1)
        row.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)
        return wrap(row)

    def _goal_card(self) -> QWidget:
        card = widgets.Card(padding=22)
        seg = widgets.Segmented([str(g) for g in GOALS], GOALS.index(self.store.daily_goal)
                                if self.store.daily_goal in GOALS else 1, 36)
        seg.changed.connect(self._set_goal)
        card.body().addWidget(self._row(
            "每日目标", "每天自动排入队列的词数，复习词优先。", seg))
        return card

    def _appearance_card(self) -> QWidget:
        card = widgets.Card(padding=22)
        dark = widgets.Switch(theme.Theme.mode == "dark")
        dark.toggled.connect(self._toggle_dark)
        card.body().addWidget(self._row("深色外观", "黑白两套主题，跟随你的环境光。", dark))
        card.body().addSpacing(16)
        card.body().addWidget(widgets.Divider())
        card.body().addSpacing(16)
        speak = widgets.Switch(bool(self.store.settings.get("tts", True)))
        speak.toggled.connect(self._toggle_tts)
        card.body().addWidget(self._row("翻面后朗读", "使用系统西班牙语语音朗读单词。", speak))
        return card

    def _data_card(self) -> QWidget:
        card = widgets.Card(padding=22)
        info = vbox(4)
        info.addWidget(widgets.ThemedLabel("本地数据", theme.BODY + 1, theme.W_MEDIUM, "ink"))
        info.addWidget(widgets.caption(str(STATE_FILE), "mist"))
        open_btn = widgets.AnimButton("打开目录", "outline", 40, theme.R_CTRL, size=theme.BODY_S)
        open_btn.clicked.connect(self._open_dir)
        row = hbox(24)
        row.addLayout(info, 1)
        row.addWidget(open_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        card.body().addWidget(wrap(row))
        card.body().addSpacing(16)
        card.body().addWidget(widgets.Divider())
        card.body().addSpacing(16)

        self.reset_btn = widgets.AnimButton("重置学习进度", "danger", 40, theme.R_CTRL,
                                            size=theme.BODY_S)
        self.reset_btn.clicked.connect(self._reset_clicked)
        row2 = hbox(24)
        desc = vbox(4)
        desc.addWidget(widgets.ThemedLabel("重置进度", theme.BODY + 1, theme.W_MEDIUM, "ink"))
        desc.addWidget(widgets.caption("清空记忆层级与历史记录，词库不会删除。", "slate"))
        row2.addLayout(desc, 1)
        row2.addWidget(self.reset_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        card.body().addWidget(wrap(row2))
        return card

    def _about_card(self) -> QWidget:
        card = widgets.Card(padding=22, fill="surface2")
        card.body().addWidget(widgets.eyebrow("关于"))
        card.body().addSpacing(9)
        card.body().addWidget(widgets.h3("Palabra · 背西班牙语单词"))
        card.body().addSpacing(5)
        card.body().addWidget(widgets.caption(
            f"版本 1.0 · 词库 {len(self.store.words)} 词 · PySide6 / Python 3", "slate"))
        card.body().addSpacing(9)
        card.body().addWidget(widgets.ThemedLabel(
            "黑白灰 + 单一强调色，遵循 DESIGN_SYSTEM.md。复习调度为 Leitner 分层，"
            "间隔 1 / 2 / 4 / 7 / 15 / 30 天。", theme.CAPTION + 1, theme.W_REGULAR, "slate",
            wrap=True))
        return card

    # ------------------------------------------------------------ 行为

    def _set_goal(self, index: int) -> None:
        self.store.set_setting("daily_goal", GOALS[index])
        self.ctx.toast(f"每日目标已设为 {GOALS[index]} 词")

    def _toggle_dark(self, checked: bool) -> None:
        self.store.set_setting("theme", "dark" if checked else "light")
        self.ctx.refresh_theme()

    def _toggle_tts(self, checked: bool) -> None:
        self.store.set_setting("tts", checked)

    def _open_dir(self) -> None:
        try:
            USER_DIR.mkdir(parents=True, exist_ok=True)
            os.startfile(str(USER_DIR))  # type: ignore[attr-defined]
        except Exception:
            self.ctx.toast("目录暂时打不开")

    def _reset_clicked(self) -> None:
        if not self._reset_confirming:
            self._reset_confirming = True
            self.reset_btn.setText("再次点击确认")
            self.ctx.toast("再次点击将清空全部学习进度")
            return
        self._reset_confirming = False
        self.reset_btn.setText("重置学习进度")
        self.store.reset()
        self.ctx.toast("进度已重置")