-- =====================================================================
--  REVON Hybrid Motorcycle Management System  -  MySQL 8.x schema (DDL)
--  7 tables | 6 foreign keys | CHECK / UNIQUE / NOT NULL / DEFAULT | indexes | views
-- =====================================================================
-- BEGIN-DB-SETUP  (skipped automatically when the database is pre-created by a host)
DROP DATABASE IF EXISTS revon_db;
CREATE DATABASE revon_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE revon_db;
-- END-DB-SETUP

CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name   VARCHAR(100) NOT NULL,
    company     VARCHAR(100) NULL,
    phone       VARCHAR(20)  NOT NULL,
    email       VARCHAR(100) NULL,
    city        VARCHAR(50)  NOT NULL,
    address     VARCHAR(200) NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_cust_phone UNIQUE (phone),
    CONSTRAINT uq_cust_email UNIQUE (email),
    CONSTRAINT ck_cust_email CHECK (email IS NULL OR email LIKE '%_@_%._%')
) ENGINE=InnoDB;

CREATE TABLE staff (
    staff_id       INT AUTO_INCREMENT PRIMARY KEY,
    full_name      VARCHAR(100) NOT NULL,
    employee_no    VARCHAR(30)  NOT NULL,
    phone          VARCHAR(20)  NOT NULL,
    role           VARCHAR(20)  NOT NULL DEFAULT 'Sales Advisor',
    hire_date      DATE NOT NULL,
    experience_yrs INT NOT NULL DEFAULT 0,
    status         VARCHAR(20)  NOT NULL DEFAULT 'Available',
    CONSTRAINT uq_staff_emp UNIQUE (employee_no),
    CONSTRAINT ck_staff_role CHECK (role IN ('Sales Advisor','Technician','Delivery Rider')),
    CONSTRAINT ck_staff_exp CHECK (experience_yrs BETWEEN 0 AND 50),
    CONSTRAINT ck_staff_status CHECK (status IN ('Available','On Delivery','On Leave'))
) ENGINE=InnoDB;

CREATE TABLE bikes (
    bike_id     INT AUTO_INCREMENT PRIMARY KEY,
    vin         VARCHAR(30) NOT NULL,
    bike_type   VARCHAR(20) NOT NULL,
    model_name  VARCHAR(50) NOT NULL,
    color       VARCHAR(30) NOT NULL,
    make_year   INT NOT NULL,
    battery_kwh DECIMAL(5,2) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'In Stock',
    CONSTRAINT uq_bike_vin UNIQUE (vin),
    CONSTRAINT ck_bike_type CHECK (bike_type IN ('City','Sport','Eco','Cargo','Touring','Demo')),
    CONSTRAINT ck_bike_year CHECK (make_year BETWEEN 2020 AND 2040),
    CONSTRAINT ck_bike_batt CHECK (battery_kwh > 0),
    CONSTRAINT ck_bike_status CHECK (status IN ('In Stock','Reserved','Sold','In Service','Demo'))
) ENGINE=InnoDB;

CREATE TABLE models (
    model_id       INT AUTO_INCREMENT PRIMARY KEY,
    model_name     VARCHAR(50) NOT NULL,
    variant        VARCHAR(50) NOT NULL,
    engine_cc      INT NOT NULL,
    battery_kwh    DECIMAL(5,2) NOT NULL,
    range_km       DECIMAL(7,2) NOT NULL,
    top_speed_kmh  INT NOT NULL,
    base_price     DECIMAL(12,2) NOT NULL,
    CONSTRAINT uq_model_variant UNIQUE (model_name, variant),
    CONSTRAINT ck_model_cc CHECK (engine_cc > 0),
    CONSTRAINT ck_model_batt CHECK (battery_kwh > 0),
    CONSTRAINT ck_model_range CHECK (range_km > 0),
    CONSTRAINT ck_model_speed CHECK (top_speed_kmh > 0),
    CONSTRAINT ck_model_price CHECK (base_price >= 0)
) ENGINE=InnoDB;

CREATE TABLE orders (
    order_id      INT AUTO_INCREMENT PRIMARY KEY,
    order_no      VARCHAR(20) NOT NULL,
    customer_id   INT NOT NULL,
    model_id      INT NOT NULL,
    bike_id       INT NULL,
    staff_id      INT NULL,
    items_desc    VARCHAR(150) NOT NULL,
    quantity      INT NOT NULL,
    order_date    DATE NOT NULL,
    delivery_date DATE NULL,
    status        VARCHAR(20) NOT NULL DEFAULT 'Booked',
    total_price   DECIMAL(12,2) NOT NULL DEFAULT 0,
    CONSTRAINT uq_order_no UNIQUE (order_no),
    CONSTRAINT ck_order_qty CHECK (quantity > 0),
    CONSTRAINT ck_order_dates CHECK (delivery_date IS NULL OR delivery_date >= order_date),
    CONSTRAINT ck_order_status CHECK (status IN ('Booked','In Assembly','Delivered','Cancelled')),
    CONSTRAINT ck_order_total CHECK (total_price >= 0),
    CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_order_model FOREIGN KEY (model_id) REFERENCES models(model_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_order_bike FOREIGN KEY (bike_id) REFERENCES bikes(bike_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_order_staff FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE payments (
    payment_id   INT AUTO_INCREMENT PRIMARY KEY,
    order_id     INT NOT NULL,
    amount       DECIMAL(12,2) NOT NULL,
    method       VARCHAR(20) NOT NULL,
    payment_date DATE NOT NULL,
    reference_no VARCHAR(40) NULL,
    CONSTRAINT ck_pay_amount CHECK (amount > 0),
    CONSTRAINT ck_pay_method CHECK (method IN ('Cash','Bank Transfer','Card','Cheque','Online','Installment')),
    CONSTRAINT fk_pay_order FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE service_records (
    service_id   INT AUTO_INCREMENT PRIMARY KEY,
    bike_id      INT NOT NULL,
    service_date DATE NOT NULL,
    service_type VARCHAR(30) NOT NULL,
    description  VARCHAR(200) NULL,
    cost         DECIMAL(10,2) NOT NULL DEFAULT 0,
    CONSTRAINT ck_svc_type CHECK (service_type IN ('Battery Check','Oil Change','Tyre','Engine','Brakes','General Service','Software Update')),
    CONSTRAINT ck_svc_cost CHECK (cost >= 0),
    CONSTRAINT fk_svc_bike FOREIGN KEY (bike_id) REFERENCES bikes(bike_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

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
