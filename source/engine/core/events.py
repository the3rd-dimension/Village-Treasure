"""Pygame window and input events."""
from __future__ import annotations

import pygame


class EventManager:
    """Pygame events per frame"""

    def __init__(self) -> None:
        self._events: list[pygame.event.Event] = []
        self.quit_requested = False

    @property
    def events(self) -> tuple[pygame.event.Event, ...]:
        """Read-only snapshot of events collected during the latest poll."""
        return tuple(self._events)

    def poll(self) -> tuple[pygame.event.Event, ...]:
        """Collect the event queue and record whether the window was closed."""
        self._events = pygame.event.get()
        self.quit_requested = any(
            event.type == pygame.QUIT for event in self._events
        )
        return self.events
