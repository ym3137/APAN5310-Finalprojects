"""
ABC Foodmart - Sample Data Population Script
APAN 5310 - Group 2

Requirements:
    pip install faker psycopg2-binary

Usage:
    python populate_data.py

Database connection: update DB_CONFIG below before running.
"""

import random
import psycopg2
from faker import Faker
from datetime import date, timedelta, datetime
from decimal import Decimal

fake = Faker()
random.seed(42)
Faker.seed(42)

# ---------------------------------------------------------------
# DATABASE CONNECTION — update before running
# ---------------------------------------------------------------
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "abc_foodmart",
    "user":     "postgres",
    "password": "your_password"
}

# ---------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------

def connect():
    return psycopg2.connect(**DB_CONFIG)

def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


# ---------------------------------------------------------------
# MODULE 1: STORE & STAFF
# ---------------------------------------------------------------

def insert_stores(cur):
    """5 stores: 2 existing Queens, 3 new Brooklyn."""
    stores = [
        ("ABC Foodmart Queens #1", "82-10 Jamaica Ave",    "Queens",   "11421", "(718) 555-0101", "queens1@abcfoodmart.com",  date(1995, 3, 15), "active",  8400),
        ("ABC Foodmart Queens #2", "37-20 Junction Blvd",  "Queens",   "11372", "(718) 555-0102", "queens2@abcfoodmart.com",  date(2003, 7, 22), "active",  7200),
        ("ABC Foodmart Brooklyn #1","450 Fulton St",        "Brooklyn", "11201", "(718) 555-0103", "brooklyn1@abcfoodmart.com",date(2025, 1, 10), "active",  9100),
        ("ABC Foodmart Brooklyn #2","1205 Atlantic Ave",    "Brooklyn", "11216", "(718) 555-0104", "brooklyn2@abcfoodmart.com",date(2025, 2, 28), "active",  8800),
        ("ABC Foodmart Brooklyn #3","786 Flatbush Ave",     "Brooklyn", "11226", "(718) 555-0105", "brooklyn3@abcfoodmart.com",date(2025, 4,  1), "active",  7600),
    ]
    ids = []
    for s in stores:
        cur.execute("""
            INSERT INTO Stores (store_name, address, borough, zip_code, phone, email,
                                open_date, status, sq_footage)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING store_id
        """, s)
        ids.append(cur.fetchone()[0])
    print(f"  Stores: {len(ids)} rows")
    return ids


def insert_departments(cur, store_ids):
    """4 departments per store."""
    dept_names = ["Produce", "Bakery", "Dairy & Frozen", "Cashiers"]
    ids = []
    for sid in store_ids:
        for name in dept_names:
            cur.execute("""
                INSERT INTO Departments (dept_name, store_id)
                VALUES (%s, %s) RETURNING dept_id
            """, (name, sid))
            ids.append((cur.fetchone()[0], sid))
    print(f"  Departments: {len(ids)} rows")
    return ids  # list of (dept_id, store_id)


def insert_employees(cur, store_ids, dept_rows):
    """~10 employees per store = 50 total."""
    roles = ["Cashier", "Stock Associate", "Department Lead", "Assistant Manager", "Store Manager"]
    ids = []
    # group dept_ids by store
    store_depts = {}
    for dept_id, sid in dept_rows:
        store_depts.setdefault(sid, []).append(dept_id)

    for sid in store_ids:
        for _ in range(10):
            role = random.choice(roles)
            dept_id = random.choice(store_depts[sid])
            hire = random_date(date(2015, 1, 1), date(2025, 3, 1))
            # hourly wages: Cashier ~$16-18, Stock ~$17-20, Lead ~$20-25, Asst Mgr ~$25-32, Mgr ~$30-40
            wage_ranges = {
                "Cashier":           (16.00, 18.50),
                "Stock Associate":   (17.00, 20.00),
                "Department Lead":   (20.00, 25.00),
                "Assistant Manager": (25.00, 32.00),
                "Store Manager":     (30.00, 40.00),
            }
            lo, hi = wage_ranges[role]
            hourly_wage = round(random.uniform(lo, hi), 2)
            cur.execute("""
                INSERT INTO Employees
                    (first_name, last_name, role, dept_id, store_id,
                     hire_date, hourly_wage, email, phone, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'active')
                RETURNING emp_id
            """, (
                fake.first_name(), fake.last_name(), role, dept_id, sid,
                hire, hourly_wage,
                fake.unique.email(), fake.numerify("(###) ###-####")
            ))
            ids.append((cur.fetchone()[0], sid))
    print(f"  Employees: {len(ids)} rows")
    return ids  # list of (emp_id, store_id)


