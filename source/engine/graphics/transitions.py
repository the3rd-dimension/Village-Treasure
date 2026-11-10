"""Reusable fade-out, destination-label, and fade-in transitions."""
from __future__ import annotations


class LocationTransition:
    """Runs a location transition"""

    def __init__(self, fade_seconds: float = 0.24, label_seconds: float = 0.55) -> None:
        if fade_seconds <= 0 or label_seconds < 0:
            raise ValueError("Transition durations must be positive.")
        self.fade_seconds = fade_seconds
        self.label_seconds = label_seconds
        self.destination: str | None = None
        self.phase: str | None = None
        self.elapsed = 0.0
        self._destination_pending = False

    @property
    def active(self) -> bool:
        return self.phase is not None

    @property
    def alpha(self) -> int:
        if self.phase == "out":
            return min(255, int(255 * self.elapsed / self.fade_seconds))
        if self.phase == "hold":
            return 255
        if self.phase == "in":
            return max(0, 255 - int(255 * self.elapsed / self.fade_seconds))
        return 0

    def start(self, destination: str) -> None:
        if self.active:
            return
        self.destination = destination
        self.phase = "out"
        self.elapsed = 0.0
        self._destination_pending = True

    def update(self, delta_time: float) -> str | None:
        """Advance the fade and return its destination once at full black."""
        if not self.active:
            return None
        self.elapsed += max(0.0, delta_time)
        if self.phase == "out" and self.elapsed >= self.fade_seconds:
            self.phase = "hold"
            self.elapsed = 0.0
            if self._destination_pending:
                self._destination_pending = False
                return self.destination
        elif self.phase == "hold" and self.elapsed >= self.label_seconds:
            self.phase = "in"
            self.elapsed = 0.0
        elif self.phase == "in" and self.elapsed >= self.fade_seconds:
            self.phase = None
            self.destination = None
            self.elapsed = 0.0
        return None