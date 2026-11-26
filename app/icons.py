"""线性矢量图标：全部由 QPainter 现画，不依赖任何图片资源或第三方图标库。

坐标系固定 24×24，描边 1.6（视觉重量对齐 16px 文本）。
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap


def _pen(color: QColor, w: float) -> QPen:
    pen = QPen(color, w)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _today(p: QPainter) -> None:
    p.drawEllipse(QPointF(12, 12), 4.2, 4.2)
    for a in range(8):
        p.save()
        p.translate(12, 12)
        p.rotate(45 * a)
        p.drawLine(QPointF(0, -7.6), QPointF(0, -9.4))
        p.restore()


def _study(p: QPainter) -> None:
    path = QPainterPath()
    path.addRoundedRect(QRectF(3.5, 6.5, 13, 13), 3, 3)
    p.drawPath(path)
    p.drawLine(QPointF(7.5, 6.5), QPointF(17.0, 6.5))
    p.drawLine(QPointF(8.5, 3.5), QPointF(16.2, 3.5))


def _quiz(p: QPainter) -> None:
    p.drawEllipse(QPointF(12, 12), 8.4, 8.4)
    p.drawPolyline([QPointF(8.2, 12.4), QPointF(11.0, 15.1), QPointF(16.0, 9.4)])


def _library(p: QPainter) -> None:
    path = QPainterPath()
    path.addRoundedRect(QRectF(4.2, 4.0, 15.6, 16.0), 2.6, 2.6)
    p.drawPath(path)
    p.drawLine(QPointF(8.4, 4.0), QPointF(8.4, 20.0))
    p.drawLine(QPointF(12.2, 8.6), QPointF(16.2, 8.6))
    p.drawLine(QPointF(12.2, 12.0), QPointF(16.2, 12.0))


def _stats(p: QPainter) -> None:
    p.drawLine(QPointF(4.2, 19.6), QPointF(19.8, 19.6))
    p.drawLine(QPointF(7.6, 19.6), QPointF(7.6, 13.4))
    p.drawLine(QPointF(12.0, 19.6), QPointF(12.0, 7.6))
    p.drawLine(QPointF(16.4, 19.6), QPointF(16.4, 10.8))


def _settings(p: QPainter) -> None:
    for y, x in ((7.2, 9.0), (12.0, 15.0), (16.8, 8.0)):
        p.drawLine(QPointF(3.6, y), QPointF(20.4, y))
        p.save()
        p.setBrush(p.pen().color())
        p.drawEllipse(QPointF(x, y), 2.1, 2.1)
        p.restore()


def _speaker(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(4.2, 9.4)
    path.lineTo(7.6, 9.4)
    path.lineTo(11.6, 5.6)
    path.lineTo(11.6, 18.4)
    path.lineTo(7.6, 14.6)
    path.lineTo(4.2, 14.6)
    path.closeSubpath()
    p.drawPath(path)
    p.drawArc(QRectF(11.0, 7.6, 7.4, 8.8), -55 * 16, 110 * 16)
    p.drawArc(QRectF(12.6, 5.4, 8.6, 13.2), -52 * 16, 104 * 16)


def _search(p: QPainter) -> None:
    p.drawEllipse(QPointF(10.8, 10.8), 6.4, 6.4)
    p.drawLine(QPointF(15.6, 15.6), QPointF(20.2, 20.2))


def _close(p: QPainter) -> None:
    p.drawLine(QPointF(7.2, 7.2), QPointF(16.8, 16.8))
    p.drawLine(QPointF(16.8, 7.2), QPointF(7.2, 16.8))


def _minimize(p: QPainter) -> None:
    p.drawLine(QPointF(6.8, 12.0), QPointF(17.2, 12.0))


def _maximize(p: QPainter) -> None:
    path = QPainterPath()
    path.addRoundedRect(QRectF(6.8, 6.8, 10.4, 10.4), 2.2, 2.2)
    p.drawPath(path)


def _restore(p: QPainter) -> None:
    path = QPainterPath()
    path.addRoundedRect(QRectF(5.6, 8.4, 9.2, 9.2), 2.0, 2.0)
    p.drawPath(path)
    p.drawLine(QPointF(9.0, 8.0), QPointF(9.0, 6.6))
    p.drawLine(QPointF(9.0, 6.6), QPointF(18.2, 6.6))
    p.drawLine(QPointF(18.2, 6.6), QPointF(18.2, 15.6))


def _arrow_left(p: QPainter) -> None:
    p.drawPolyline([QPointF(14.4, 5.6), QPointF(8.2, 12.0), QPointF(14.4, 18.4)])


def _arrow_right(p: QPainter) -> None:
    p.drawPolyline([QPointF(9.6, 5.6), QPointF(15.8, 12.0), QPointF(9.6, 18.4)])


def _chevron_down(p: QPainter) -> None:
    p.drawPolyline([QPointF(6.6, 9.6), QPointF(12.0, 15.0), QPointF(17.4, 9.6)])


def _sun(p: QPainter) -> None:
    _today(p)


def _moon(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(15.4, 4.6)
    path.arcTo(QRectF(4.6, 4.6, 14.8, 14.8), 62, 250)
    path.closeSubpath()
    p.drawPath(path)


def _check(p: QPainter) -> None:
    p.drawPolyline([QPointF(5.6, 12.4), QPointF(10.0, 16.8), QPointF(18.4, 7.6)])


def _plus(p: QPainter) -> None:
    p.drawLine(QPointF(12.0, 5.6), QPointF(12.0, 18.4))
    p.drawLine(QPointF(5.6, 12.0), QPointF(18.4, 12.0))


def _flame(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(12.0, 3.6)
    path.cubicTo(15.6, 8.0, 18.6, 10.4, 18.6, 14.2)
    path.cubicTo(18.6, 17.9, 15.6, 20.4, 12.0, 20.4)
    path.cubicTo(8.4, 20.4, 5.4, 17.9, 5.4, 14.2)
    path.cubicTo(5.4, 11.4, 7.2, 9.6, 9.0, 7.2)
    path.cubicTo(9.6, 9.2, 10.6, 10.2, 12.0, 11.4)
    path.cubicTo(12.4, 8.6, 12.4, 6.0, 12.0, 3.6)
    p.drawPath(path)


def _target(p: QPainter) -> None:
    p.drawEllipse(QPointF(12, 12), 8.4, 8.4)
    p.drawEllipse(QPointF(12, 12), 4.4, 4.4)
    p.drawEllipse(QPointF(12, 12), 0.9, 0.9)


def _refresh(p: QPainter) -> None:
    p.drawArc(QRectF(4.6, 4.6, 14.8, 14.8), 40 * 16, 280 * 16)
    p.drawPolyline([QPointF(15.8, 3.6), QPointF(18.8, 6.6), QPointF(15.4, 8.4)])


def _trash(p: QPainter) -> None:
    p.drawLine(QPointF(4.8, 7.2), QPointF(19.2, 7.2))
    p.drawLine(QPointF(9.6, 7.2), QPointF(9.6, 4.8))
    p.drawLine(QPointF(9.6, 4.8), QPointF(14.4, 4.8))
    p.drawLine(QPointF(14.4, 4.8), QPointF(14.4, 7.2))
    path = QPainterPath()
    path.moveTo(6.6, 7.2)
    path.lineTo(7.8, 19.2)
    path.lineTo(16.2, 19.2)
    path.lineTo(17.4, 7.2)
    p.drawPath(path)


def _info(p: QPainter) -> None:
    p.drawEllipse(QPointF(12, 12), 8.4, 8.4)
    p.drawLine(QPointF(12.0, 11.0), QPointF(12.0, 16.4))
    p.drawPoint(QPointF(12.0, 8.2))


_DRAW = {
    "today": _today,
    "study": _study,
    "quiz": _quiz,
    "library": _library,
    "stats": _stats,
    "settings": _settings,
    "speaker": _speaker,
    "search": _search,
    "close": _close,
    "minimize": _minimize,
    "maximize": _maximize,
    "restore": _restore,
    "arrow_left": _arrow_left,
    "arrow_right": _arrow_right,
    "chevron_down": _chevron_down,
    "sun": _sun,
    "moon": _moon,
    "check": _check,
    "plus": _plus,
    "flame": _flame,
    "target": _target,
    "refresh": _refresh,
    "trash": _trash,
    "info": _info,
}


def paint(p: QPainter, name: str, rect: QRectF, color: QColor, stroke: float = 1.6) -> None:
    fn = _DRAW.get(name)
    if fn is None:
        return
    size = min(rect.width(), rect.height())
    if size <= 1:
        return
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_pen(color, stroke))
    p.translate(rect.center())
    p.scale(size / 24.0, size / 24.0)
    p.translate(-12.0, -12.0)
    fn(p)
    p.restore()


def pixmap(name: str, size: int, color: QColor, stroke: float = 1.6, ratio: float = 2.0) -> QPixmap:
    pm = QPixmap(int(size * ratio), int(size * ratio))
    pm.setDevicePixelRatio(ratio)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    paint(p, name, QRectF(0, 0, size, size), color, stroke)
    p.end()
    return pm