-- =============================================================
-- ABC Foodmart Database Schema
-- APAN 5310 - Group 2
-- =============================================================

-- Drop tables in reverse dependency order (if re-running)
ALTER TABLE IF EXISTS Stores DROP CONSTRAINT IF EXISTS fk_stores_manager;

DROP TABLE IF EXISTS Payroll             CASCADE;
DROP TABLE IF EXISTS Expenses            CASCADE;
DROP TABLE IF EXISTS Expense_Categories  CASCADE;
DROP TABLE IF EXISTS Promotions          CASCADE;
DROP TABLE IF EXISTS Transaction_Items   CASCADE;
DROP TABLE IF EXISTS Transactions        CASCADE;
DROP TABLE IF EXISTS Customers           CASCADE;
DROP TABLE IF EXISTS Delivery_Items      CASCADE;
DROP TABLE IF EXISTS Deliveries          CASCADE;
DROP TABLE IF EXISTS Inventory           CASCADE;
DROP TABLE IF EXISTS Products            CASCADE;
DROP TABLE IF EXISTS Vendors             CASCADE;
DROP TABLE IF EXISTS Schedules           CASCADE;
DROP TABLE IF EXISTS Employees           CASCADE;
DROP TABLE IF EXISTS Departments         CASCADE;
DROP TABLE IF EXISTS Stores              CASCADE;


-- =============================================================
-- MODULE 1: STORE & STAFF
-- =============================================================

-- 1. Stores (create without manager_id FK first to avoid circular dependency)
CREATE TABLE Stores (
    store_id      SERIAL          PRIMARY KEY,
    store_name    VARCHAR(100)    NOT NULL,
    address       VARCHAR(200)    NOT NULL,
    borough       VARCHAR(50)     NOT NULL
                                  CHECK (borough IN ('Queens', 'Brooklyn')),
    city          VARCHAR(50)     NOT NULL DEFAULT 'New York',
    zip_code      CHAR(5)         NOT NULL,
    phone         VARCHAR(20)     UNIQUE,
    email         VARCHAR(100),
    open_date     DATE            NOT NULL,
    status        VARCHAR(20)     NOT NULL DEFAULT 'active'
                                  CHECK (status IN ('active', 'closed', 'under_renovation')),
    sq_footage    INTEGER         CHECK (sq_footage > 0),
    manager_id    INTEGER         -- FK added via ALTER TABLE after Employees is created
);

-- 2. Departments
CREATE TABLE Departments (
    dept_id       SERIAL          PRIMARY KEY,
    dept_name     VARCHAR(100)    NOT NULL,
    store_id      INTEGER         NOT NULL
                                  REFERENCES Stores(store_id)
                                  ON DELETE CASCADE,
    UNIQUE (dept_name, store_id)  -- dept name must be unique within a store
);

-- 3. Employees
CREATE TABLE Employees (
    emp_id        SERIAL          PRIMARY KEY,
    first_name    VARCHAR(50)     NOT NULL,
    last_name     VARCHAR(50)     NOT NULL,
    role          VARCHAR(50)     NOT NULL,
    dept_id       INTEGER         REFERENCES Departments(dept_id)
                                  ON DELETE SET NULL,
    store_id      INTEGER         NOT NULL
                                  REFERENCES Stores(store_id)
                                  ON DELETE RESTRICT,
    hire_date     DATE            NOT NULL,
    hourly_wage   NUMERIC(8,2)    NOT NULL CHECK (hourly_wage >= 0),
    email         VARCHAR(100)    UNIQUE,
    phone         VARCHAR(20),
    status        VARCHAR(20)     NOT NULL DEFAULT 'active'
                                  CHECK (status IN ('active', 'inactive', 'terminated'))
);

-- Resolve circular FK: Stores.manager_id -> Employees
ALTER TABLE Stores
    ADD CONSTRAINT fk_stores_manager
    FOREIGN KEY (manager_id)
    REFERENCES Employees(emp_id)
    ON DELETE SET NULL;

-- 4. Schedules
CREATE TABLE Schedules (
    schedule_id   SERIAL          PRIMARY KEY,
    emp_id        INTEGER         NOT NULL
                                  REFERENCES Employees(emp_id)
                                  ON DELETE CASCADE,
    work_date     DATE            NOT NULL,
    shift_start   TIME            NOT NULL,
    shift_end     TIME            NOT NULL,
    CHECK (shift_end > shift_start),
    UNIQUE (emp_id, work_date, shift_start) -- prevent duplicate shifts
);


-- =============================================================
-- MODULE 2: SUPPLY CHAIN & INVENTORY
-- =============================================================

-- 5. Vendors
CREATE TABLE Vendors (
    vendor_id       SERIAL          PRIMARY KEY,
    company_name    VARCHAR(150)    NOT NULL,
    contact_name    VARCHAR(100),
    phone           VARCHAR(20),
    email           VARCHAR(100),
    address         VARCHAR(200)
);