def assign_managers(cur, store_ids, emp_rows):
    """Assign one manager per store."""
    store_emps = {}
    for emp_id, sid in emp_rows:
        store_emps.setdefault(sid, []).append(emp_id)
    for sid in store_ids:
        manager = random.choice(store_emps[sid])
        cur.execute("UPDATE Stores SET manager_id = %s WHERE store_id = %s", (manager, sid))
    print(f"  Managers assigned to {len(store_ids)} stores")


def insert_schedules(cur, emp_rows):
    """~12 schedule entries per employee (3 weeks of shifts)."""
    count = 0
    for emp_id, _ in emp_rows:
        shifts_added = set()
        attempts = 0
        while len(shifts_added) < 12 and attempts < 30:
            attempts += 1
            work_date = random_date(date(2025, 1, 1), date(2025, 3, 31))
            start_hour = random.choice([7, 9, 13, 15])
            start = f"{start_hour:02d}:00"
            end   = f"{start_hour + 8:02d}:00"
            key = (emp_id, str(work_date), start)
            if key in shifts_added:
                continue
            shifts_added.add(key)
            cur.execute("""
                INSERT INTO Schedules (emp_id, work_date, shift_start, shift_end)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT DO NOTHING
            """, (emp_id, work_date, start, end))
            count += 1
    print(f"  Schedules: {count} rows")


# ---------------------------------------------------------------
# MODULE 2: SUPPLY CHAIN & INVENTORY
# ---------------------------------------------------------------

def insert_vendors(cur):
    vendor_data = [
        ("FreshFarms Wholesale",     "Carlos Rivera",   "(212) 555-1001", "carlos@freshfarms.com",    "123 Market St, NYC"),
        ("Metro Dairy Supply",       "Linda Chen",      "(212) 555-1002", "linda@metrodairy.com",     "456 Dairy Rd, NJ"),
        ("BakePro Distributors",     "James O'Brien",   "(212) 555-1003", "james@bakepro.com",        "789 Flour Ave, NYC"),
        ("Green Valley Produce",     "Sofia Patel",     "(212) 555-1004", "sofia@greenvalley.com",    "321 Farm Ln, CT"),
        ("National Frozen Foods",    "Marcus Williams", "(212) 555-1005", "marcus@natfrozen.com",     "654 Cold St, NYC"),
        ("Sunrise Beverage Co",      "Priya Nair",      "(212) 555-1006", "priya@sunrisebev.com",     "987 Drink Blvd, NJ"),
        ("QuickSnack Wholesale",     "Tom Nguyen",      "(212) 555-1007", "tom@quicksnack.com",       "147 Snack Way, NYC"),
        ("Harbor Seafood Supply",    "Elena Vasquez",   "(212) 555-1008", "elena@harborseafood.com",  "258 Harbor Dr, NYC"),
    ]
    ids = []
    for v in vendor_data:
        cur.execute("""
            INSERT INTO Vendors (company_name, contact_name, phone, email, address)
            VALUES (%s,%s,%s,%s,%s) RETURNING vendor_id
        """, v)
        ids.append(cur.fetchone()[0])
    print(f"  Vendors: {len(ids)} rows")
    return ids


