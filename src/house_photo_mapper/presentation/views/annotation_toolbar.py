"""AnnotationToolbar - Tool selection widget for annotation creation."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QToolBar, QToolButton


class AnnotationToolbar(QToolBar):
    """Toolbar with Select, Place Marker, and Set Cone tool buttons.

    Emits tool_selected when a tool button is clicked.
    """

    tool_selected = Signal(str)  # tool name: 'select', 'place_marker', 'set_cone'

    def __init__(self, parent=None) -> None:
        super().__init__("Annotation", parent)

        self._btn_select = QToolButton(self)
        self._btn_select.setText("Select")
        self._btn_select.setCheckable(True)
        self._btn_select.setChecked(True)
        self._btn_select.setToolTip("Select and move annotations (V)")

        self._btn_place = QToolButton(self)
        self._btn_place.setText("Place Marker")
        self._btn_place.setCheckable(True)
        self._btn_place.setToolTip("Place a camera marker (Ctrl+Shift+A)")

        self._btn_cone = QToolButton(self)
        self._btn_cone.setText("Set Cone")
        self._btn_cone.setCheckable(True)
        self._btn_cone.setToolTip("Adjust viewing cone direction")

        self.addWidget(self._btn_select)
        self.addWidget(self._btn_place)
        self.addWidget(self._btn_cone)

        self._group = QButtonGroup(self)
        self._group.addButton(self._btn_select, 0)
        self._group.addButton(self._btn_place, 1)
        self._group.addButton(self._btn_cone, 2)

        self._btn_select.clicked.connect(lambda: self.tool_selected.emit("select"))
        self._btn_place.clicked.connect(lambda: self.tool_selected.emit("place_marker"))
        self._btn_cone.clicked.connect(lambda: self.tool_selected.emit("set_cone"))

    def set_active_tool(self, tool_name: str) -> None:
        """Update checked state to reflect active tool."""
        mapping = {
            "select": self._btn_select,
            "place_marker": self._btn_place,
            "set_cone": self._btn_cone,
            "set_direction": self._btn_place,
        }
        btn = mapping.get(tool_name)
        if btn:
            btn.setChecked(True)
