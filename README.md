# invoice-flow

A Finance demo built to match a BI Developer / AI agents job: supplier invoices moving
from received → approved → paid, shown in a Power BI dashboard, then automated with
Power Automate and answered by a Copilot Studio agent.

## The data (`data/`, made by `python3 tools/make_data.py`)

| File | Kind | One row is |
|---|---|---|
| `invoices.csv` | fact table | one invoice |
| `suppliers.csv` | dimension | one supplier |
| `departments.csv` | dimension | one department |

The export is dated 2026-09-26. Like a real Finance export, it is not clean —
finding and fixing the problems in Power Query is part of the exercise.
