"""General-purpose helpers"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import TypeVar

Number = TypeVar("Number", int, float)


def clamp(value: Number, minimum: Number, maximum: Number) -> Number:
    """Clamp value to the [minimum, maximum] range."""
    if minimum > maximum:
        raise ValueError("minimum cannot be greater than maximum")
    return max(minimum, min(value, maximum))


def ensure_directory(path: str | Path) -> Path:
    """Create a directory (including parents) and return it as a Path."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def resource_path(relative_path: str | Path) -> Path:
    """Resolve a bundled resource path for development or PyInstaller builds."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base_path / relative_path
