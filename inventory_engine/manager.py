
from .models import InventoryItem
from .exceptions import (
    InvalidItemError,
    DuplicateItemError,
    ItemNotFoundError,
)


class InventoryManager:
    """Manages inventory items and their operations."""

    def __init__(self):
        # Encapsulation: internal dictionary stores inventory records.
        self._items = {}

    def add_item(self, item):
        """Add a new item to the inventory."""
        if not isinstance(item, InventoryItem):
            raise InvalidItemError(
                "Only InventoryItem objects can be added"
            )

        if item.item_id in self._items:
            raise DuplicateItemError(
                f"Item ID '{item.item_id}' already exists"
            )

        self._items[item.item_id] = item

    def get_item(self, item_id):
        """Find an item using its unique ID."""
        if item_id not in self._items:
            raise ItemNotFoundError(
                f"Item ID '{item_id}' was not found"
            )

        return self._items[item_id]

    def update_quantity(self, item_id, quantity):
        """Update the quantity of an existing item."""
        item = self.get_item(item_id)
        item.quantity = quantity

    def remove_item(self, item_id):
        """Remove an item and return the removed object."""
        item = self.get_item(item_id)
        del self._items[item_id]
        return item

    def list_items(self):
        """Return inventory items in sorted ID order."""
        return sorted(
            self._items.values(),
            key=lambda item: item.item_id
        )

    def total_stock_value(self):
        """Calculate the total value of all inventory."""
        return round(
            sum(item.stock_value for item in self._items.values()),
            2
        )

    def to_records(self):
        """Convert inventory into dictionaries for storage."""
        return [
            item.to_dict()
            for item in self.list_items()
        ]