def insert_products(cur, vendor_ids):
    categories = {
        "Produce":        [("Bananas","1 bunch",0.99), ("Apples","3 lb bag",3.49), ("Spinach","5 oz bag",2.99),
                           ("Tomatoes","1 lb",1.99), ("Carrots","2 lb bag",1.49), ("Broccoli","1 head",1.79),
                           ("Strawberries","1 pint",3.99), ("Avocados","each",1.29), ("Oranges","4 lb bag",4.49),
                           ("Lettuce","1 head",1.99)],
        "Dairy & Frozen": [("Whole Milk","1 gallon",3.99), ("2% Milk","1 gallon",3.79), ("Cheddar Cheese","8 oz",4.49),
                           ("Greek Yogurt","32 oz",5.99), ("Butter","1 lb",4.99), ("Frozen Peas","16 oz",1.99),
                           ("Ice Cream","1 quart",4.49), ("Cream Cheese","8 oz",3.49), ("Sour Cream","16 oz",2.99),
                           ("Orange Juice","64 oz",4.99)],
        "Bakery":         [("White Bread","20 oz loaf",2.99), ("Whole Wheat Bread","24 oz",3.49),
                           ("Bagels","6 pack",3.99), ("Muffins","4 pack",4.49), ("Croissants","4 pack",5.49),
                           ("Dinner Rolls","12 pack",3.29), ("Sourdough Loaf","24 oz",4.99),
                           ("Tortillas","10 pack",2.99), ("Pita Bread","8 pack",3.49), ("Rye Bread","24 oz",3.79)],
        "Beverages":      [("Coca-Cola","12 pack",6.99), ("Pepsi","12 pack",6.49), ("Spring Water","24 pack",4.99),
                           ("Orange Juice","52 oz",4.49), ("Apple Juice","64 oz",3.99), ("Sparkling Water","12 pack",7.99),
                           ("Iced Tea","64 oz",2.99), ("Sports Drink","6 pack",5.99), ("Coffee","12 oz bag",8.99),
                           ("Green Tea","20 bags",4.49)],
        "Snacks":         [("Potato Chips","8 oz",3.49), ("Tortilla Chips","13 oz",4.29), ("Pretzels","16 oz",3.99),
                           ("Mixed Nuts","10 oz",7.99), ("Granola Bars","6 pack",4.99), ("Popcorn","3 pack",3.49),
                           ("Crackers","13 oz",3.99), ("Rice Cakes","4.5 oz",3.29), ("Trail Mix","12 oz",5.49),
                           ("Cookies","13 oz",4.49)],
    }
    ids = []
    prices = {}  # product_id -> Decimal price
    for category, items in categories.items():
        vendor_id = random.choice(vendor_ids)
        for name, size, price in items:
            cur.execute("""
                INSERT INTO Products (product_name, category, unit_size, unit_price, vendor_id)
                VALUES (%s,%s,%s,%s,%s) RETURNING product_id
            """, (name, category, size, price, vendor_id))
            pid = cur.fetchone()[0]
            ids.append(pid)
            prices[pid] = Decimal(str(price))
    print(f"  Products: {len(ids)} rows")
    return ids, prices


def insert_inventory(cur, product_ids, store_ids):
    count = 0
    for pid in product_ids:
        for sid in store_ids:
            qty     = random.randint(20, 200)
            reorder = random.randint(10, 30)
            cur.execute("""
                INSERT INTO Inventory (product_id, store_id, quantity, reorder_level, last_updated)
                VALUES (%s,%s,%s,%s, CURRENT_TIMESTAMP)
                ON CONFLICT DO NOTHING
            """, (pid, sid, qty, reorder))
            count += 1
    print(f"  Inventory: {count} rows")


def insert_deliveries_and_items(cur, vendor_ids, store_ids, product_ids, product_prices):
    delivery_ids = []
    # ~6 deliveries per store
    for sid in store_ids:
        for _ in range(6):
            vid    = random.choice(vendor_ids)
            d_date = random_date(date(2025, 1, 1), date(2025, 4, 1))
            status = random.choice(["delivered", "delivered", "delivered", "pending", "cancelled"])
            cur.execute("""
                INSERT INTO Deliveries (vendor_id, store_id, delivery_date, status)
                VALUES (%s,%s,%s,%s) RETURNING delivery_id
            """, (vid, sid, d_date, status))
            delivery_ids.append(cur.fetchone()[0])

    # 3–6 items per delivery
    # unit_cost = 50–70% of retail price (fixed per product, realistic wholesale margin)
    count = 0
    for did in delivery_ids:
        for pid in random.sample(product_ids, random.randint(3, 6)):
            qty       = random.randint(10, 100)
            retail    = product_prices[pid]
            unit_cost = round(float(retail) * random.uniform(0.50, 0.70), 2)
            cur.execute("""
                INSERT INTO Delivery_Items (delivery_id, product_id, quantity, unit_cost)
                VALUES (%s,%s,%s,%s)
            """, (did, pid, qty, unit_cost))
            count += 1
    print(f"  Deliveries: {len(delivery_ids)} rows")
    print(f"  Delivery_Items: {count} rows")