-- 6. Products
CREATE TABLE Products (
    product_id      SERIAL          PRIMARY KEY,
    product_name    VARCHAR(150)    NOT NULL,
    category        VARCHAR(100)    NOT NULL,
    unit_size       VARCHAR(50),
    unit_price      NUMERIC(10,2)   NOT NULL CHECK (unit_price >= 0),
    vendor_id       INTEGER         REFERENCES Vendors(vendor_id)
                                    ON DELETE SET NULL
);

-- 7. Inventory
CREATE TABLE Inventory (
    inventory_id    SERIAL          PRIMARY KEY,
    product_id      INTEGER         NOT NULL
                                    REFERENCES Products(product_id)
                                    ON DELETE CASCADE,
    store_id        INTEGER         NOT NULL
                                    REFERENCES Stores(store_id)
                                    ON DELETE CASCADE,
    quantity        INTEGER         NOT NULL DEFAULT 0
                                    CHECK (quantity >= 0),
    reorder_level   INTEGER         NOT NULL DEFAULT 10
                                    CHECK (reorder_level >= 0),
    last_updated    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (product_id, store_id)   -- one inventory record per product per store
);

-- 8. Deliveries
CREATE TABLE Deliveries (
    delivery_id     SERIAL          PRIMARY KEY,
    vendor_id       INTEGER         NOT NULL
                                    REFERENCES Vendors(vendor_id)
                                    ON DELETE RESTRICT,
    store_id        INTEGER         NOT NULL
                                    REFERENCES Stores(store_id)
                                    ON DELETE RESTRICT,
    delivery_date   DATE            NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'pending'
                                    CHECK (status IN ('pending', 'delivered', 'cancelled'))
);

-- 9. Delivery_Items
CREATE TABLE Delivery_Items (
    item_id         SERIAL          PRIMARY KEY,
    delivery_id     INTEGER         NOT NULL
                                    REFERENCES Deliveries(delivery_id)
                                    ON DELETE CASCADE,
    product_id      INTEGER         NOT NULL
                                    REFERENCES Products(product_id)
                                    ON DELETE RESTRICT,
    quantity        INTEGER         NOT NULL CHECK (quantity > 0),
    unit_cost       NUMERIC(10,2)   NOT NULL CHECK (unit_cost >= 0)
);


-- =============================================================
-- MODULE 3: SALES & CUSTOMERS
-- =============================================================

-- 10. Customers
CREATE TABLE Customers (
    customer_id     SERIAL          PRIMARY KEY,
    first_name      VARCHAR(50)     NOT NULL,
    last_name       VARCHAR(50)     NOT NULL,
    email           VARCHAR(100)    UNIQUE,
    phone           VARCHAR(20),
    loyalty_points  INTEGER         NOT NULL DEFAULT 0
                                    CHECK (loyalty_points >= 0),
    join_date       DATE            NOT NULL DEFAULT CURRENT_DATE
);

-- 11. Transactions
CREATE TABLE Transactions (
    txn_id          SERIAL          PRIMARY KEY,
    store_id        INTEGER         NOT NULL
                                    REFERENCES Stores(store_id)
                                    ON DELETE RESTRICT,
    customer_id     INTEGER         REFERENCES Customers(customer_id)
                                    ON DELETE SET NULL, -- allow guest checkout
    emp_id          INTEGER         REFERENCES Employees(emp_id)
                                    ON DELETE SET NULL,
    txn_date        TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount    NUMERIC(10,2)   NOT NULL CHECK (total_amount >= 0),
    payment_method  VARCHAR(20)     CHECK (payment_method IN ('cash', 'credit', 'debit', 'loyalty'))
);

-- 12. Transaction_Items
CREATE TABLE Transaction_Items (
    item_id         SERIAL          PRIMARY KEY,
    txn_id          INTEGER         NOT NULL
                                    REFERENCES Transactions(txn_id)
                                    ON DELETE CASCADE,
    product_id      INTEGER         NOT NULL
                                    REFERENCES Products(product_id)
                                    ON DELETE RESTRICT,
    quantity        INTEGER         NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(10,2)   NOT NULL CHECK (unit_price >= 0),
    discount        NUMERIC(5,2)    NOT NULL DEFAULT 0.00
                                    CHECK (discount >= 0 AND discount <= 100)
);

-- 13. Promotions
CREATE TABLE Promotions (
    promo_id        SERIAL          PRIMARY KEY,
    product_id      INTEGER         NOT NULL
                                    REFERENCES Products(product_id)
                                    ON DELETE CASCADE,
    promo_name      VARCHAR(150),
    discount_pct    NUMERIC(5,2)    NOT NULL
                                    CHECK (discount_pct > 0 AND discount_pct <= 100),
    start_date      DATE            NOT NULL,
    end_date        DATE            NOT NULL,
    CHECK (end_date >= start_date)
);


