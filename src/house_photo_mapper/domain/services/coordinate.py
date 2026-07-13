"""CoordinateConverter - Central coordinate transformation service."""

from dataclasses import dataclass

from house_photo_mapper.domain.models.coordinate import (
    CRSMismatchError,
    ScreenPoint,
    WorldPoint,
)


@dataclass(frozen=True, slots=True)
class ViewportContext:
    """Viewport context for coordinate transformations.

    Attributes:
        origin: Screen coordinates of world origin (0,0).
        pixels_per_meter: Scale factor (pixels per world meter).
    """

    origin: ScreenPoint
    pixels_per_meter: float = 100.0


class CoordinateConverter:
    """Central coordinate transformation service.

    Stateless, thread-safe service for converting between WORLD (Y-up, meters),
    SCREEN (Y-down, pixels), and EXIF (8 orientations) coordinate systems.

    All transformations go through this service to ensure consistency
    and prevent Y-up/Y-down bugs.
    """

    def __init__(self, pixels_per_meter: float = 100.0) -> None:
        """Initialize converter with scale factor.

        Args:
            pixels_per_meter: Scale factor for world-to-screen conversion.
                Default 100.0 means 1 meter = 100 pixels.
        """
        if pixels_per_meter <= 0:
            raise ValueError("pixels_per_meter must be positive")
        self._pixels_per_meter = pixels_per_meter

    @property
    def pixels_per_meter(self) -> float:
        """Get the current scale factor."""
        return self._pixels_per_meter

    def world_to_screen(
        self, world_pt: WorldPoint, viewport_origin: ScreenPoint
    ) -> ScreenPoint:
        """Convert world point to screen point with viewport pan.

        Args:
            world_pt: Point in world coordinates (Y-up, meters).
            viewport_origin: Pan offset in screen coordinates (top-left of viewport).

        Returns:
            Point in screen coordinates (Y-down, pixels).
        """
        return ScreenPoint(
            x=world_pt.x * self._pixels_per_meter + viewport_origin.x,
            y=-world_pt.y * self._pixels_per_meter + viewport_origin.y,
        )

    def screen_to_world(
        self, screen_pt: ScreenPoint, viewport_origin: ScreenPoint
    ) -> WorldPoint:
        """Convert screen point to world point with viewport pan.

        Args:
            screen_pt: Point in screen coordinates (Y-down, pixels).
            viewport_origin: Pan offset in screen coordinates.

        Returns:
            Point in world coordinates (Y-up, meters).
        """
        return WorldPoint(
            x=(screen_pt.x - viewport_origin.x) / self._pixels_per_meter,
            y=-(screen_pt.y - viewport_origin.y) / self._pixels_per_meter,
        )

    def exif_to_world(
        self,
        screen_pt: ScreenPoint,
        orientation: int,
        image_size: tuple[int, int],
    ) -> WorldPoint:
        """Convert screen point with EXIF orientation to world coordinates.

        Applies EXIF orientation transform in image pixel space, then
        converts to world via screen_to_world with zero viewport origin.

        Args:
            screen_pt: Point in image pixel coordinates (0..width, 0..height).
            orientation: EXIF orientation value (1-8 per TIFF spec).
            image_size: (width, height) of the image in pixels.

        Returns:
            Point in world coordinates.

        Raises:
            CRSMismatchError: If orientation is not in 1..8.
        """
        if not 1 <= orientation <= 8:
            raise CRSMismatchError(f"Invalid EXIF orientation: {orientation}")

        w, h = image_size
        x, y = screen_pt.x, screen_pt.y

        # Apply EXIF orientation transform (TIFF/EXIF spec)
        match orientation:
            case 1:  # Normal
                pass
            case 2:  # Flip horizontal
                x = w - x
            case 3:  # Rotate 180
                x, y = w - x, h - y
            case 4:  # Flip vertical
                y = h - y
            case 5:  # Transpose (flip horizontal + rotate 90 CCW)
                x, y = y, x
            case 6:  # Rotate 90 CW
                x, y = h - y, x
            case 7:  # Transverse (flip vertical + rotate 90 CCW)
                x, y = y, w - x
            case 8:  # Rotate 270 CW (or 90 CCW)
                x, y = y, h - x

        # Convert oriented screen point to world (zero viewport origin)
        return self.screen_to_world(ScreenPoint(x, y), ScreenPoint(0, 0))

    def world_to_exif_screen(
        self,
        world_pt: WorldPoint,
        orientation: int,
        image_size: tuple[int, int],
    ) -> ScreenPoint:
        """Convert world point to EXIF-oriented screen coordinates.

        Inverse of exif_to_world: world -> screen (zero origin) -> apply
        inverse EXIF orientation.

        Args:
            world_pt: Point in world coordinates.
            orientation: EXIF orientation value (1-8).
            image_size: (width, height) of the image in pixels.

        Returns:
            Point in EXIF-oriented image pixel coordinates.

        Raises:
            CRSMismatchError: If orientation is not in 1..8.
        """
        if not 1 <= orientation <= 8:
            raise CRSMismatchError(f"Invalid EXIF orientation: {orientation}")

        w, h = image_size
        # World -> screen (zero origin)
        screen = self.world_to_screen(world_pt, ScreenPoint(0, 0))
        x, y = screen.x, screen.y

        # Apply inverse EXIF orientation
        match orientation:
            case 1:  # Normal
                pass
            case 2:  # Flip horizontal (self-inverse)
                x = w - x
            case 3:  # Rotate 180 (self-inverse)
                x, y = w - x, h - y
            case 4:  # Flip vertical (self-inverse)
                y = h - y
            case 5:  # Transpose (self-inverse)
                x, y = y, x
            case 6:  # Rotate 90 CW -> inverse is rotate 270 CW (orientation 8)
                x, y = y, w - x
            case 7:  # Transverse (self-inverse)
                x, y = h - y, x
            case 8:  # Rotate 270 CW -> inverse is rotate 90 CW (orientation 6)
                x, y = h - y, x

        return ScreenPoint(x, y)
