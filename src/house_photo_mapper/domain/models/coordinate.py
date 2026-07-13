"""Coordinate system models - enums, point types, and exceptions."""

from dataclasses import dataclass
from enum import Enum, auto


class CoordinateSystem(Enum):
    """Coordinate reference systems used in the application."""

    WORLD = auto()      # Y-up, meters, origin at project (0,0)
    SCREEN = auto()     # Y-down, pixels, origin at viewport top-left
    EXIF = auto()       # 8 orientations, relative to sensor


class CRSMismatchError(ValueError):
    """Raised when transforming between incompatible coordinate systems."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class WorldPoint:
    """Point in world coordinates (Y-up, meters)."""

    x: float
    y: float  # Y-up

    def __repr__(self) -> str:
        return f"WorldPoint(x={self.x:.3f}, y={self.y:.3f})"


@dataclass(frozen=True, slots=True)
class ScreenPoint:
    """Point in screen/viewport coordinates (Y-down, pixels)."""

    x: float
    y: float  # Y-down

    def __repr__(self) -> str:
        return f"ScreenPoint(x={self.x:.1f}, y={self.y:.1f})"
