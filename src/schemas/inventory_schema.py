"""Pandera schemas for inventory data validation."""

import pandera.pandas as pa
from pandera.typing.pandas import Series


class RawInventorySchema(pa.DataFrameModel):
    """Schema for raw inventory data before normalization.

    This schema validates the structure of CSV data after column mapping,
    before SKU normalization. Uses coercion for quantity field.
    """

    sku: Series[str] = pa.Field(nullable=False)
    name: Series[str] = pa.Field(nullable=False)
    quantity: Series[int] = pa.Field(coerce=True)
    location: Series[str] = pa.Field(nullable=False)
    last_counted: Series[str] = pa.Field(nullable=False)

    class Config:
        """Pandera schema configuration."""

        strict = False  # Allow extra columns (will flag as quality issue)
        coerce = True


class NormalizedInventorySchema(pa.DataFrameModel):
    """Schema for inventory data after normalization.

    This schema validates data after SKU and name normalization.
    SKUs should match format SKU-NNN after normalization.
    """

    sku: Series[str] = pa.Field(
        str_matches=r"^SKU-\d{3}$",
        description="Normalized SKU in format SKU-NNN",
    )
    name: Series[str] = pa.Field(
        str_length={"min_value": 1},
        description="Product name (trimmed)",
    )
    quantity: Series[int] = pa.Field(
        coerce=True,
        description="Stock count",
    )
    location: Series[str] = pa.Field(
        str_length={"min_value": 1},
        description="Warehouse identifier",
    )
    last_counted: Series[str] = pa.Field(
        description="Date of last inventory count",
    )

    class Config:
        """Pandera schema configuration."""

        strict = False
        coerce = True


# Canonical column names expected after mapping
CANONICAL_COLUMNS = ["sku", "name", "quantity", "location", "last_counted"]
