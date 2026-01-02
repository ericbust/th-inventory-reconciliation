"""Inventory item data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class InventoryItem:
    """Represents a single inventory record from a snapshot CSV file.

    Natural Key: (sku, location) - composite key for matching between snapshots.
    """

    sku: str
    name: str
    quantity: int
    location: str
    last_counted: str

    def __post_init__(self) -> None:
        """Validate inventory item after initialization."""
        if not self.sku:
            raise ValueError("SKU cannot be empty")
        if not self.name:
            raise ValueError("Name cannot be empty")
        if not self.location:
            raise ValueError("Location cannot be empty")

    @property
    def key(self) -> tuple[str, str]:
        """Return the composite key (sku, location) for matching."""
        return (self.sku, self.location)
