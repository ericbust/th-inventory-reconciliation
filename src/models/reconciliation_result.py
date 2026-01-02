"""Reconciliation result data model."""

from dataclasses import dataclass
from typing import Literal, Optional


ReconciliationStatus = Literal["unchanged", "quantity_changed", "added", "removed"]


@dataclass
class ReconciliationResult:
    """Represents the comparison outcome for a single inventory item.

    Status definitions:
    - unchanged: Item exists in both snapshots with identical quantity
    - quantity_changed: Item exists in both snapshots with different quantity
    - added: Item exists only in snapshot_2
    - removed: Item exists only in snapshot_1
    """

    sku: str
    location: str
    status: ReconciliationStatus
    old_quantity: Optional[int] = None
    new_quantity: Optional[int] = None
    quantity_delta: Optional[int] = None
    old_name: Optional[str] = None
    new_name: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "sku": self.sku,
            "location": self.location,
            "status": self.status,
            "old_quantity": self.old_quantity,
            "new_quantity": self.new_quantity,
            "quantity_delta": self.quantity_delta,
            "old_name": self.old_name,
            "new_name": self.new_name,
        }
