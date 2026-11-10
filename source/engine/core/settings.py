"""runtime settings loaded from the project configuration."""
from __future__ import annotations

from dataclasses import dataclass

import config


@dataclass(frozen=True, slots=True)
class GameSettings:
    """Immutable settings snapshot."""

    title: str = config.GAME_TITLE
    window_width: int = config.WINDOW_WIDTH
    window_height: int = config.WINDOW_HEIGHT
    minimum_width: int = config.WINDOW_MIN_WIDTH
    minimum_height: int = config.WINDOW_MIN_HEIGHT
    target_fps: int = config.TARGET_FPS
    fullscreen: bool = config.START_FULLSCREEN
    vsync: bool = config.START_VSYNC
    background_color: tuple[int, int, int] = config.BACKGROUND_COLOR

    def __post_init__(self) -> None:
        if self.window_width <= 0 or self.window_height <= 0:
            raise ValueError("Window dimensions must be positive.")
        if self.minimum_width <= 0 or self.minimum_height <= 0:
            raise ValueError("Minimum window dimensions must be positive.")
        if self.target_fps <= 0:
            raise ValueError("Target FPS must be positive.")
        if len(self.background_color) != 3 or any(
            not 0 <= channel <= 255 for channel in self.background_color
        ):
            raise ValueError("background_color must be an RGB tuple.")

    @classmethod
    def from_project_config(cls) -> "GameSettings":
        """Build settings from values in the root ``config.py`` file."""
        return cls()
