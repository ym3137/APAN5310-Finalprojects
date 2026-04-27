# APAN5310-Finalprojects
# ABC Foodmart Database System
**APAN 5310 – Group 2 | Columbia University | Spring 2026**

A fully normalized relational database system designed for ABC Foodmart, a five-store neighborhood grocery chain in New York City. This repository contains the complete database schema, ETL script, and ERD definition.

---

## Project Overview

ABC Foodmart operates two existing locations in Queens and three new locations in Brooklyn. This system replaces their legacy spreadsheet and paper-based records with a centralized PostgreSQL database covering:

- Store & Staff management (stores, departments, employees, schedules)
- Supply Chain & Inventory (vendors, products, inventory, deliveries)
- Sales & Customers (transactions, loyalty program, promotions)
- Finance (expenses, payroll, profitability)

The database consists of **16 tables in 3NF**, with automated triggers, a profitability view, and an interactive Metabase dashboard.

---

## Repository Structure

```
abc-foodmart-db/
├── README.md
├── schema/
│   └── abc_foodmart_schema.sql    # Full CREATE TABLE, triggers, and view
├── etl/
│   └── populate_data_fixed.py     # Python ETL script to populate all 16 tables
└── erd/
    └── abc_foodmart.dbml          # DBML for ERD visualization on dbdiagram.io
```

---

## Requirements

- PostgreSQL 15+
- Python 3.10+
- Python packages: `faker`, `psycopg2-binary`

Install dependencies:
```bash
pip install faker psycopg2-binary
```

---

## Setup Instructions

### Step 1 – Create the database

```bash
psql -U postgres -c "CREATE DATABASE abc_foodmart;"
```

### Step 2 – Run the schema

```bash
psql -U postgres -d abc_foodmart -f schema/abc_foodmart_schema.sql
```

This creates all 16 tables, 3 triggers, and the `store_profitability` view.

### Step 3 – Configure the ETL script

Open `etl/populate_data_fixed.py` and update the `DB_CONFIG` section at the top:

```python
DB_CONFIG = {
    "host":     "localhost",   # or your DB host
    "port":     5432,
    "dbname":   "abc_foodmart",
    "user":     "postgres",    # your PostgreSQL username
    "password": "your_password"
}
```

### Step 4 – Run the ETL script

```bash
python etl/populate_data_fixed.py
```

Expected output:
```
Connecting to database...
Inserting data...
  Stores: 5 rows
  Departments: 20 rows
  Employees: 50 rows
  ...
  Payroll: 150 rows
All data inserted successfully.
```

### Step 5 – Verify

```bash
psql -U postgres -d abc_foodmart -c "SELECT COUNT(*) FROM Transactions;"
# Expected: ~1000
```

---

## Database Schema

| Module | Tables |
|--------|--------|
| Store & Staff | Stores, Departments, Employees, Schedules |
| Supply Chain & Inventory | Vendors, Products, Inventory, Deliveries, Delivery_Items |
| Sales & Customers | Customers, Transactions, Transaction_Items, Promotions |
| Finance | Expense_Categories, Expenses, Payroll |

### ERD

View the full ERD on dbdiagram.io by pasting the contents of `erd/abc_foodmart.dbml`:
👉 [dbdiagram.io](https://dbdiagram.io)

### Key Design Decisions

- **Circular FK**: `Stores.manager_id` → `Employees` and `Employees.store_id` → `Stores` creates a circular dependency. Resolved by creating `Stores` first without the FK, then adding it via `ALTER TABLE` after `Employees` is populated.
- **Hourly wages**: Employees store `hourly_wage` rather than annual salary. Payroll records compute `base_pay = hours_worked × hourly_wage` and `overtime = overtime_hours × hourly_wage × 1.5`. `net_pay` is a `GENERATED ALWAYS AS` computed column.
- **Fixed pricing**: `Products.unit_price` is the authoritative retail price. `Transaction_Items.unit_price` is copied from this at time of sale. `Delivery_Items.unit_cost` is set at 50–70% of retail price.
- **Inventory safety**: The ETL script checks available inventory before inserting each `Transaction_Item` to avoid triggering a negative-quantity CHECK violation.

### Triggers

| Trigger | Table | Action |
|---------|-------|--------|
| `trg_reduce_inventory` | Transaction_Items | Decrements inventory after each sale |
| `trg_loyalty_points` | Transactions | Credits loyalty points after each transaction |
| `trg_inventory_updated` | Inventory | Updates `last_updated` timestamp on stock changes |

---

## ETL Notes

- Uses `random.seed(42)` and `Faker.seed(42)` for reproducibility
- All inserts wrapped in a single transaction with rollback on error
- Data is inserted in FK dependency order to maintain referential integrity throughout
- Sample data covers January–April 2025 across all 5 store locations

---

## Dashboard

The executive dashboard is built in **Metabase**, connected to the PostgreSQL instance. It is organized into three tabs:

| Tab | Panels |
|-----|--------|
| Financial Overview | Total Revenue by Store, Labor Cost by Store |
| Sales & Products | Daily Revenue Trend, Top 10 Products by Revenue, Daily Transaction Volume |
| Operations | Inventory Alert, Top 20 Customers by Spend |

---

## Team

| Name | Role |
|------|------|
| Member 1 | Business Analyst |
| Yike Meng (ym3137) | Database Architect |
| Member 2 | Data Engineer |
| Member 3 | Analytics & Reporting Lead |

---

*Columbia University – APAN 5310 – Spring 2025*
