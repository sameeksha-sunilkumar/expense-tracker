# Expense Tracker (Python) 

Small CLI-based expense tracker using SQLite + SQLAlchemy.

## Features (required)
- Log daily expenses (via CLI).
- Categorize expenses (e.g., Food, Transport).
- Set monthly budgets per category (and default monthly budgets).
- System alerts if user exceeds a category budget.
- Basic reports:
  - Total spending per month.
  - Compare spending vs budget per category.

## Extra-credit features implemented
- Different budgets per month (budget with `--month YYYY-MM`).
- Custom alerts: check when only X% budget is left (default 10%), adjustable via `--alert-threshold`.
- Uses SQLAlchemy ORM (fulfills SQL/ORM requirement).

> Email notification and group splitting not implemented to keep the app simple and easy to run. Comments in the code explain where to insert SMTP logic if needed.

---

## Quick start (local)
1. Clone the repo.
2. Create and activate a Python virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   
   venv\Scripts\activate      