# ---------------------------------------------------------------
# MODULE 3: SALES & CUSTOMERS
# ---------------------------------------------------------------

def insert_customers(cur):
    ids = []
    for _ in range(200):
        join = random_date(date(2020, 1, 1), date(2025, 3, 1))
        cur.execute("""
            INSERT INTO Customers (first_name, last_name, email, phone, loyalty_points, join_date)
            VALUES (%s,%s,%s,%s,%s,%s) RETURNING customer_id
        """, (
            fake.first_name(), fake.last_name(),
            fake.unique.email(), fake.numerify("(###) ###-####"),
            random.randint(0, 2000), join
        ))
        ids.append(cur.fetchone()[0])
    print(f"  Customers: {len(ids)} rows")
    return ids


def insert_transactions_and_items(cur, store_ids, customer_ids, emp_rows, product_ids, product_prices):
    store_emps = {}
    for emp_id, sid in emp_rows:
        store_emps.setdefault(sid, []).append(emp_id)

    payment_methods = ["cash", "credit", "debit", "loyalty"]
    txn_ids = []

    # ~200 transactions per store = 1000 total
    for sid in store_ids:
        for _ in range(200):
            cid    = random.choice(customer_ids + [None, None])  # some guest checkouts
            emp_id = random.choice(store_emps[sid])
            txn_dt = fake.date_time_between(start_date=date(2025, 1, 1), end_date=date(2025, 4, 1))
            method = random.choice(payment_methods)
            cur.execute("""
                INSERT INTO Transactions
                    (store_id, customer_id, emp_id, txn_date, total_amount, payment_method)
                VALUES (%s,%s,%s,%s, 0, %s) RETURNING txn_id
            """, (sid, cid, emp_id, txn_dt, method))
            txn_ids.append((cur.fetchone()[0], sid))

    # 2-6 items per transaction
    # unit_price pulled from product_prices dict (fixed retail price from Products table)
    # Check inventory before inserting to avoid CHECK constraint violation (quantity >= 0)
    item_count = 0
    for txn_id, sid in txn_ids:
        total = Decimal("0.00")
        for pid in random.sample(product_ids, random.randint(2, 6)):
            cur.execute("SELECT quantity FROM Inventory WHERE product_id = %s AND store_id = %s", (pid, sid))
            row = cur.fetchone()
            if row is None or row[0] <= 0:
                continue
            qty      = min(random.randint(1, 5), row[0])
            price    = product_prices[pid]
            discount = Decimal(str(random.choice([0, 0, 0, 5, 10, 15])))
            cur.execute("""
                INSERT INTO Transaction_Items
                    (txn_id, product_id, quantity, unit_price, discount)
                VALUES (%s,%s,%s,%s,%s)
            """, (txn_id, pid, qty, price, discount))
            line_total = price * qty * (1 - discount / 100)
            total += line_total
            item_count += 1
        cur.execute("UPDATE Transactions SET total_amount = %s WHERE txn_id = %s",
                    (round(total, 2), txn_id))

    print(f"  Transactions: {len(txn_ids)} rows")
    print(f"  Transaction_Items: {item_count} rows")


def insert_promotions(cur, product_ids):
    count = 0
    for pid in random.sample(product_ids, 20):
        start = random_date(date(2025, 1, 1), date(2025, 3, 1))
        end   = start + timedelta(days=random.randint(7, 30))
        disc  = random.choice([5, 10, 15, 20, 25])
        cur.execute("""
            INSERT INTO Promotions (product_id, promo_name, discount_pct, start_date, end_date)
            VALUES (%s,%s,%s,%s,%s)
        """, (pid, f"{disc}% Off Promotion", disc, start, end))
        count += 1
    print(f"  Promotions: {count} rows")


