"""Annotation graphics items for plan view."""

import math
from typing import Optional

from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import (
    QPen,
    QBrush,
    QColor,
    QPainterPath,
    QPolygonF,
    QTransform,
)
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
    QGraphicsSceneMouseEvent,
)


class CameraMarkerItem(QGraphicsEllipseItem):
    """Camera position marker on the plan.

    Red circle indicating camera location. Movable and selectable.
    """

    positionChanged = Signal(QPointF)

    def __init__(
        self,
        x: float,
        y: float,
        radius: float = 8.0,
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        """Initialize camera marker.

        Args:
            x: X coordinate in scene coordinates.
            y: Y coordinate in scene coordinates.
            radius: Marker radius in pixels.
            parent: Parent graphics item.
        """
        super().__init__(-radius, -radius, radius * 2, radius * 2, parent)
        self.setPos(x, y)
        self.setZValue(4)  # On top

        # Visual style
        self.setPen(QPen(QColor(220, 50, 50), 2))
        self.setBrush(QBrush(QColor(220, 50, 50, 180)))

        # Flags for interaction
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        # Store radius for serialization
        self._radius = radius

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value) -> any:
        """Handle item changes to emit position changed signal."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.positionChanged.emit(self.pos())
        return super().itemChange(change, value)

    def get_position(self) -> tuple[float, float]:
        """Get current position as (x, y) tuple."""
        pos = self.pos()
        return (pos.x(), pos.y())

    def set_position(self, x: float, y: float) -> None:
        """Set marker position."""
        self.setPos(x, y)


class DirectionArrowItem(QGraphicsLineItem):
    """Direction arrow emanating from camera marker.

    Indicates the camera's viewing direction.
    """

    angleChanged = Signal(float)

    def __init__(
        self,
        length: float = 40.0,
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        """Initialize direction arrow.

        Args:
            length: Arrow length in pixels.
            parent: Parent graphics item (should be CameraMarkerItem).
        """
        super().__init__(0, 0, length, 0, parent)
        self.setZValue(3)  # Above cone, below marker

        # Visual style
        self.setPen(QPen(QColor(50, 50, 220), 3))

        # Store length
        self._length = length

        # Rotation handle (small circle at end)
        self._handle_radius = 5.0

    def set_angle(self, angle_degrees: float) -> None:
        """Set arrow direction.

        Args:
            angle_degrees: Direction in degrees (0 = right, 90 = down).
        """
        # Convert to radians (Qt uses degrees for rotation)
        self.setRotation(angle_degrees)
        self.angleChanged.emit(angle_degrees)

    def get_angle(self) -> float:
        """Get current direction angle."""
        return self.rotation()

    def set_length(self, length: float) -> None:
        """Update arrow length."""
        self._length = length
        self.setLine(0, 0, length, 0)


class ViewingConeItem(QGraphicsPolygonItem):
    """Viewing cone polygon showing camera field of view.

    Triangular/sector polygon based on cone angle and direction.
    """

    def __init__(
        self,
        cone_angle: float = 60.0,
        cone_length: float = 80.0,
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        """Initialize viewing cone.

        Args:
            cone_angle: Opening angle in degrees.
            cone_length: Cone length in pixels.
            parent: Parent graphics item (should be CameraMarkerItem).
        """
        super().__init__(parent)
        self.setZValue(2)  # Above polygon, below arrow

        # Visual style
        self.setPen(QPen(QColor(50, 180, 50), 1))
        self.setBrush(QBrush(QColor(50, 180, 50, 60)))

        # Store parameters
        self._cone_angle = cone_angle
        self._cone_length = cone_length

        # Update polygon
        self._update_polygon()

    def set_cone_angle(self, angle: float) -> None:
        """Set cone opening angle.

        Args:
            angle: Opening angle in degrees (0-180).
        """
        self._cone_angle = max(0, min(180, angle))
        self._update_polygon()

    def get_cone_angle(self) -> float:
        """Get current cone angle."""
        return self._cone_angle

    def set_cone_length(self, length: float) -> None:
        """Update cone length."""
        self._cone_length = length
        self._update_polygon()

    def _update_polygon(self) -> None:
        """Update the cone polygon based on current parameters."""
        half_angle = math.radians(self._cone_angle / 2)

        # Create polygon points
        points = [QPointF(0, 0)]  # Origin (camera position)

        # Right edge
        right_x = self._cone_length * math.cos(half_angle)
        right_y = self._cone_length * math.sin(half_angle)
        points.append(QPointF(right_x, right_y))

        # Left edge
        left_x = self._cone_length * math.cos(-half_angle)
        left_y = self._cone_length * math.sin(-half_angle)
        points.append(QPointF(left_x, left_y))

        self.setPolygon(QPolygonF(points))


class VisibleAreaItem(QGraphicsPolygonItem):
    """Visible area polygon drawn by user.

    Semi-transparent polygon with 4+ points defining the visible region.
    Supports vertex dragging for editing.
    """

    pointsChanged = Signal()

    def __init__(
        self,
        points: Optional[list[QPointF]] = None,
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        """Initialize visible area polygon.

        Args:
            points: Initial polygon points.
            parent: Parent graphics item.
        """
        super().__init__(parent)
        self.setZValue(1)  # Bottom layer

        # Visual style
        self.setPen(QPen(QColor(180, 50, 180), 2))
        self.setBrush(QBrush(QColor(180, 50, 180, 40)))

        # Vertex handles
        self._handle_radius = 4.0
        self._dragging_vertex = -1
        self._vertices: list[QPointF] = []

        # Set initial points
        if points:
            self._vertices = points
            self._update_polygon()

    def set_points(self, points: list[QPointF]) -> None:
        """Set polygon points.

        Args:
            points: List of QPointF vertices.
        """
        self._vertices = points
        self._update_polygon()
        self.pointsChanged.emit()

    def get_points(self) -> list[QPointF]:
        """Get current polygon points."""
        return self._vertices.copy()

    def add_point(self, point: QPointF) -> None:
        """Add a point to the polygon.

        Args:
            point: Point to add.
        """
        self._vertices.append(point)
        self._update_polygon()
        self.pointsChanged.emit()

    def _update_polygon(self) -> None:
        """Update the polygon from vertices."""
        if self._vertices:
            self.setPolygon(QPolygonF(self._vertices))


class AnnotationGraphicsGroup(QGraphicsItem):
    """Group containing all annotation graphics items.

    Single selection/drag unit for the entire annotation.
    """

    def __init__(
        self,
        annotation_id: str,
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        """Initialize annotation graphics group.

        Args:
            annotation_id: Unique annotation identifier.
            parent: Parent graphics item.
        """
        super().__init__(parent)
        self._annotation_id = annotation_id

        # Create child items
        self._marker = CameraMarkerItem(0, 0, parent=self)
        self._arrow = DirectionArrowItem(length=40.0, parent=self._marker)
        self._cone = ViewingConeItem(cone_angle=60.0, cone_length=80.0, parent=self._marker)
        self._visible_area: Optional[VisibleAreaItem] = None

        # Connect signals
        self._marker.positionChanged.connect(self._on_marker_moved)

    @property
    def annotation_id(self) -> str:
        """Get annotation ID."""
        return self._annotation_id

    @property
    def marker(self) -> CameraMarkerItem:
        """Get camera marker item."""
        return self._marker

    @property
    def arrow(self) -> DirectionArrowItem:
        """Get direction arrow item."""
        return self._arrow

    @property
    def cone(self) -> ViewingConeItem:
        """Get viewing cone item."""
        return self._cone

    @property
    def visible_area(self) -> Optional[VisibleAreaItem]:
        """Get visible area item."""
        return self._visible_area

    def set_visible_area(self, points: list[QPointF]) -> None:
        """Set or create visible area polygon.

        Args:
            points: Polygon vertices.
        """
        if self._visible_area is None:
            self._visible_area = VisibleAreaItem(parent=self)
        self._visible_area.set_points(points)

    def get_position(self) -> tuple[float, float]:
        """Get camera marker position."""
        return self._marker.get_position()

    def set_position(self, x: float, y: float) -> None:
        """Set camera marker position."""
        self._marker.set_position(x, y)

    def get_direction_angle(self) -> float:
        """Get direction angle."""
        return self._arrow.get_angle()

    def set_direction_angle(self, angle: float) -> None:
        """Set direction angle."""
        self._arrow.set_angle(angle)

    def get_cone_angle(self) -> float:
        """Get cone angle."""
        return self._cone.get_cone_angle()

    def set_cone_angle(self, angle: float) -> None:
        """Set cone angle."""
        self._cone.set_cone_angle(angle)

    def get_visible_area_points(self) -> list[tuple[float, float]]:
        """Get visible area points as list of (x, y) tuples."""
        if self._visible_area is None:
            return []
        return [(p.x(), p.y()) for p in self._visible_area.get_points()]

    def set_visible_area_points(self, points: list[tuple[float, float]]) -> None:
        """Set visible area points from list of (x, y) tuples."""
        qpoints = [QPointF(x, y) for x, y in points]
        self.set_visible_area(qpoints)

    def _on_marker_moved(self, pos: QPointF) -> None:
        """Handle marker position change."""
        # The arrow and cone move with the marker since they're children
        pass

    def boundingRect(self) -> QRectF:
        """Return bounding rect encompassing all children."""
        if not self._marker:
            return QRectF()
        # Simple bounding rect around marker
        return self._marker.boundingRect()

    def paint(self, painter, option, widget=None):
        """Custom paint - children paint themselves."""
        pass
