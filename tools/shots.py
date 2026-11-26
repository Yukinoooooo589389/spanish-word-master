"""生成高保真截图：用临时 userdata 目录，避免污染真实进度。"""
from __future__ import annotations

import os
import random
import shutil
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.gettempdir()) / "palabra_shots"
if TMP.exists():
    shutil.rmtree(TMP)
TMP.mkdir(parents=True)
os.environ["PALABRA_USER_DIR"] = str(TMP / "userdata")

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app import theme  # noqa: E402
from app.main import MainWindow  # noqa: E402
from app.store import get_store  # noqa: E402

random.seed(7)


def seed(store) -> None:
    words = store.words
    today = date.today()
    for i, w in enumerate(words[:96]):
        card = store.card(w.id)
        card.seen = random.randint(1, 4)
        card.box = min(5, (i // 18) + random.randint(0, 1))
        card.correct = random.randint(1, 5)
        card.wrong = random.randint(0, 2)
        card.last = (today - timedelta(days=random.randint(0, 5))).isoformat()
        card.due = (today + timedelta(days=random.randint(0, 6))).isoformat()
    for d in range(1, 14):
        day = (today - timedelta(days=d)).isoformat()
        if random.random() < 0.82:
            n = random.randint(6, 22)
            pool = [w.id for w in words[:96]]
            store.history[day] = {
                "studied": random.sample(pool, min(n, len(pool))),
                "correct": n - random.randint(0, 4),
                "wrong": random.randint(0, 4),
            }
    store.history[today.isoformat()] = {
        "studied": [w.id for w in words[:8]],
        "correct": 7,
        "wrong": 1,
    }
    store.save()


app = QApplication(sys.argv)
store = get_store()
seed(store)
app.setStyleSheet(theme.qss())
win = MainWindow(store)
win.resize(1320, 860)
win.show()

OUT = ROOT / "shots"
OUT.mkdir(exist_ok=True)

steps: list[tuple[str, callable]] = []


def go_today():
    win.navigate("today")


def go_study():
    win.navigate("study")
    page = win.pages["study"]
    page.card.reveal()


def go_study_front():
    win.navigate("study")


def go_quiz():
    win.navigate("quiz")
    page = win.pages["quiz"]
    page._answer(page.correct_index)


def go_study_done():
    win.navigate("study")
    page = win.pages["study"]
    while page.stack.currentIndex() == 0 and page.index < len(page.queue):
        page._reveal()
        page._rate(3)
        app.processEvents()


def go_quiz_result():
    win.navigate("quiz")
    page = win.pages["quiz"]
    while not page.finished:
        page._answer(page.correct_index)
        app.processEvents()
        page._next()
        app.processEvents()


def go_library():
    win.navigate("library")
    page = win.pages["library"]
    page.list.setCurrentRow(3)


def go_stats():
    win.navigate("stats")


def go_settings():
    win.navigate("settings")


def go_dark():
    win.navigate("today")
    if theme.Theme.mode != "dark":
        win.toggle_theme()


actions = [
    ("01-today", go_today),
    ("02-study", go_study),
    ("02b-study-front", go_study_front),
    ("02c-study-done", go_study_done),
    ("03-quiz", go_quiz),
    ("03b-quiz-result", go_quiz_result),
    ("04-library", go_library),
    ("05-stats", go_stats),
    ("06-settings", go_settings),
    ("07-today-dark", go_dark),
]

idx = 0


def shoot():
    global idx
    if idx >= len(actions):
        print("shots done")
        app.quit()
        return
    name, fn = actions[idx]
    fn()
    app.processEvents()

    def grab():
        global idx
        win.grab().save(str(OUT / f"{name}.png"))
        print("saved", name)
        idx += 1
        QTimer.singleShot(120, shoot)

    QTimer.singleShot(700, grab)


QTimer.singleShot(600, shoot)
app.exec()