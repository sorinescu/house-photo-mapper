"""ThemeManager - Dark/light mode theming with QPalette-based theming."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QColor, QPalette


class ThemeMode(Enum):
    """Theme mode options."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


@dataclass
class ThemePalette:
    """Color palette for a theme.
    
    Defines all colors needed for consistent theming across the application.
    """
    
    # Base colors
    background: QColor = field(default_factory=lambda: QColor(255, 255, 255))
    foreground: QColor = field(default_factory=lambda: QColor(0, 0, 0))
    
    # Widget colors
    widget_background: QColor = field(default_factory=lambda: QColor(240, 240, 240))
    widget_foreground: QColor = field(default_factory=lambda: QColor(0, 0, 0))
    
    # Button colors
    button_background: QColor = field(default_factory=lambda: QColor(200, 200, 200))
    button_foreground: QColor = field(default_factory=lambda: QColor(0, 0, 0))
    
    # Input colors
    input_background: QColor = field(default_factory=lambda: QColor(255, 255, 255))
    input_foreground: QColor = field(default_factory=lambda: QColor(0, 0, 0))
    
    # Accent colors
    accent: QColor = field(default_factory=lambda: QColor(0, 122, 255))
    accent_hover: QColor = field(default_factory=lambda: QColor(0, 102, 235))
    
    # Border colors
    border: QColor = field(default_factory=lambda: QColor(200, 200, 200))
    border_focus: QColor = field(default_factory=lambda: QColor(0, 122, 255))
    
    # Text colors
    text_primary: QColor = field(default_factory=lambda: QColor(0, 0, 0))
    text_secondary: QColor = field(default_factory=lambda: QColor(100, 100, 100))
    text_disabled: QColor = field(default_factory=lambda: QColor(150, 150, 150))
    
    # Status colors
    success: QColor = field(default_factory=lambda: QColor(40, 167, 69))
    warning: QColor = field(default_factory=lambda: QColor(255, 193, 7))
    error: QColor = field(default_factory=lambda: QColor(220, 53, 69))
    
    # Selection colors
    selection_background: QColor = field(default_factory=lambda: QColor(0, 122, 255))
    selection_foreground: QColor = field(default_factory=lambda: QColor(255, 255, 255))
    
    # Tooltip colors
    tooltip_background: QColor = field(default_factory=lambda: QColor(255, 255, 220))
    tooltip_foreground: QColor = field(default_factory=lambda: QColor(0, 0, 0))
    
    def to_qpalette(self) -> QPalette:
        """Convert theme palette to QPalette for Qt widgets."""
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.ColorRole.Window, self.background)
        palette.setColor(QPalette.ColorRole.WindowText, self.foreground)
        
        # Widget colors
        palette.setColor(QPalette.ColorRole.Base, self.widget_background)
        palette.setColor(QPalette.ColorRole.Text, self.widget_foreground)
        
        # Button colors
        palette.setColor(QPalette.ColorRole.Button, self.button_background)
        palette.setColor(QPalette.ColorRole.ButtonText, self.button_foreground)
        
        # Input colors
        palette.setColor(QPalette.ColorRole.Base, self.input_background)
        palette.setColor(QPalette.ColorRole.Text, self.input_foreground)
        
        # Accent/highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, self.selection_background)
        palette.setColor(QPalette.ColorRole.HighlightedText, self.selection_foreground)
        
        # Disabled colors
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, self.text_disabled)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, self.text_disabled)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, self.text_disabled)
        
        return palette


# Default light theme
LIGHT_THEME = ThemePalette(
    background=QColor(255, 255, 255),
    foreground=QColor(0, 0, 0),
    widget_background=QColor(240, 240, 240),
    widget_foreground=QColor(0, 0, 0),
    button_background=QColor(200, 200, 200),
    button_foreground=QColor(0, 0, 0),
    input_background=QColor(255, 255, 255),
    input_foreground=QColor(0, 0, 0),
    accent=QColor(0, 122, 255),
    accent_hover=QColor(0, 102, 235),
    border=QColor(200, 200, 200),
    border_focus=QColor(0, 122, 255),
    text_primary=QColor(0, 0, 0),
    text_secondary=QColor(100, 100, 100),
    text_disabled=QColor(150, 150, 150),
    success=QColor(40, 167, 69),
    warning=QColor(255, 193, 7),
    error=QColor(220, 53, 69),
    selection_background=QColor(0, 122, 255),
    selection_foreground=QColor(255, 255, 255),
    tooltip_background=QColor(255, 255, 220),
    tooltip_foreground=QColor(0, 0, 0),
)

