
class InventoryError(Exception):
    """Base exception for inventory-related errors."""


class InvalidItemError(InventoryError, ValueError):
    """Raised when item data is invalid."""


class DuplicateItemError(InventoryError):
    """Raised when an item ID already exists."""


class ItemNotFoundError(InventoryError, LookupError):
    """Raised when an item cannot be found."""


class PersistenceError(InventoryError):
    """Raised when saving or loading data fails."""