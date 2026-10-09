
import csv
import json
from pathlib import Path

from .exceptions import PersistenceError
from .models import (
    InventoryItem,
    PerishableItem,
    ElectronicItem,
)
from .manager import InventoryManager


def item_from_dict(data):
    """Recreate an item object from a dictionary."""
    item_type = data.get("item_type", "general")

    common = {
        "item_id": data["item_id"],
        "name": data["name"],
        "quantity": data["quantity"],
        "unit_price": data["unit_price"],
    }

    if item_type == "perishable":
        return PerishableItem(
            **common,
            best_before=data["best_before"]
        )

    if item_type == "electronic":
        return ElectronicItem(
            **common,
            warranty_months=data["warranty_months"]
        )

    if item_type == "general":
        return InventoryItem(**common)

    raise ValueError(f"Unknown item type: {item_type}")


class JSONStorage:
    """Save and load inventory using JSON."""

    def save(self, manager, path):
        try:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)

            target.write_text(
                json.dumps(
                    {"items": manager.to_records()},
                    indent=2
                ),
                encoding="utf-8"
            )
        except (OSError, TypeError, ValueError) as exc:
            raise PersistenceError(
                f"Could not save JSON: {exc}"
            ) from exc

    def load(self, manager, path):
        try:
            payload = json.loads(
                Path(path).read_text(encoding="utf-8")
            )

            if not isinstance(payload, dict):
                raise ValueError("JSON root must be an object")

            records = payload.get("items")
            if not isinstance(records, list):
                raise ValueError("'items' must be a list")

            items = [item_from_dict(record) for record in records]

            # Build a temporary manager so invalid data
            # cannot partially overwrite the existing inventory.
            temporary = InventoryManager()
            for item in items:
                temporary.add_item(item)

            manager._items = temporary._items

        except PersistenceError:
            raise
        except (OSError, json.JSONDecodeError, KeyError,
                TypeError, ValueError) as exc:
            raise PersistenceError(
                f"Could not load JSON: {exc}"
            ) from exc


class CSVStorage:
    """Save and load inventory using CSV."""

    FIELDS = [
        "item_id",
        "name",
        "quantity",
        "unit_price",
        "item_type",
        "best_before",
        "warranty_months",
    ]

    def save(self, manager, path):
        try:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)

            with target.open(
                "w", newline="", encoding="utf-8"
            ) as file:
                writer = csv.DictWriter(
                    file, fieldnames=self.FIELDS
                )
                writer.writeheader()

                for record in manager.to_records():
                    writer.writerow({
                        key: record.get(key, "")
                        for key in self.FIELDS
                    })

        except (OSError, csv.Error, TypeError, ValueError) as exc:
            raise PersistenceError(
                f"Could not save CSV: {exc}"
            ) from exc

    def load(self, manager, path):
        try:
            with Path(path).open(
                "r", newline="", encoding="utf-8"
            ) as file:
                reader = csv.DictReader(file)

                if (
                    reader.fieldnames is None
                    or not set(self.FIELDS).issubset(reader.fieldnames)
                ):
                    raise ValueError(
                        "CSV file is missing required columns"
                    )

                items = []

                for row in reader:
                    record = {
                        "item_id": row["item_id"],
                        "name": row["name"],
                        "quantity": int(row["quantity"]),
                        "unit_price": float(row["unit_price"]),
                        "item_type": row["item_type"],
                    }

                    if record["item_type"] == "perishable":
                        record["best_before"] = row["best_before"]

                    elif record["item_type"] == "electronic":
                        record["warranty_months"] = int(
                            row["warranty_months"]
                        )

                    items.append(item_from_dict(record))

            temporary = InventoryManager()
            for item in items:
                temporary.add_item(item)

            manager._items = temporary._items

        except PersistenceError:
            raise
        except (OSError, csv.Error, KeyError,
                TypeError, ValueError) as exc:
            raise PersistenceError(
                f"Could not load CSV: {exc}"
            ) from exc