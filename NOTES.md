## Quickstart

Reference the quickstart.md file in specs/001-inventory-reconciliation for full details

## Key Decisions

1. Use pandas for CSV operations for diff and group/agg ops
2. Using panderas for data quailty checks
3. Pytest for testing suite
4. Not sure if I need to handle normalization/reconciliation or flag, I'll likely normalize AND flag
5. I am assuming SKU + Warehouse as the natural key
6. I will be using speckit + claude code to plan and implement

## Quality Check Ideas

1. Column naming inconsistencies
2. Key/ID format
3. Numeric issues, float vs string, negative range
4. Duplicate rows
5. Text quality like name drift, typos, spaces
6. Date format consistencies, dates in comparison that are in the past
7. Assign levels, error, warning, info depending on severity. Error would be breaking changes like dupe keys, missing columns, etc

## General Notes

I approached this with the mindset of knowing how data quality is paramount to the authenticity of Ground Signal. This meant that I spent the majority of my time evaluating what tools I would use, engineering context based on the initial requirements and my initial thoughts of quality checks, and prompting a spec that can be followed. I required that the AI to follow a test driven style to make sure that it can always be double checking its work as the phases were implemented.

I ended up going with pandas for CSV processing, normalization, merging, and to take advantage of DataFrames to be used in tandem with panderas for data quality checks. The majority of the data quality checks that I initially thought of seemed to be ok, but I did end up prompting in a few more as I was validating my output like when the quantities had to be normalized which I wasn't reporting on before but is useful to identify data entry or parsing issues.

I used GitHub's speckit which I've been using recently. It is overkill for a take home task but it follows how I tend to work with AI which is spending time up front planning, letting the AI implement, and reviewing its output and adjusting/iterating the output or tasks as needed.

## Quality Issues Found

1. Column name differences
2. Column type differences - quantities (int vs float), dates (iso vs other)
3. Name drift for items
4. SKU's not normalized (SKU005 vs SKU-005, casing)
5. White space issues in string values (spaces and random quotes)
