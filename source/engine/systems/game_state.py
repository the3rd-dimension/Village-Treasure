"""Story progression and validated player interactions."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import config
from engine.inventory.inventory import Inventory
from engine.inventory.item import Item
from engine.utilities.logger import get_logger
from engine.world.world_manager import WorldManager, load_game_data


logger = get_logger("game_state")
USE_LOCATIONS = {
    "old_rope": "L03",
    "rusty_key": "L10",
    "old_coin": "L06",
    "lantern": "L07",
    "old_photograph": "L05",
    "sun_medallion": "L12",
}


@dataclass(frozen=True, slots=True)
class ActionResult:
    message: str = ""
    speaker: str = ""
    lines: tuple[str, ...] = ()


class GameState:
    """Stores the player's progress independently from Pygame presentation."""

    def __init__(self, world: WorldManager | None = None, data_dir: Path | None = None) -> None:
        self.world = world or WorldManager()
        root = data_dir or config.DATA_DIR
        raw_items = load_game_data(root / "items" / "items.json")
        raw_characters = load_game_data(root / "characters" / "characters.json")
        self.dialogue: dict[str, Any] = load_game_data(root / "dialogue" / "dialogue.json")
        self.characters: dict[str, dict[str, Any]] = raw_characters
        self.items: dict[str, Item] = {}
        for item_id, values in raw_items.items():
            if not isinstance(values, dict):
                raise ValueError(f"Invalid item definition: {item_id}")
            color = values.get("color", [120, 120, 120])
            if (
                not isinstance(color, list)
                or len(color) != 3
                or any(not isinstance(channel, int) or not 0 <= channel <= 255 for channel in color)
            ):
                raise ValueError(f"Invalid item color: {item_id}")
            usage_requirements = values.get("usage_requirements", {})
            if not isinstance(usage_requirements, dict):
                raise ValueError(f"Invalid item usage requirements: {item_id}")
            self.items[item_id] = Item(
                id=item_id,
                name=str(values.get("name", item_id.replace("_", " ").title())),
                description=str(values.get("description", "")),
                icon=str(values.get("icon", "")),
                color=(color[0], color[1], color[2]),
                usage_requirements=usage_requirements,
            )

        self.inventory = Inventory(capacity=4)
        self.player_name = ""
        self.location_id = self.world.start_location
        self.visited = {self.location_id}
        self.collected: set[str] = set()
        self.met_mira = False
        self.photograph_shown = False
        self.mill_unlocked = False
        self.in_mill_storage = False
        self.coin_traded = False
        self.medallion_found = False
        self.gate_open = False
        self.shrine_discovered = False
        self.completed = False
        self.actions_data = load_game_data(root / "actions.json")

    @property
    def location(self):
        return self.world.get(self.location_id)

    @property
    def quest_step(self) -> str:
        if self.completed:
            return "Treasure discovered"
        for step in self.actions_data.get("quests", []):
            # Basic requirement checking
            req = step.get("requirement")
            if req == "met_mira" and self.met_mira:
                return step.get("target")
            if req == "old_rope_collected" and "old_rope" in self.collected:
                return step.get("target")
            if req == "mill_unlocked" and self.mill_unlocked:
                return step.get("target")
            if req == "coin_traded" and self.coin_traded:
                return step.get("target")
            if req == "medallion_found" and self.medallion_found:
                return step.get("target")
            if req == "gate_open" and self.gate_open:
                return step.get("target")
            if req == "at_l13" and self.location_id == "L13":
                return step.get("target")

        # Fallback if none met or missing
        return "Continue your journey"

    def start(self, player_name: str) -> ActionResult:
        name = " ".join(player_name.strip().split())[:20] or "Traveler"
        self.player_name = name
        lines = tuple(self.dialogue["intro"])
        return ActionResult(
            speaker="Willowmere",
            lines=tuple(line.format(player=name) for line in lines),
        )

    def exits(self) -> dict[str, str]:
        return self.world.exits(self.location_id, self.gate_open)

    def destination_for(self, direction: str) -> str | None:
        return self.exits().get(direction)

    def move_to(self, destination: str) -> bool:
        if destination not in self.exits().values():
            return False
        self.location_id = destination
        self.visited.add(destination)
        self.in_mill_storage = False
        logger.info("Player entered %s.", self.location.name)
        return True

    def actions(self) -> list[tuple[str, str]]:
        """Return only the actions currently available at this location."""
        actions: list[tuple[str, str]] = []
        location_id = self.location_id

        for npc_id in self.location.npcs:
            character = self.characters.get(npc_id, {})
            npc_name = character.get("name", npc_id.title())
            actions.append((f"talk:{npc_id}", f"Talk with {npc_name}"))

        if location_id in self.actions_data:
            for action in self.actions_data[location_id]:
                condition = action.get("condition")
                if not condition or self._check_condition(condition):
                    actions.append((action["id"], action["label"]))

        selected = self.inventory.selected_item
        if (
            selected is not None
            and USE_LOCATIONS.get(selected.id) == location_id
            and self._can_use(selected.id)
        ):
            actions.append(("use_selected", f"Use {selected.name} here"))
        return actions

    def _check_condition(self, condition: str) -> bool:
        if condition == "not_collected:old_rope":
            return "old_rope" not in self.collected
        if condition == "not_collected:old_photograph":
            return "old_photograph" not in self.collected
        if condition == "in_storage_and_not_collected:old_coin":
            return self.in_mill_storage and "old_coin" not in self.collected
        if condition == "in_storage":
            return self.in_mill_storage
        if condition == "unlocked_and_not_in_storage":
            return self.mill_unlocked and not self.in_mill_storage
        if condition == "not_discovered:shrine":
            return not self.shrine_discovered
        if condition == "not_completed":
            return not self.completed
        return True

    def select_item(self, item_id: str) -> str:
        if not self.inventory.select(item_id):
            return "That item is not in your bag."
        selected = self.inventory.selected_item
        if selected is None:
            return "That item is not in your bag."
        return selected.description

    def perform(self, action_id: str) -> ActionResult:
        """Apply a visible action, rejecting invalid actions without side effects."""
        if action_id not in {identifier for identifier, _ in self.actions()}:
            return ActionResult(message="That action is not available here.")

        if action_id.startswith("talk:"):
            return self._talk(action_id.partition(":")[2])
        if action_id.startswith("pickup:"):
            return self._pick_up(action_id.partition(":")[2])
        if action_id == "use_selected":
            return self._use_selected()
        if action_id == "examine:noticeboard":
            return self._say("locations", "noticeboard")
        if action_id == "read:shrine":
            self.shrine_discovered = True
            return self._say("locations", "shrine")
        if action_id == "enter_storage":
            self.in_mill_storage = True
            return ActionResult(message="You enter the mill storage room.")
        if action_id == "leave_storage":
            self.in_mill_storage = False
            return ActionResult(message="You return to the mill's main room.")
        if action_id == "open:chest":
            self.completed = True
            return self._say("locations", "ending")
        return ActionResult(message="That action is not available here.")

    def _can_use(self, item_id: str) -> bool:
        item = self.items.get(item_id)
        if not item:
            return False

        reqs = item.usage_requirements
        if reqs.get("location") and reqs.get("location") != self.location_id:
            return False

        for key, value in reqs.items():
            if key == "location":
                continue

            current_val = getattr(self, key, None)
            if current_val != value:
                return False

        return True

    def _pick_up(self, item_id: str) -> ActionResult:
        item = self.items.get(item_id)
        if item is None or item_id in self.collected:
            return ActionResult(message="That item is no longer here.")
        if not self.inventory.add(item):
            return ActionResult(message="Your bag is full!")
        self.collected.add(item_id)
        return ActionResult(message=f"You collected the {item.name}.")

    def _use_selected(self) -> ActionResult:
        item = self.inventory.selected_item
        if item is None:
            return ActionResult(message="Select an item from your bag first.")
        if not self.inventory.has(item.id):
            return ActionResult(message="You don't have the required item.")
        if not self._can_use(item.id):
            return ActionResult(message="That item cannot be used here.")

        if item.id == "old_rope":
            self.inventory.remove(item.id)
            pickup = self._pick_up("rusty_key")
            return ActionResult(
                message=f"You used the Old Rope. {pickup.message}"
            )
        if item.id == "rusty_key":
            self.inventory.remove(item.id)
            self.mill_unlocked = True
            return ActionResult(message="You used the Rusty Key. The mill storage is unlocked.")
        if item.id == "old_coin":
            self.inventory.remove(item.id)
            if not self.inventory.add(self.items["lantern"]):
                self.inventory.add(item)
                return ActionResult(message="Your bag is full!")
            self.coin_traded = True
            self.collected.add("lantern")
            return ActionResult(message="You traded the Old Coin for a Lantern.")
        if item.id == "lantern":
            medallion = self.items["sun_medallion"]
            if not self.inventory.add(medallion):
                return ActionResult(message="Your bag is full!")
            self.medallion_found = True
            self.collected.add("sun_medallion")
            return ActionResult(message="The lantern reveals the Sun Medallion at the altar.")
        if item.id == "old_photograph":
            self.photograph_shown = True
            return self._say("mira", "photograph", "You showed the Old Photograph to Mira.")
        if item.id == "sun_medallion":
            self.gate_open = True
            return ActionResult(
                message="You presented the Sun Medallion. The Treasure Gate opens.",
                speaker="Bram",
                lines=tuple(self.dialogue["bram"]["open"]),
            )
        return ActionResult(message="That item cannot be used here.")

    def _talk(self, npc_id: str) -> ActionResult:
        if npc_id == "mira":
            if not self.met_mira:
                self.met_mira = True
                return self._say("mira", "first_meeting")
            if self.photograph_shown:
                return self._say("mira", "after_photograph")
            return self._say("mira", "met")
        if npc_id == "elias":
            if self.coin_traded:
                return self._say("elias", "traded")
            if self.inventory.has("old_coin"):
                return self._say("elias", "coin")
            return self._say("elias", "greeting")
        if npc_id == "thomas":
            if self.mill_unlocked:
                return self._say("thomas", "storage_open")
            if self.inventory.has("rusty_key"):
                return self._say("thomas", "key_found")
            return self._say("thomas", "greeting")
        if npc_id == "bram":
            return self._say("bram", "open" if self.gate_open else "locked")
        return ActionResult(message="There is no one here to talk to.")

    def _say(
        self,
        group: str,
        key: str,
        message: str = "",
    ) -> ActionResult:
        lines = tuple(self.dialogue[group][key])
        return ActionResult(
            message=message,
            speaker=self.characters.get(group, {}).get("name", group.title()),
            lines=lines,
        )