# Default dark theme
DARK_THEME = ThemePalette(
    background=QColor(30, 30, 30),
    foreground=QColor(255, 255, 255),
    widget_background=QColor(40, 40, 40),
    widget_foreground=QColor(255, 255, 255),
    button_background=QColor(60, 60, 60),
    button_foreground=QColor(255, 255, 255),
    input_background=QColor(50, 50, 50),
    input_foreground=QColor(255, 255, 255),
    accent=QColor(0, 122, 255),
    accent_hover=QColor(0, 142, 255),
    border=QColor(80, 80, 80),
    border_focus=QColor(0, 122, 255),
    text_primary=QColor(255, 255, 255),
    text_secondary=QColor(180, 180, 180),
    text_disabled=QColor(120, 120, 120),
    success=QColor(40, 167, 69),
    warning=QColor(255, 193, 7),
    error=QColor(220, 53, 69),
    selection_background=QColor(0, 122, 255),
    selection_foreground=QColor(255, 255, 255),
    tooltip_background=QColor(50, 50, 50),
    tooltip_foreground=QColor(255, 255, 255),
)


class ThemeManager(QObject):
    """Manages application theming with QPalette-based theming.
    
    Provides:
    - Dark/light mode switching
    - System preference detection
    - Theme change signals
    - Persistent theme preference
    """
    
    # Signal emitted when theme changes
    theme_changed = Signal(ThemeMode)
    
    # Signal emitted when system theme changes
    system_theme_changed = Signal(ThemeMode)
    
    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize ThemeManager.
        
        Args:
            parent: Parent QObject.
        """
        super().__init__(parent)
        
        # Current theme mode
        self._current_mode = ThemeMode.SYSTEM
        
        # Available themes
        self._themes: dict[ThemeMode, ThemePalette] = {
            ThemeMode.LIGHT: LIGHT_THEME,
            ThemeMode.DARK: DARK_THEME,
        }
        
        # Custom themes (can be set by user)
        self._custom_themes: dict[ThemeMode, ThemePalette] = {}
        
        # System theme detection
        self._system_theme = self._detect_system_theme()
        
        # System theme monitoring
        self._monitoring_system_theme = False
    
    def _detect_system_theme(self) -> ThemeMode:
        """Detect the current system theme.
        
        Returns:
            ThemeMode matching the system theme.
        """
        # On macOS, we can detect dark mode via QPalette
        from PySide6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app:
            palette = app.palette()
            # Check if the window background is dark
            bg_color = palette.color(QPalette.ColorRole.Window)
            # Calculate brightness (simple luminance formula)
            brightness = (bg_color.red() * 299 + bg_color.green() * 587 + bg_color.blue() * 114) / 1000
            if brightness < 128:
                return ThemeMode.DARK
        
        return ThemeMode.LIGHT
    
    def get_current_mode(self) -> ThemeMode:
        """Get the current theme mode.
        
        Returns:
            Current ThemeMode.
        """
        return self._current_mode
    
    def get_effective_mode(self) -> ThemeMode:
        """Get the effective theme mode (resolves SYSTEM to LIGHT or DARK).
        
        Returns:
            Effective ThemeMode (LIGHT or DARK).
        """
        if self._current_mode == ThemeMode.SYSTEM:
            return self._system_theme
        return self._current_mode
    
    def set_theme(self, mode: ThemeMode) -> None:
        """Set the application theme.
        
        Args:
            mode: ThemeMode to apply.
        """
        if mode == self._current_mode:
            return
        
        self._current_mode = mode
        self.theme_changed.emit(mode)
    
    def get_palette(self) -> ThemePalette:
        """Get the current theme palette.
        
        Returns:
            ThemePalette for the current theme.
        """
        effective_mode = self.get_effective_mode()
        
        # Check for custom theme first
        if effective_mode in self._custom_themes:
            return self._custom_themes[effective_mode]
        
        return self._themes[effective_mode]
    
    def get_qpalette(self) -> QPalette:
        """Get the current theme as QPalette.
        
        Returns:
            QPalette for the current theme.
        """
        return self.get_palette().to_qpalette()
    
    def set_custom_theme(self, mode: ThemeMode, palette: ThemePalette) -> None:
        """Set a custom theme palette.
        
        Args:
            mode: ThemeMode to customize.
            palette: Custom ThemePalette.
        """
        self._custom_themes[mode] = palette
        # If this is the current theme, emit change
        if mode == self.get_effective_mode():
            self.theme_changed.emit(self._current_mode)
    
    def reset_to_default(self, mode: ThemeMode) -> None:
        """Reset a theme to its default palette.
        
        Args:
            mode: ThemeMode to reset.
        """
        if mode in self._custom_themes:
            del self._custom_themes[mode]
            # If this is the current theme, emit change
            if mode == self.get_effective_mode():
                self.theme_changed.emit(self._current_mode)
    
    def get_theme_css(self) -> str:
        """Get CSS variables for custom widgets.
        
        Returns:
            CSS string with theme variables.
        """
        palette = self.get_palette()
        
        return f"""
        :root {{
            --background: {palette.background.name()};
            --foreground: {palette.foreground.name()};
            --widget-background: {palette.widget_background.name()};
            --widget-foreground: {palette.widget_foreground.name()};
            --button-background: {palette.button_background.name()};
            --button-foreground: {palette.button_foreground.name()};
            --input-background: {palette.input_background.name()};
            --input-foreground: {palette.input_foreground.name()};
            --accent: {palette.accent.name()};
            --accent-hover: {palette.accent_hover.name()};
            --border: {palette.border.name()};
            --border-focus: {palette.border_focus.name()};
            --text-primary: {palette.text_primary.name()};
            --text-secondary: {palette.text_secondary.name()};
            --text-disabled: {palette.text_disabled.name()};
            --success: {palette.success.name()};
            --warning: {palette.warning.name()};
            --error: {palette.error.name()};
            --selection-background: {palette.selection_background.name()};
            --selection-foreground: {palette.selection_foreground.name()};
            --tooltip-background: {palette.tooltip_background.name()};
            --tooltip-foreground: {palette.tooltip_foreground.name()};
        }}
        """
    
    def apply_theme(self) -> None:
        """Apply the current theme to the application."""
        from PySide6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app:
            palette = self.get_qpalette()
            app.setPalette(palette)
    
    def start_monitoring_system_theme(self) -> None:
        """Start monitoring for system theme changes.
        
        This connects to the application's paletteChange signal to detect
        when the OS theme changes (e.g., macOS dark mode toggle).
        """
        if self._monitoring_system_theme:
            return
        
        from PySide6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app:
            app.paletteChanged.connect(self._on_system_palette_changed)
            self._monitoring_system_theme = True
    
    def stop_monitoring_system_theme(self) -> None:
        """Stop monitoring for system theme changes."""
        if not self._monitoring_system_theme:
            return
        
        from PySide6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app:
            try:
                app.paletteChanged.disconnect(self._on_system_palette_changed)
            except RuntimeError:
                # Signal wasn't connected
                pass
            self._monitoring_system_theme = False
    
    @Slot(QPalette)
    def _on_system_palette_changed(self, palette: QPalette) -> None:
        """Handle system palette change.
        
        Args:
            palette: New system palette.
        """
        # Detect new system theme
        new_theme = self._detect_system_theme()
        
        # Only emit if theme actually changed
        if new_theme != self._system_theme:
            self._system_theme = new_theme
            self.system_theme_changed.emit(new_theme)
            
            # If currently using system theme, emit theme_changed
            if self._current_mode == ThemeMode.SYSTEM:
                self.theme_changed.emit(self._current_mode)
