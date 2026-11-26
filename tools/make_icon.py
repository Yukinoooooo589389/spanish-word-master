"""生成应用图标 build/palabra.ico（黑底 + 白色 P，无外部素材）。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication(sys.argv)
out = ROOT / "build"
out.mkdir(exist_ok=True)

sizes = [16, 24, 32, 48, 64, 128, 256]
images = []
for size in sizes:
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    radius = size * 0.22
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#0B0B0C"))
    p.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)
    f = QFont()
    f.setFamilies(["Segoe UI", "Arial"])
    f.setPixelSize(int(size * 0.62))
    f.setWeight(QFont.Weight.DemiBold)
    p.setFont(f)
    p.setPen(QColor("#F5F5F7"))
    p.drawText(QRectF(0, -size * 0.03, size, size), int(Qt.AlignmentFlag.AlignCenter), "P")
    # 强调色小点，呼应界面里的品牌句号
    p.setBrush(QColor("#C8362B"))
    d = max(2.0, size * 0.075)
    p.drawEllipse(QRectF(size * 0.68, size * 0.66, d, d))
    p.end()
    images.append(img)

# Qt 的 ICO 写入插件只接受单一尺寸，这里手工拼多尺寸 ICO
import struct  # noqa: E402

blobs = []
for img in images:
    path = out / f"_icon_{img.width()}.png"
    img.save(str(path), "PNG")
    blobs.append((img.width(), path.read_bytes()))

header = struct.pack("<HHH", 0, 1, len(blobs))
entries = b""
data = b""
offset = 6 + 16 * len(blobs)
for size, blob in blobs:
    b = 0 if size >= 256 else size
    entries += struct.pack("<BBBBHHII", b, b, 0, 0, 1, 32, len(blob), offset + len(data))
    data += blob

ico = out / "palabra.ico"
ico.write_bytes(header + entries + data)

for size, _ in blobs:
    (out / f"_icon_{size}.png").unlink(missing_ok=True)

print(f"icon: {ico} ({ico.stat().st_size} bytes, {len(blobs)} sizes)")
app.quit()