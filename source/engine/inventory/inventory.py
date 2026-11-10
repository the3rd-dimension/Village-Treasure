"""Four-slot player inventory with selection and item inspection."""
from __future__ import annotations

from engine.inventory.item import Item


class Inventory:
    """Stores unique items and the currently selected item."""

    def __init__(self, capacity: int = 4) -> None:
        if capacity <= 0:
            raise ValueError("Inventory capacity must be positive.")
        self.capacity = capacity
        self._items: list[Item] = []
        self.selected_id: str | None = None

    @property
    def items(self) -> tuple[Item, ...]:
        return tuple(self._items)

    @property
    def selected_item(self) -> Item | None:
        return next((item for item in self._items if item.id == self.selected_id),None)

    def has(self, item_id: str) -> bool:
        return any(item.id == item_id for item in self._items)

    def add(self, item: Item) -> bool:
        if self.has(item.id) or len(self._items) >= self.capacity:
            return False
        self._items.append(item)
        if self.selected_id is None:
            self.selected_id = item.id
        return True

    def remove(self, item_id: str) -> Item | None:
        for index, item in enumerate(self._items):
            if item.id == item_id:
                removed = self._items.pop(index)
                if self.selected_id == item_id:
                    self.selected_id = self._items[0].id if self._items else None
                return removed
        return None

    def select(self, item_id: str) -> bool:
        if not self.has(item_id):
            return False
        self.selected_id = item_id
        return True