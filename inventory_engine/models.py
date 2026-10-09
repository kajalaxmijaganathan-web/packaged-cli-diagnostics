
from datetime import date
from .exceptions import InvalidItemError


class InventoryItem:
    """Base class for all inventory items."""

    def __init__(self, item_id, name, quantity, unit_price):
        self.item_id = item_id
        self.name = name
        self.quantity = quantity
        self.unit_price = unit_price

    @property
    def item_id(self):
        return self._item_id

    @item_id.setter
    def item_id(self, value):
        if not isinstance(value, str) or not value.strip():
            raise InvalidItemError("Item ID cannot be empty")
        self._item_id = value.strip()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str) or not value.strip():
            raise InvalidItemError("Name cannot be empty")
        self._name = value.strip()

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise InvalidItemError("Quantity must be a non-negative integer")
        self._quantity = value

    @property
    def unit_price(self):
        return self._unit_price

    @unit_price.setter
    def unit_price(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise InvalidItemError("Price must be non-negative")
        self._unit_price = float(value)

    @property
    def stock_value(self):
        return round(self.quantity * self.unit_price, 2)

    def item_type(self):
        return "general"

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "name": self.name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "item_type": self.item_type(),
        }


class PerishableItem(InventoryItem):
    """Inventory item with an expiry or best-before date."""

    def __init__(self, item_id, name, quantity, unit_price, best_before):
        super().__init__(item_id, name, quantity, unit_price)

        try:
            date.fromisoformat(best_before)
        except (TypeError, ValueError) as exc:
            raise InvalidItemError(
                "Date must use YYYY-MM-DD format"
            ) from exc

        self.best_before = best_before

    def item_type(self):
        return "perishable"

    def to_dict(self):
        data = super().to_dict()
        data["best_before"] = self.best_before
        return data


class ElectronicItem(InventoryItem):
    """Electronic item with a warranty period."""

    def __init__(
        self, item_id, name, quantity, unit_price, warranty_months
    ):
        super().__init__(item_id, name, quantity, unit_price)

        if (
            isinstance(warranty_months, bool)
            or not isinstance(warranty_months, int)
            or warranty_months < 0
        ):
            raise InvalidItemError(
                "Warranty must be a non-negative integer"
            )

        self.warranty_months = warranty_months

    def item_type(self):
        return "electronic"

    def to_dict(self):
        data = super().to_dict()
        data["warranty_months"] = self.warranty_months
        return data