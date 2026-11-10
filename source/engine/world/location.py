"""Location data used by the choice-based village map."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Location:
    id: str
    name: str
    description: str
    background: str
    background_image: str
    music: str
    connections: dict[str, str]
    npcs: tuple[str, ...]
    objects: tuple[str, ...]
    gate_id: str | None = None