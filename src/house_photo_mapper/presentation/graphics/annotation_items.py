"""Annotation graphics items — camera marker, direction arrow, viewing cone, visible area."""

from __future__ import annotations

import math
from typing import Optional

from PySide6.QtCore import Qt, Signal, QPointF, QRectF, QVariant
from PySide6.QtGui import QBrush, QColor, QPen, QPolygonF, QPainterPath
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsPolygonItem,
    QGraphicsItem,
    QGraphicsItemGroup,
)

# Z-ordering constants
Z_AREA = 1
Z_CONE = 2
Z_ARROW = 3
Z_MARKER = 4
Z_GRIP = 5

# Data role for storing annotation_id on graphics items
ANNOTATION_ID_ROLE = Qt.ItemDataRole.UserRole + 1

# Default annotation color
DEFAULT_ANNOTATION_COLOR = "#DC2828"


def hex_to_qcolor(hex_color: str, alpha: int = 255) -> QColor:
    """Convert hex color string to QColor.

    Args:
        hex_color: Hex color string like '#DC2828' or 'DC2828'.
        alpha: Alpha channel (0-255).

    Returns:
        QColor instance.
    """
    if not hex_color:
        return QColor(DEFAULT_ANNOTATION_COLOR)
    if not hex_color.startswith("#"):
        hex_color = "#" + hex_color
    c = QColor(hex_color)
    c.setAlpha(alpha)
    return c


class GripItem(QGraphicsEllipseItem):
    """Small draggable handle for resizing rectangles.

    Attached to a parent VisibleAreaItem at corners and edges.
    Dragging a grip resizes the parent rectangle.
    """

    GRIP_RADIUS = 6.0

    def __init__(
        self,
        index: int,
        parent_rect: VisibleAreaItem,
        pos: QPointF,
        parent=None,
    ):
        super().__init__(
            -self.GRIP_RADIUS,
            -self.GRIP_RADIUS,
            self.GRIP_RADIUS * 2,
            self.GRIP_RADIUS * 2,
            parent,
        )
        self._index = index  # 0-7: 4 corners + 4 edge midpoints
        self._parent_rect = parent_rect
        self.setPos(pos)
        self.setZValue(Z_GRIP)
        self.setBrush(QBrush(QColor(255, 255, 255, 200)))
        self.setPen(QPen(QColor(100, 100, 100), 1.0))
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setVisible(False)  # Hidden by default, shown on selection

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionHasChanged:
            self._parent_rect.resize_from_grip(self._index, self.pos())
        return super().itemChange(change, value)


class CameraMarkerItem(QGraphicsEllipseItem):
    """Red circle marking camera position on a plan.

    Movable, selectable, and emits positionChanged when dragged.
    """

    positionChanged = Signal(float, float)

    MARKER_RADIUS = 24.0

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

    def set_color(self, hex_color: str) -> None:
        """Update marker color."""
        c = hex_to_qcolor(hex_color)
        self.setBrush(QBrush(c))
        dark = QColor(c)
        dark.setAlpha(200)
        self.setPen(QPen(dark, 1.5))

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

    def set_color(self, hex_color: str) -> None:
        """Update arrow color."""
        self.setPen(QPen(hex_to_qcolor(hex_color), 2.0))

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

        p1 = end + self.ARROW_HEAD_LEN * QPointF(math.cos(a1), math.sin(a1))
        p2 = end + self.ARROW_HEAD_LEN * QPointF(math.cos(a2), math.sin(a2))
        painter.drawLine(end, p1)
        painter.drawLine(end, p2)


class ViewingConeItem(QGraphicsPolygonItem):
    """Semi-transparent polygon showing camera field of view cone.

    Updates based on marker position, direction angle, and cone angle.
    """

    CONE_LENGTH = 80.0

    def __init__(
        self,
        marker_item: CameraMarkerItem,
        direction_item: DirectionArrowItem,
        cone_angle: float = 60.0,
        parent=None,
    ):
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

    def set_color(self, hex_color: str) -> None:
        """Update cone color."""
        c = hex_to_qcolor(hex_color, 40)
        self.setBrush(QBrush(c))
        border = hex_to_qcolor(hex_color, 120)
        self.setPen(QPen(border, 1.0, Qt.PenStyle.DashLine))

    def update_geometry(self) -> None:
        """Rebuild cone polygon from marker position, direction, and cone angle."""
        marker_pos = self._marker.pos()
        direction = self._direction.angle
        half = math.radians(self._cone_angle / 2.0)

        left_dir = math.radians(direction) + half
        right_dir = math.radians(direction) - half

        tip = marker_pos
        left = tip + self.CONE_LENGTH * QPointF(
            math.cos(math.pi - left_dir), -math.sin(math.pi - left_dir)
        )
        right = tip + self.CONE_LENGTH * QPointF(
            math.cos(math.pi - right_dir), -math.sin(math.pi - right_dir)
        )

        polygon = QPolygonF([tip, left, right])
        self.setPolygon(polygon)


