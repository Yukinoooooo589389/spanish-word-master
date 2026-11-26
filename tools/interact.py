"""交互自测：把学习、测验、词库、设置的主流程各跑一遍。"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.gettempdir()) / "palabra_interact"
if TMP.exists():
    shutil.rmtree(TMP)
TMP.mkdir(parents=True)
os.environ["PALABRA_USER_DIR"] = str(TMP / "userdata")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from datetime import date  # noqa: E402
from app import theme  # noqa: E402
from app.main import MainWindow  # noqa: E402
from app.store import STATE_FILE, get_store  # noqa: E402

app = QApplication(sys.argv)
app.setStyleSheet(theme.qss())
store = get_store()
win = MainWindow(store)
win.resize(1320, 860)
win.show()
win.activateWindow()
win.raise_()
QTest.qWaitForWindowActive(win, 1000)
app.processEvents()

ok = []
fail = []


def check(name: str, cond: bool, extra: str = "") -> None:
    (ok if cond else fail).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f"  {extra}" if extra else ""))


# ---------------------------------------------------------------- 学习
win.navigate("study")
app.processEvents()
study = win.pages["study"]
check("学习队列非空", len(study.queue) > 0, f"{len(study.queue)} 张")
first = study.queue[0]
study._reveal()
app.processEvents()
check("翻面后显示评分", study.rate_row.isVisible())
QTest.keyClick(study, Qt.Key.Key_3)
app.processEvents()
check("评分后进入下一张", study.index == 1)
check("记忆层级提升", store.card(first.id).box >= 1, f"box={store.card(first.id).box}")
check("今日记录已写入", first.id in store.day_record()["studied"])

# 键盘翻面
QTest.keyClick(study, Qt.Key.Key_Space)
app.processEvents()
check("空格翻面", study.card.is_revealed())
QTest.keyClick(study, Qt.Key.Key_1)
app.processEvents()
check("按键 1 评分生效", study.index == 2)

# 一路走完
while study.stack.currentIndex() == 0 and study.index < len(study.queue):
    study._reveal()
    study._rate(3)
    app.processEvents()
check("整轮完成后显示结算", study.stack.currentIndex() == 1)

# ---------------------------------------------------------------- 测验
win.navigate("quiz")
app.processEvents()
quiz = win.pages["quiz"]
check("测验共 10 题", len(quiz.questions) == 10, f"{len(quiz.questions)}")
wrong = (quiz.correct_index + 1) % 4
quiz._answer(wrong)
app.processEvents()
check("答错后显示反馈", quiz.footer_host.isVisible())
check("答错会自动回到今日队列", store.card(quiz.target.id).due == date.today().isoformat(),
      store.card(quiz.target.id).due)
while not quiz.finished:
    quiz._answer(quiz.correct_index)
    app.processEvents()
    quiz._next()
    app.processEvents()
check("测验跑完进入结果页", quiz.finished and quiz.stack.currentIndex() == 1)

# ---------------------------------------------------------------- 词库
win.navigate("library")
app.processEvents()
lib = win.pages["library"]
total = len(lib.words)
lib.search.setText("casa")
app.processEvents()
check("搜索生效", 0 < len(lib.words) < total, f"{len(lib.words)} 条")
lib.search.setText("")
app.processEvents()
lib.level_seg.set_index(1)
app.processEvents()
check("等级筛选生效", all(w.level == "A1" for w in lib.words), f"{len(lib.words)} 条")
lib.level_seg.set_index(0)
lib.theme_combo.setCurrentIndex(1)
app.processEvents()
themes = {w.theme for w in lib.words}
check("主题筛选生效", len(themes) == 1, str(themes))
lib.theme_combo.setCurrentIndex(0)
app.processEvents()
lib.list.setCurrentRow(0)
app.processEvents()
check("详情面板有内容", lib.detail_box.count() > 3)
lib._review_later(lib.words[0].id)
app.processEvents()

# ---------------------------------------------------------------- 设置 / 主题
win.navigate("settings")
app.processEvents()
settings = win.pages["settings"]
settings._set_goal(2)
app.processEvents()
check("每日目标已保存", store.daily_goal == 30, f"{store.daily_goal}")
settings._toggle_tts(False)
check("朗读开关已保存", store.settings["tts"] is False)

mode_before = theme.Theme.mode
win.toggle_theme()
app.processEvents()
check("深浅切换生效", theme.Theme.mode != mode_before)
win.toggle_theme()
app.processEvents()

# 快捷键
QTest.keyClick(win, Qt.Key.Key_4, Qt.KeyboardModifier.ControlModifier)
app.processEvents()
check("Ctrl+4 跳到词库", win.stack.currentWidget() is win.pages["library"])

# 顶层窗口泄漏检查：曾经因为 clear_layout 里直接 setParent(None)，
# 可见控件短暂变成顶层窗口，于是点「词库」时闪出大量小窗。
leaks = []
for key in ("today", "library", "stats", "settings", "library", "today"):
    win.navigate(key)
    for _ in range(80):
        app.processEvents()
        extra = [w for w in QApplication.topLevelWidgets() if w.isVisible() and w is not win]
        if extra:
            leaks.append((key, [type(w).__name__ for w in extra]))
            break
check("页面切换不再产生多余弹窗", not leaks, str(leaks[:2]))

# ---------------------------------------------------------------- 持久化
store.save()
data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
check("状态文件可解析", isinstance(data.get("cards"), dict), f"{len(data['cards'])} 张卡")
check("设置已落盘", data["settings"]["daily_goal"] == 30)

print(f"\n通过 {len(ok)} 项，失败 {len(fail)} 项")
if fail:
    print("失败项：", fail)
app.quit()
raise SystemExit(1 if fail else 0)