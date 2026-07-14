"""Annotation graphics items — camera marker, direction arrow, viewing cone, visible area."""

from __future__ import annotations

import math
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPen, QPolygonF
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
    QGraphicsItemGroup,
)

# Z-ordering constants
Z_AREA = 1
Z_CONE = 2
Z_ARROW = 3
Z_MARKER = 4


class CameraMarkerItem(QGraphicsEllipseItem):
    """Red circle marking camera position on a plan.

    Movable, selectable, and emits positionChanged when dragged.
    """

    positionChanged = Signal(float, float)

    MARKER_RADIUS = 8.0

    def __init__(self, x: float = 0.0, y: float = 0.0, parent=None):
        super().__init__(
            -self.MARKER_RADIUS,
            -self.MARKER_RADIUS,
            self.MARKER_RADIUS * 2,
            self.MARKER_RADIUS * 2,
            parent,
        )
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(220, 40, 40)))
        self.setPen(QPen(QColor(160, 20, 20), 1.5))
        self.setZValue(Z_MARKER)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionHasChanged:
            pos = self.pos()
            self.positionChanged.emit(pos.x(), pos.y())
        return super().itemChange(change, value)


class DirectionArrowItem(QGraphicsLineItem):
    """Arrow line indicating camera viewing direction.

    Rotates around the camera marker position. Emits angleChanged on rotation.
    """

    angleChanged = Signal(float)

    ARROW_LENGTH = 40.0
    ARROW_HEAD_LEN = 8.0

    def __init__(self, marker_item: CameraMarkerItem, angle: float = 0.0, parent=None):
        super().__init__(parent)
        self._marker = marker_item
        self._angle = angle
        self.setZValue(Z_ARROW)
        self.setPen(QPen(QColor(220, 40, 40), 2.0))
        self.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable, False)
        self._update_geometry()

    def _update_geometry(self) -> None:
        """Recalculate line endpoints based on marker position and angle."""
        marker_pos = self._marker.pos()
        rad = math.radians(self._angle)
        dx = self.ARROW_LENGTH * math.cos(rad)
        dy = -self.ARROW_LENGTH * math.sin(rad)

        self.setLine(0, 0, dx, dy)
        self.setPos(marker_pos)

    def set_angle(self, angle: float) -> None:
        """Set direction angle in degrees (0=right, CCW positive)."""
        self._angle = angle
        self._update_geometry()
        self.angleChanged.emit(angle)

    @property
    def angle(self) -> float:
        return self._angle

    def paint(self, painter, option, widget=None):
        """Draw arrow line with arrowhead at the tip."""
        painter.setPen(self.pen())
        painter.setBrush(Qt.BrushStyle.NoBrush)

        line = self.line()
        start = line.p1()
        end = line.p2()

        painter.drawLine(start, end)

        # Arrowhead
        rad = math.atan2(end.y() - start.y(), end.x() - start.x())
        a1 = rad + math.radians(150)
        a2 = rad - math.radians(150)

        p1 = end + self.ARROW_HEAD_LEN * (
            __import__("PySide6.QtCore", fromlist=["QPointF"]).QPointF(math.cos(a1), math.sin(a1))
        )
        p2 = end + self.ARROW_HEAD_LEN * (
            __import__("PySide6.QtCore", fromlist=["QPointF"]).QPointF(math.cos(a2), math.sin(a2))
        )
        painter.drawLine(end, p1)
        painter.drawLine(end, p2)


