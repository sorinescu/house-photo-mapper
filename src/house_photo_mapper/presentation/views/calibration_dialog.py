"""CalibrationDialog: Guided 5-step calibration wizard UI.

Provides step-by-step UI for specification-based scale calibration:
1. Enter known dimension (meters/feet/inches)
2. Click first endpoint on plan
3. Click second endpoint on plan
4. Enter verification dimension + click verify points
5. Calibration complete

The dialog installs an event filter on PlanGraphicsView to capture
mouse clicks and convert them to scene coordinates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QEvent, QPointF, Slot
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QWidget,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QMessageBox,
    QGroupBox,
)

from house_photo_mapper.presentation.viewmodels.calibration_vm import (
    CalibrationViewModel,
    CalibrationStep,
)

if TYPE_CHECKING:
    from house_photo_mapper.infrastructure.qt_patterns import PlanGraphicsView


class CalibrationDialog(QDialog):
    """Dialog guiding user through 5-step calibration wizard.

    Uses QStackedWidget for step-by-step navigation. Installs event
    filter on PlanGraphicsView to capture clicks in scene coordinates.
    """

    def __init__(
        self,
        vm: CalibrationViewModel,
        plan_view: "PlanGraphicsView | None" = None,
        parent=None,
    ) -> None:
        """Initialize CalibrationDialog.

        Args:
            vm: CalibrationViewModel to bind to.
            plan_view: PlanGraphicsView for click capture (optional for testing).
            parent: Parent widget.
        """
        super().__init__(parent)
        self._vm = vm
        self._plan_view = plan_view

        self.setWindowTitle("Calibrate Plan Scale")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        # Install event filter on plan view for click capture
        if self._plan_view is not None:
            self._plan_view.viewport().installEventFilter(self)

        self._setup_ui()
        self._connect_signals()

        # Initialize UI state
        self._on_step_changed(int(self._vm.step))

    def _setup_ui(self) -> None:
        """Build the stacked widget UI for all 5 steps."""
        layout = QVBoxLayout(self)

        # Stacked widget for steps
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        # Step 0: Enter known dimension
        self._stack.addWidget(self._create_spec_step())

        # Step 1: Click point 1
        self._stack.addWidget(self._create_click_step("Click Point 1", "Click the first endpoint of the known dimension on the plan."))

        # Step 2: Click point 2
        self._stack.addWidget(self._create_click_step("Click Point 2", "Click the second endpoint of the known dimension on the plan."))

        # Step 3: Verify
        self._stack.addWidget(self._create_verify_step())

        # Step 4: Complete
        self._stack.addWidget(self._create_complete_step())

        # Buttons
        button_layout = QHBoxLayout()

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._vm.cancel)
        button_layout.addWidget(self._cancel_btn)

        button_layout.addStretch()

        self._accept_btn = QPushButton("Accept")
        self._accept_btn.setEnabled(False)
        self._accept_btn.clicked.connect(self._vm.accept)
        button_layout.addWidget(self._accept_btn)

        layout.addLayout(button_layout)

    def _create_spec_step(self) -> QWidget:
        """Step 0: Enter known dimension."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("Enter Known Dimension")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        desc = QLabel("Enter a known real-world distance (e.g., door width = 36 inches).")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Distance input
        input_layout = QHBoxLayout()
        self._distance_input = QLineEdit()
        self._distance_input.setPlaceholderText("e.g., 36")
        input_layout.addWidget(self._distance_input)

        self._unit_combo = QComboBox()
        self._unit_combo.addItems(["inches", "feet", "meters"])
        self._unit_combo.setCurrentText("inches")
        input_layout.addWidget(self._unit_combo)

        layout.addLayout(input_layout)

        self._next_btn = QPushButton("Next")
        self._next_btn.clicked.connect(self._on_spec_next)
        layout.addWidget(self._next_btn)

        layout.addStretch()
        return widget

    def _create_click_step(self, title: str, description: str) -> QWidget:
        """Step 1-2: Click point on plan."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        status = QLabel("Waiting for click on plan...")
        status.setStyleSheet("color: blue;")
        layout.addWidget(status)

        layout.addStretch()
        return widget

    def _create_verify_step(self) -> QWidget:
        """Step 4: Verification."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("Verify Calibration")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        desc = QLabel(
            "Click two points for a second known dimension to verify accuracy. "
            "Error must be <= 2%."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self._verify_status = QLabel("Click first verification point...")
        self._verify_status.setStyleSheet("color: blue;")
        layout.addWidget(self._verify_status)

        self._error_label = QLabel("")
        layout.addWidget(self._error_label)

        self._verify_btn = QPushButton("Verify")
        self._verify_btn.setEnabled(False)
        self._verify_btn.clicked.connect(self._vm.request_verification)
        layout.addWidget(self._verify_btn)

        layout.addStretch()
        return widget

    def _create_complete_step(self) -> QWidget:
        """Step 5: Complete."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("Calibration Complete")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        layout.addWidget(title)

        self._complete_info = QLabel("")
        self._complete_info.setWordWrap(True)
        layout.addWidget(self._complete_info)

        layout.addStretch()
        return widget

    def _connect_signals(self) -> None:
        """Connect ViewModel signals to UI updates."""
        self._vm.step_changed.connect(self._on_step_changed)
        self._vm.calibration_ready.connect(self._on_calibration_ready)
        self._vm.cancelled.connect(self._on_cancelled)
        self._vm.error_message.connect(self._on_error)

    @Slot(int)
    def _on_step_changed(self, step: int) -> None:
        """Handle step change from ViewModel."""
        self._stack.setCurrentIndex(step)

        if step == CalibrationStep.COMPLETE:
            self._accept_btn.setEnabled(True)
            if self._vm.calibration:
                cal = self._vm.calibration
                self._complete_info.setText(
                    f"Scale: {cal.pixels_per_meter:.2f} pixels/meter\n"
                    f"Verified: Yes (error: {self._vm.error_pct:.2f}%)"
                )

    @Slot()
    def _on_spec_next(self) -> None:
        """Handle Next button on spec step."""
        text = self._distance_input.text().strip()
        try:
            distance = float(text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")
            return

        unit = self._unit_combo.currentText()
        self._vm.set_known_distance(distance, unit)

    @Slot(object)
    def _on_calibration_ready(self, calibration) -> None:
        """Handle calibration ready — close dialog with accept."""
        self.accept()

    @Slot()
    def _on_cancelled(self) -> None:
        """Handle cancel — close dialog with reject."""
        self.reject()

    @Slot(str)
    def _on_error(self, message: str) -> None:
        """Handle error message from ViewModel."""
        QMessageBox.warning(self, "Calibration Error", message)

    def eventFilter(self, obj, event) -> bool:
        """Event filter for capturing mouse clicks on PlanGraphicsView.

        Converts viewport coordinates to scene coordinates and passes
        them to the ViewModel.

        Args:
            obj: Object that received the event.
            event: Qt event.

        Returns:
            True if event was consumed, False otherwise.
        """
        if (
            self._plan_view is not None
            and obj is self._plan_view.viewport()
            and event.type() == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
        ):
            # Convert viewport click to scene coordinates
            scene_point = self._plan_view.mapToScene(event.position().toPoint())
            self._vm.receive_point(scene_point)
            return True

        return super().eventFilter(obj, event)