class VisibleAreaItem(QGraphicsRectItem):
    """Resizable rectangle representing the visible area around a marker.

    Created automatically when a marker is placed. Supports resize via
    GripItem handles at corners and edge midpoints.
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        parent=None,
    ):
        super().__init__(x, y, width, height, parent)
        self.setZValue(Z_AREA)

        color = QColor(60, 120, 200, 35)
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor(60, 120, 200, 150), 1.5))
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        # Create 8 grip handles (4 corners + 4 edge midpoints)
        self._grips: list[GripItem] = []
        self._create_grips()

    def _create_grips(self) -> None:
        """Create grip handles at corners and edge midpoints."""
        for i in range(8):
            pos = self._grip_position(i)
            grip = GripItem(i, self, pos, parent=self)
            self._grips.append(grip)

    def _grip_position(self, index: int) -> QPointF:
        """Calculate position for grip at given index.

        Index mapping:
        0=top-left, 1=top-center, 2=top-right,
        3=middle-right, 4=bottom-right, 5=bottom-center,
        6=bottom-left, 7=middle-left
        """
        r = self.rect()
        positions = [
            QPointF(r.left(), r.top()),           # 0: top-left
            QPointF(r.center().x(), r.top()),      # 1: top-center
            QPointF(r.right(), r.top()),           # 2: top-right
            QPointF(r.right(), r.center().y()),    # 3: middle-right
            QPointF(r.right(), r.bottom()),        # 4: bottom-right
            QPointF(r.center().x(), r.bottom()),   # 5: bottom-center
            QPointF(r.left(), r.bottom()),         # 6: bottom-left
            QPointF(r.left(), r.center().y()),     # 7: middle-left
        ]
        return positions[index]

    def _update_grip_positions(self) -> None:
        """Move all grips to match current rect."""
        for i, grip in enumerate(self._grips):
            grip.setPos(self._grip_position(i))

    def resize_from_grip(self, grip_index: int, new_pos: QPointF) -> None:
        """Resize rectangle based on grip drag.

        Args:
            grip_index: Which grip was dragged (0-7).
            new_pos: New position of the dragged grip in parent coords.
        """
        r = self.rect()
        left, top, right, bottom = r.left(), r.top(), r.right(), r.bottom()

        # Update the appropriate edges based on grip index
        if grip_index in (0, 6, 7):  # left side
            left = min(new_pos.x(), right - 20)
        if grip_index in (2, 3, 4):  # right side
            right = max(new_pos.x(), left + 20)
        if grip_index in (0, 1, 2):  # top side
            top = min(new_pos.y(), bottom - 20)
        if grip_index in (4, 5, 6):  # bottom side
            bottom = max(new_pos.y(), top + 20)

        new_rect = QRectF(left, top, right - left, bottom - top)
        self.setRect(new_rect)
        self._update_grip_positions()

    def set_color(self, hex_color: str) -> None:
        """Update rectangle color."""
        c = hex_to_qcolor(hex_color, 35)
        self.setBrush(QBrush(c))
        border = hex_to_qcolor(hex_color, 150)
        self.setPen(QPen(border, 1.5))

    def get_rect_data(self) -> list[float]:
        """Get rectangle as [x, y, width, height]."""
        r = self.rect()
        return [r.x(), r.y(), r.width(), r.height()]

    def set_rect_data(self, data: list[float]) -> None:
        """Set rectangle from [x, y, width, height]."""
        if len(data) >= 4:
            self.setRect(QRectF(data[0], data[1], data[2], data[3]))
            self._update_grip_positions()

    def show_grips(self, visible: bool = True) -> None:
        """Show or hide grip handles."""
        for grip in self._grips:
            grip.setVisible(visible)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionHasChanged:
            self._update_grip_positions()
        return super().itemChange(change, value)


class AnnotationGraphicsGroup(QGraphicsItemGroup):
    """Groups all annotation items into a single selection/drag unit.

    Stores annotation_id for linkage to the data model.
    Z-ordering: area(1) < cone(2) < arrow(3) < marker(4) < grips(5).
    """

    def __init__(self, annotation_id: str = "", parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable, True)
        self._annotation_id = annotation_id

        self._marker: Optional[CameraMarkerItem] = None
        self._arrow: Optional[DirectionArrowItem] = None
        self._cone: Optional[ViewingConeItem] = None
        self._area: Optional[VisibleAreaItem] = None

    @property
    def annotation_id(self) -> str:
        return self._annotation_id

    @annotation_id.setter
    def annotation_id(self, value: str) -> None:
        self._annotation_id = value

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

    def set_color(self, hex_color: str) -> None:
        """Apply color to all items in the group."""
        if self._marker:
            self._marker.set_color(hex_color)
        if self._arrow:
            self._arrow.set_color(hex_color)
        if self._cone:
            self._cone.set_color(hex_color)
        # Area keeps its own blue color; only marker/cone/arrow get annotation color

    def show_area_grips(self, visible: bool = True) -> None:
        """Show or hide resize grips on the area rectangle."""
        if self._area:
            self._area.show_grips(visible)

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
