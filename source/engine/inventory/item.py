"""A collectible item definition."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Item:
    id: str
    name: str
    description: str
    icon: str
    color: tuple[int, int, int]
    usage_requirements: Mapping[str, str | bool]