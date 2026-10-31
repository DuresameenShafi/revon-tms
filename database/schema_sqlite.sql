-- Same schema for SQLite mode (zero-setup / Vercel)
PRAGMA foreign_keys = ON;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name   TEXT NOT NULL,
    company     TEXT,
    phone       TEXT NOT NULL UNIQUE,
    email       TEXT UNIQUE CHECK (email IS NULL OR email LIKE '%_@_%._%'),
    city        TEXT NOT NULL,
    address     TEXT,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE staff (
    staff_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name      TEXT NOT NULL,
    employee_no    TEXT NOT NULL UNIQUE,
    phone          TEXT NOT NULL,
    role           TEXT NOT NULL DEFAULT 'Sales Advisor' CHECK (role IN ('Sales Advisor','Technician','Delivery Rider')),
    hire_date      TEXT NOT NULL,
    experience_yrs INTEGER NOT NULL DEFAULT 0 CHECK (experience_yrs BETWEEN 0 AND 50),
    status         TEXT NOT NULL DEFAULT 'Available' CHECK (status IN ('Available','On Delivery','On Leave'))
);

CREATE TABLE bikes (
    bike_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    vin         TEXT NOT NULL UNIQUE,
    bike_type   TEXT NOT NULL CHECK (bike_type IN ('City','Sport','Eco','Cargo','Touring','Demo')),
    model_name  TEXT NOT NULL,
    color       TEXT NOT NULL,
    make_year   INTEGER NOT NULL CHECK (make_year BETWEEN 2020 AND 2040),
    battery_kwh REAL NOT NULL CHECK (battery_kwh > 0),
    status      TEXT NOT NULL DEFAULT 'In Stock' CHECK (status IN ('In Stock','Reserved','Sold','In Service','Demo'))
);

CREATE TABLE models (
    model_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name    TEXT NOT NULL,
    variant       TEXT NOT NULL,
    engine_cc     INTEGER NOT NULL CHECK (engine_cc > 0),
    battery_kwh   REAL NOT NULL CHECK (battery_kwh > 0),
    range_km      REAL NOT NULL CHECK (range_km > 0),
    top_speed_kmh INTEGER NOT NULL CHECK (top_speed_kmh > 0),
    base_price    REAL NOT NULL CHECK (base_price >= 0),
    UNIQUE (model_name, variant)
);

CREATE TABLE orders (
    order_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no      TEXT NOT NULL UNIQUE,
    customer_id   INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    model_id      INTEGER NOT NULL REFERENCES models(model_id)       ON DELETE RESTRICT ON UPDATE CASCADE,
    bike_id       INTEGER REFERENCES bikes(bike_id) ON DELETE SET NULL ON UPDATE CASCADE,
    staff_id      INTEGER REFERENCES staff(staff_id) ON DELETE SET NULL ON UPDATE CASCADE,
    items_desc    TEXT NOT NULL,
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    order_date    TEXT NOT NULL,
    delivery_date TEXT,
    status        TEXT NOT NULL DEFAULT 'Booked' CHECK (status IN ('Booked','In Assembly','Delivered','Cancelled')),
    total_price   REAL NOT NULL DEFAULT 0 CHECK (total_price >= 0),
    CHECK (delivery_date IS NULL OR delivery_date >= order_date)
);

CREATE TABLE payments (
    payment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    amount       REAL NOT NULL CHECK (amount > 0),
    method       TEXT NOT NULL CHECK (method IN ('Cash','Bank Transfer','Card','Cheque','Online','Installment')),
    payment_date TEXT NOT NULL,
    reference_no TEXT
);

CREATE TABLE service_records (
    service_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id      INTEGER NOT NULL REFERENCES bikes(bike_id) ON DELETE CASCADE ON UPDATE CASCADE,
    service_date TEXT NOT NULL,
    service_type TEXT NOT NULL CHECK (service_type IN ('Battery Check','Oil Change','Tyre','Engine','Brakes','General Service','Software Update')),
    description  TEXT,
    cost         REAL NOT NULL DEFAULT 0 CHECK (cost >= 0)
);

CREATE INDEX idx_order_status ON orders(status);
CREATE INDEX idx_order_date   ON orders(order_date);

CREATE VIEW v_order_details AS
SELECT o.order_id, o.order_no, o.items_desc, o.quantity, o.order_date, o.delivery_date,
       o.status, o.total_price,
       c.customer_id, c.full_name AS customer_name, c.city AS customer_city,
       m.model_id, m.model_name, m.variant,
       b.bike_id, b.vin,
       s.staff_id, s.full_name AS staff_name,
       COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.order_id = o.order_id), 0) AS paid
FROM orders o
INNER JOIN customers c ON c.customer_id = o.customer_id
INNER JOIN models m    ON m.model_id    = o.model_id
LEFT  JOIN bikes b     ON b.bike_id     = o.bike_id
LEFT  JOIN staff s     ON s.staff_id    = o.staff_id;

CREATE VIEW v_bike_service_summary AS
SELECT b.bike_id, b.vin, b.model_name, b.status,
       COUNT(sr.service_id) AS services, COALESCE(SUM(sr.cost), 0) AS total_service_cost
FROM bikes b
LEFT JOIN service_records sr ON sr.bike_id = b.bike_id
GROUP BY b.bike_id, b.vin, b.model_name, b.status;
