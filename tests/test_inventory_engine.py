
import pytest

from inventory_engine import (
    InventoryItem,
    PerishableItem,
    ElectronicItem,
    InventoryManager,
    JSONStorage,
    CSVStorage,
    InvalidItemError,
    DuplicateItemError,
    ItemNotFoundError,
    PersistenceError,
)


@pytest.fixture
def manager():
    inventory = InventoryManager()
    inventory.add_item(InventoryItem("A1", "Book", 5, 10))
    inventory.add_item(
        PerishableItem("B1", "Milk", 2, 30, "2027-01-31")
    )
    inventory.add_item(
        ElectronicItem("C1", "Mouse", 3, 500, 12)
    )
    return inventory


def test_stock_value_and_polymorphism(manager):
    assert manager.get_item("A1").stock_value == 50
    assert manager.get_item("B1").item_type() == "perishable"
    assert manager.get_item("C1").item_type() == "electronic"
    assert manager.total_stock_value() == 1610


def test_invalid_item_data():
    with pytest.raises(InvalidItemError):
        InventoryItem("", "Book", 2, 10)

    with pytest.raises(InvalidItemError):
        InventoryItem("A1", "Book", -1, 10)

    with pytest.raises(InvalidItemError):
        InventoryItem("A1", "Book", 2, -10)


def test_invalid_subclass_data():
    with pytest.raises(InvalidItemError):
        PerishableItem("B1", "Milk", 2, 30, "invalid-date")

    with pytest.raises(InvalidItemError):
        ElectronicItem("C1", "Mouse", 2, 500, -1)


def test_add_duplicate_item(manager):
    with pytest.raises(DuplicateItemError):
        manager.add_item(InventoryItem("A1", "Another book", 1, 5))


def test_find_missing_item(manager):
    with pytest.raises(ItemNotFoundError):
        manager.get_item("missing")


def test_update_and_remove_item(manager):
    manager.update_quantity("A1", 8)
    assert manager.get_item("A1").quantity == 8

    removed = manager.remove_item("A1")
    assert removed.name == "Book"

    with pytest.raises(ItemNotFoundError):
        manager.get_item("A1")


def test_invalid_quantity_update(manager):
    with pytest.raises(InvalidItemError):
        manager.update_quantity("A1", -5)


@pytest.mark.parametrize(
    "storage_class, filename",
    [
        (JSONStorage, "inventory.json"),
        (CSVStorage, "inventory.csv"),
    ],
)
def test_save_and_load(storage_class, filename, manager, tmp_path):
    path = tmp_path / filename
    storage = storage_class()

    storage.save(manager, path)

    loaded = InventoryManager()
    storage.load(loaded, path)

    assert loaded.to_records() == manager.to_records()


def test_json_invalid_document(manager, tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text('{"wrong": []}', encoding="utf-8")

    with pytest.raises(PersistenceError):
        JSONStorage().load(manager, path)


def test_missing_json_file(manager, tmp_path):
    with pytest.raises(PersistenceError):
        JSONStorage().load(manager, tmp_path / "missing.json")


def test_missing_csv_file(manager, tmp_path):
    with pytest.raises(PersistenceError):
        CSVStorage().load(manager, tmp_path / "missing.csv")


def test_csv_missing_columns(manager, tmp_path):
    path = tmp_path / "invalid.csv"
    path.write_text("item_id,name\nA1,Book\n", encoding="utf-8")

    with pytest.raises(PersistenceError):
        CSVStorage().load(manager, path)