# ---------------------------------------------------------------
# MODULE 4: FINANCE
# ---------------------------------------------------------------

def insert_expense_categories(cur):
    cats = [
        ("Rent",         "Monthly store lease payments"),
        ("Utilities",    "Electricity, water, and gas bills"),
        ("Supplies",     "Cleaning and office supplies"),
        ("Maintenance",  "Equipment repair and store upkeep"),
        ("Marketing",    "Local advertising and promotions"),
        ("Insurance",    "Store and liability insurance"),
        ("Miscellaneous","Other operating expenses"),
    ]
    ids = []
    for name, desc in cats:
        cur.execute("""
            INSERT INTO Expense_Categories (category_name, description)
            VALUES (%s,%s) RETURNING category_id
        """, (name, desc))
        ids.append(cur.fetchone()[0])
    print(f"  Expense_Categories: {len(ids)} rows")
    return ids


def insert_expenses(cur, store_ids, category_ids):
    count = 0
    # ~10 expense entries per store per month, 3 months
    for sid in store_ids:
        for month in range(1, 4):
            for _ in range(10):
                cid    = random.choice(category_ids)
                amount = round(random.uniform(200, 8000), 2)
                edate  = date(2025, month, random.randint(1, 28))
                cur.execute("""
                    INSERT INTO Expenses (store_id, category_id, amount, expense_date)
                    VALUES (%s,%s,%s,%s)
                """, (sid, cid, amount, edate))
                count += 1
    print(f"  Expenses: {count} rows")


def insert_payroll(cur, emp_rows):
    """Calculate pay from hourly_wage stored in Employees table."""
    count = 0
    for emp_id, _ in emp_rows:
        # fetch this employee's hourly wage
        cur.execute("SELECT hourly_wage FROM Employees WHERE emp_id = %s", (emp_id,))
        hourly_wage = float(cur.fetchone()[0])

        for month in range(1, 4):
            period         = f"2025-{month:02d}"
            hours_worked   = round(random.uniform(120, 168), 2)   # ~3–4 weeks of full-time
            overtime_hours = round(random.uniform(0, 15), 2)
            base_pay       = round(hours_worked * hourly_wage, 2)
            overtime       = round(overtime_hours * hourly_wage * 1.5, 2)
            deductions     = round(random.uniform(50, 400), 2)
            cur.execute("""
                INSERT INTO Payroll
                    (emp_id, pay_period, hours_worked, overtime_hours, base_pay, overtime, deductions)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING
            """, (emp_id, period, hours_worked, overtime_hours, base_pay, overtime, deductions))
            count += 1
    print(f"  Payroll: {count} rows")


# ---------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------

def main():
    print("Connecting to database...")
    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        print("\nInserting data...")

        # Module 1
        store_ids  = insert_stores(cur)
        dept_rows  = insert_departments(cur, store_ids)
        emp_rows   = insert_employees(cur, store_ids, dept_rows)
        assign_managers(cur, store_ids, emp_rows)
        insert_schedules(cur, emp_rows)

        # Module 2
        vendor_ids            = insert_vendors(cur)
        product_ids, product_prices = insert_products(cur, vendor_ids)
        insert_inventory(cur, product_ids, store_ids)
        insert_deliveries_and_items(cur, vendor_ids, store_ids, product_ids, product_prices)

        # Module 3
        customer_ids = insert_customers(cur)
        insert_transactions_and_items(cur, store_ids, customer_ids, emp_rows, product_ids, product_prices)
        insert_promotions(cur, product_ids)

        # Module 4
        category_ids = insert_expense_categories(cur)
        insert_expenses(cur, store_ids, category_ids)
        insert_payroll(cur, emp_rows)

        conn.commit()
        print("\nAll data inserted successfully.")

    except Exception as e:
        conn.rollback()
        print(f"\nError: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
