"""统计每个页面切换时出现的顶层窗口数量（含闪烁窗口）。"""
from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app import theme  # noqa: E402
from app.main import MainWindow  # noqa: E402
from app.store import get_store  # noqa: E402

app = QApplication(sys.argv)
app.setStyleSheet(theme.qss())
store = get_store()
win = MainWindow(store)
win.resize(1320, 860)
win.show()
app.processEvents()


def count() -> Counter:
    return Counter(type(w).__name__ for w in QApplication.topLevelWidgets() if w.isVisible())


def run() -> None:
    results = {}
    for key in ("today", "study", "quiz", "library", "stats", "settings", "library"):
        peak = 0
        seen = Counter()
        win.navigate(key)
        for _ in range(160):
            c = count()
            peak = max(peak, sum(c.values()))
            seen.update(c)
            app.processEvents()
        results[key] = (peak, dict(seen))
        print(f"{key:9s} peak_windows={peak:3d}  {dict(seen)}")
    app.quit()


QTimer.singleShot(500, run)
app.exec()