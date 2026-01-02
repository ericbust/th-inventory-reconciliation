## Key Decisions

1. Use pandas for CSV operations for diff and group/agg ops.
2. Using panderas for data quailty checks
3. Pytest for testing suite
4. Not sure if I need to handle normalization/reconciliation or flag, I'll likely normalize AND flag
5. I am assuming SKU + Warehouse as the natural key
6. I will be using speckit + claude code to plan and implement

## Quality Check Ideas

1. Column naming inconsistencies
2. Key/ID format
3. Numeric issues, float vs string, range
4. Duplicate rows
5. Text quality like name drift, typos, spaces
6. Date format consistencies
7. Added/Removed items
