"""Load and validate the connected location map."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import config
from engine.utilities.logger import get_logger
from engine.world.location import Location


logger = get_logger("world")
OPPOSITE_DIRECTION = {"N": "S", "S": "N", "W": "E", "E": "W"}


def load_game_data(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as data_file:
            data = json.load(data_file)
    except (OSError, json.JSONDecodeError) as error:
        logger.exception("Could not load required game data from %s.", path)
        raise ValueError(f"Unable to load game data: {path.name}") from error
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path.name}.")
    return data


class WorldManager:
    """Owns the location definitions and validates every map connection."""

    def __init__(self, map_path: Path | None = None) -> None:
        path = map_path or config.MAPS_DIR / "world_map.json"
        data = load_game_data(path)
        raw_locations = data.get("locations")
        if not isinstance(raw_locations, list):
            raise ValueError("The world map must contain a locations list.")

        locations: dict[str, Location] = {}
        for raw in raw_locations:
            if not isinstance(raw, dict):
                raise ValueError("Each location must be a JSON object.")
            location_id = raw.get("id")
            name = raw.get("name")
            connections = raw.get("connections", {})
            if not isinstance(location_id, str) or not location_id:
                raise ValueError("Every location needs a non-empty id.")
            if location_id in locations:
                raise ValueError(f"Duplicate location id: {location_id}")
            if not isinstance(name, str) or not isinstance(connections, dict):
                raise ValueError(f"Invalid location data for {location_id}.")
            locations[location_id] = Location(
                id=location_id,
                name=name,
                description=str(raw.get("description", "")),
                background=str(raw.get("background", "")),
                background_image=str(raw.get("background_image", "")),
                music=str(raw.get("music", "")),
                connections=connections,
                npcs=tuple(raw.get("npcs", [])),
                objects=tuple(raw.get("objects", [])),
                gate_id=raw.get("gate_id")
            )

        start_location = data.get("start_location")
        if start_location not in locations:
            raise ValueError("The world map start_location is not defined.")

        for location in locations.values():
            for direction, destination in location.connections.items():
                if direction not in OPPOSITE_DIRECTION:
                    raise ValueError(
                        f"Invalid direction {direction!r} in {location.id}."
                    )
                if destination not in locations:
                    raise ValueError(
                        f"Unknown destination {destination!r} in {location.id}."
                    )
                reverse = OPPOSITE_DIRECTION[direction]
                if locations[destination].connections.get(reverse) != location.id:
                    raise ValueError(
                        f"Connection {location.id} {direction} to {destination} "
                        "must have a matching return connection."
                    )

        self.locations = locations
        self.start_location = start_location

    def get(self, location_id: str) -> Location:
        """Return a location by id, raising a useful error for invalid ids."""
        try:
            return self.locations[location_id]
        except KeyError as error:
            raise ValueError(f"Unknown location: {location_id}") from error

    def exits(self, location_id: str, gate_open: bool = False) -> dict[str, str]:
        """Return usable exits, hiding the chamber until the gate is open."""
        location = self.get(location_id)
        connections = dict(location.connections)
        if location.gate_id and not gate_open:
            connections.pop("S", None)
        return connections