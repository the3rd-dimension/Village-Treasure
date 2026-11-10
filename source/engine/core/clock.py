"""Frame timing and delta-time management."""
from __future__ import annotations

import pygame

from engine.utilities.constants import MAX_DELTA_TIME


class GameClock:
    """Wrap pygame's clock and expose frame delta time in seconds."""

    def __init__(self, target_fps: int = 60) -> None:
        if target_fps <= 0:
            raise ValueError("target_fps must be greater than zero.")

        self._clock = pygame.time.Clock()
        self.target_fps = target_fps
        self.delta_time = 0.0
        self.fps = 0.0

    def tick(self) -> float:
        """Wait for the frame cap and return a clamped delta time in seconds."""
        elapsed_ms = self._clock.tick(self.target_fps)
        self.delta_time = min(elapsed_ms / 1000.0, MAX_DELTA_TIME)
        self.fps = self._clock.get_fps()
        return self.delta_time

    def reset(self) -> None:
        """Reset timing history"""
        self._clock = pygame.time.Clock()
        self.delta_time = 0.0
        self.fps = 0.0
