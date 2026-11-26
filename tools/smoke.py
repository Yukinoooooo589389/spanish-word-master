"""冒烟测试：离屏构建全部页面，捕获异常并输出诊断。"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from app import theme  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(theme.qss())
    try:
        from app.main import MainWindow
        from app.store import get_store

        store = get_store()
        print(f"words={len(store.words)} themes={len(store.themes)}")
        win = MainWindow(store)
        win.resize(1320, 860)
        win.show()
        app.processEvents()
        for key in ("today", "study", "quiz", "library", "stats", "settings"):
            win.navigate(key)
            app.processEvents()
            print(f"  page ok: {key}")
        win.toggle_theme()
        app.processEvents()
        print("  theme ok: dark")
        win.navigate("today")
        app.processEvents()
        print("SMOKE OK")
        return 0
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())