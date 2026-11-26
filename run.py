"""Palabra · 背西班牙语单词。

启动：python run.py
自检：python run.py --selftest   （打印词库/数据路径，不开窗口）
"""
from __future__ import annotations

import sys
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))
if not FROZEN:
    ROOT = Path(__file__).resolve().parent
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app import theme  # noqa: E402
from app.main import MainWindow  # noqa: E402
from app.store import APP_ROOT, DATA_DIR, USER_DIR, get_store  # noqa: E402


def selftest() -> int:
    store = get_store()
    lines = [
        f"frozen   = {FROZEN}",
        f"data_dir = {DATA_DIR}",
        f"user_dir = {USER_DIR}",
        f"words    = {len(store.words)}",
        f"themes   = {len(store.themes)}",
        f"levels   = {sorted({w.level for w in store.words})}",
        f"sample   = {store.words[0].es} / {store.words[0].zh}",
    ]
    ok = len(store.words) >= 100 and len(store.themes) >= 5
    lines.append("SELFTEST OK" if ok else "SELFTEST FAILED: 词库未正确打包")
    # 打包成 windowed exe 后没有控制台，同时写一份日志方便排查
    try:
        print("\n".join(lines))
    except Exception:
        pass
    try:
        (APP_ROOT / "selftest.log").write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Palabra")
    app.setApplicationDisplayName("Palabra · 背西班牙语单词")

    store = get_store()
    theme.Theme.mode = "dark" if store.settings.get("theme") == "dark" else "light"
    app.setStyleSheet(theme.qss())

    window = MainWindow(store)

    # 按屏幕可用区域自适应，并居中显示
    screen = window.screen()
    if screen is not None:
        avail = screen.availableGeometry()
        window.resize(min(1320, max(1080, avail.width() - 40)),
                      min(860, max(720, avail.height() - 40)))
        frame = window.frameGeometry()
        frame.moveCenter(avail.center())
        window.move(frame.topLeft())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())