-- =============================================================
-- MODULE 4: FINANCE
-- =============================================================

-- 14. Expense_Categories
CREATE TABLE Expense_Categories (
    category_id     SERIAL          PRIMARY KEY,
    category_name   VARCHAR(100)    NOT NULL UNIQUE,
    description     TEXT
);

-- 15. Expenses
CREATE TABLE Expenses (
    expense_id      SERIAL          PRIMARY KEY,
    store_id        INTEGER         NOT NULL
                                    REFERENCES Stores(store_id)
                                    ON DELETE RESTRICT,
    category_id     INTEGER         NOT NULL
                                    REFERENCES Expense_Categories(category_id)
                                    ON DELETE RESTRICT,
    amount          NUMERIC(10,2)   NOT NULL CHECK (amount > 0),
    expense_date    DATE            NOT NULL,
    notes           TEXT
);

-- 16. Payroll
CREATE TABLE Payroll (
    payroll_id      SERIAL          PRIMARY KEY,
    emp_id          INTEGER         NOT NULL
                                    REFERENCES Employees(emp_id)
                                    ON DELETE RESTRICT,
    pay_period      VARCHAR(20)     NOT NULL, -- e.g. '2025-03'
    hours_worked    NUMERIC(6,2)    NOT NULL CHECK (hours_worked >= 0),
    overtime_hours  NUMERIC(6,2)    NOT NULL DEFAULT 0.00 CHECK (overtime_hours >= 0),
    base_pay        NUMERIC(10,2)   NOT NULL CHECK (base_pay >= 0), -- hours_worked * hourly_wage
    overtime        NUMERIC(10,2)   NOT NULL DEFAULT 0.00 CHECK (overtime >= 0), -- overtime_hours * hourly_wage * 1.5
    deductions      NUMERIC(10,2)   NOT NULL DEFAULT 0.00 CHECK (deductions >= 0),
    net_pay         NUMERIC(10,2)   GENERATED ALWAYS AS (base_pay + overtime - deductions) STORED,
    UNIQUE (emp_id, pay_period)     -- one payroll record per employee per period
);


-- =============================================================
-- TRIGGERS
-- =============================================================

-- Trigger 1: Auto-update Inventory.last_updated on quantity change
CREATE OR REPLACE FUNCTION update_inventory_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_inventory_updated
    BEFORE UPDATE ON Inventory
    FOR EACH ROW
    EXECUTE FUNCTION update_inventory_timestamp();


-- Trigger 2: Auto-update Customer loyalty points after each transaction
CREATE OR REPLACE FUNCTION update_loyalty_points()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.customer_id IS NOT NULL THEN
        UPDATE Customers
        SET loyalty_points = loyalty_points + FLOOR(NEW.total_amount)
        WHERE customer_id = NEW.customer_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_loyalty_points
    AFTER INSERT ON Transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_loyalty_points();


-- Trigger 3: Reduce inventory quantity after a sale is recorded
CREATE OR REPLACE FUNCTION reduce_inventory_on_sale()
RETURNS TRIGGER AS $$
DECLARE
    v_store_id INTEGER;
BEGIN
    SELECT store_id INTO v_store_id
    FROM Transactions
    WHERE txn_id = NEW.txn_id;

    UPDATE Inventory
    SET quantity = quantity - NEW.quantity
    WHERE product_id = NEW.product_id
      AND store_id = v_store_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_reduce_inventory
    AFTER INSERT ON Transaction_Items
    FOR EACH ROW
    EXECUTE FUNCTION reduce_inventory_on_sale();


-- =============================================================
-- SAMPLE PROFITABILITY VIEW (supports Business Requirement #15)
-- =============================================================

CREATE OR REPLACE VIEW store_profitability AS
SELECT
    s.store_id,
    s.store_name,
    s.borough,
    COALESCE(SUM(t.total_amount), 0)            AS total_revenue,
    COALESCE(SUM(e.amount), 0)                  AS total_expenses,
    COALESCE(SUM(p.base_pay + p.overtime), 0)   AS total_payroll,
    COALESCE(SUM(t.total_amount), 0)
        - COALESCE(SUM(e.amount), 0)
        - COALESCE(SUM(p.base_pay + p.overtime), 0) AS net_profit
FROM Stores s
LEFT JOIN Transactions t    ON t.store_id = s.store_id
LEFT JOIN Expenses e        ON e.store_id = s.store_id
LEFT JOIN Employees emp     ON emp.store_id = s.store_id
LEFT JOIN Payroll p         ON p.emp_id = emp.emp_id
GROUP BY s.store_id, s.store_name, s.borough;