class ViewingConeItem(QGraphicsPolygonItem):
    """Semi-transparent polygon showing camera field of view cone.

    Updates based on marker position, direction angle, and cone angle.
    """

    CONE_LENGTH = 80.0

    def __init__(self, marker_item: CameraMarkerItem, direction_item: DirectionArrowItem, cone_angle: float = 60.0, parent=None):
        super().__init__(parent)
        self._marker = marker_item
        self._direction = direction_item
        self._cone_angle = cone_angle
        self.setZValue(Z_CONE)

        color = QColor(220, 40, 40, 40)
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor(220, 40, 40, 120), 1.0, Qt.PenStyle.DashLine))
        self.setFlag(QGraphicsPolygonItem.GraphicsItemFlag.ItemIsSelectable, False)

    def set_cone_angle(self, angle: float) -> None:
        """Set cone spread angle in degrees."""
        self._cone_angle = angle

    def update_geometry(self) -> None:
        """Rebuild cone polygon from marker position, direction, and cone angle."""
        marker_pos = self._marker.pos()
        direction = self._direction.angle
        half = math.radians(self._cone_angle / 2.0)

        left_dir = math.radians(direction) + half
        right_dir = math.radians(direction) - half

        tip = marker_pos
        left = tip + self.CONE_LENGTH * (
            __import__("PySide6.QtCore", fromlist=["QPointF"]).QPointF(
                math.cos(math.pi - left_dir), -math.sin(math.pi - left_dir)
            )
        )
        right = tip + self.CONE_LENGTH * (
            __import__("PySide6.QtCore", fromlist=["QPointF"]).QPointF(
                math.cos(math.pi - right_dir), -math.sin(math.pi - right_dir)
            )
        )

        polygon = QPolygonF([tip, left, right])
        self.setPolygon(polygon)


class VisibleAreaItem(QGraphicsPolygonItem):
    """Semi-transparent polygon for user-drawn visible area.

    Supports vertex dragging via handle items for editing.
    """

    def __init__(self, points: list[list[float]] | None = None, parent=None):
        super().__init__(parent)
        self.setZValue(Z_AREA)

        color = QColor(60, 120, 200, 35)
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor(60, 120, 200, 150), 1.5))
        self.setFlag(QGraphicsPolygonItem.GraphicsItemFlag.ItemIsSelectable, True)

        if points and len(points) >= 3:
            self.set_points(points)

    def set_points(self, points: list[list[float]]) -> None:
        """Set polygon vertices from list of [x, y] pairs."""
        polygon = QPolygonF([__import__("PySide6.QtCore", fromlist=["QPointF"]).QPointF(p[0], p[1]) for p in points])
        self.setPolygon(polygon)

    def get_points(self) -> list[list[float]]:
        """Get polygon vertices as [[x, y], ...]."""
        poly = self.polygon()
        return [[poly.at(i).x(), poly.at(i).y()] for i in range(poly.size())]

    def add_vertex(self, x: float, y: float) -> None:
        """Append a new vertex to the polygon."""
        poly = self.polygon()
        poly.append(__import__("PySide6.QtCore", fromlist=["QPointF"]).QPointF(x, y))
        self.setPolygon(poly)

    def move_vertex(self, index: int, x: float, y: float) -> None:
        """Move vertex at index to new position."""
        poly = self.polygon()
        if 0 <= index < poly.size():
            poly.replace(index, __import__("PySide6.QtCore", fromlist=["QPointF"]).QPointF(x, y))
            self.setPolygon(poly)


class AnnotationGraphicsGroup(QGraphicsItemGroup):
    """Groups all annotation items into a single selection/drag unit.

    Z-ordering: area(1) < cone(2) < arrow(3) < marker(4).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable, True)

        self._marker: Optional[CameraMarkerItem] = None
        self._arrow: Optional[DirectionArrowItem] = None
        self._cone: Optional[ViewingConeItem] = None
        self._area: Optional[VisibleAreaItem] = None

    def set_items(
        self,
        marker: CameraMarkerItem,
        arrow: DirectionArrowItem,
        cone: ViewingConeItem,
        area: VisibleAreaItem | None = None,
    ) -> None:
        """Add all sub-items to this group."""
        self._marker = marker
        self._arrow = arrow
        self._cone = cone
        self._area = area

        self.addToGroup(marker)
        self.addToGroup(arrow)
        self.addToGroup(cone)
        if area is not None:
            self.addToGroup(area)

    @property
    def marker(self) -> CameraMarkerItem | None:
        return self._marker

    @property
    def arrow(self) -> DirectionArrowItem | None:
        return self._arrow

    @property
    def cone(self) -> ViewingConeItem | None:
        return self._cone

    @property
    def area(self) -> VisibleAreaItem | None:
        return self._area
