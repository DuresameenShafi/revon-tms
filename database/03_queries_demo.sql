-- =====================================================================
--  REVON - SQL demo script (MySQL 8).  Run statement by statement (Ctrl+Enter).
-- =====================================================================
USE revon_db;

-- ---------------- PART A: CRUD ----------------
INSERT INTO customers (full_name, phone, email, city) VALUES ('Demo Rider','0399-0000001','demo.rider@example.com','Karachi');
SELECT * FROM customers ORDER BY customer_id DESC LIMIT 3;
UPDATE customers SET city = 'Lahore' WHERE phone = '0399-0000001';
DELETE FROM customers WHERE phone = '0399-0000001';

-- ---------------- PART B: JOINS ----------------
-- INNER JOIN
SELECT o.order_no, c.full_name, m.model_name, m.variant, o.total_price
FROM orders o INNER JOIN customers c ON c.customer_id = o.customer_id
              INNER JOIN models m ON m.model_id = o.model_id;
-- LEFT JOIN (customers with no orders still appear)
SELECT c.full_name, COUNT(o.order_id) AS orders
FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.full_name;
-- RIGHT JOIN (bikes that are not on any order)
SELECT b.vin, o.order_no FROM orders o RIGHT JOIN bikes b ON b.bike_id = o.bike_id;
-- SELF JOIN (customers living in the same city)
SELECT a.full_name AS customer_1, b.full_name AS customer_2, a.city
FROM customers a JOIN customers b ON a.city = b.city AND a.customer_id < b.customer_id;

-- ---------------- PART C: AGGREGATES / GROUP BY / HAVING ----------------
SELECT COUNT(*) AS orders, SUM(total_price) AS revenue, AVG(total_price) AS avg_order,
       MAX(total_price) AS max_order, MIN(total_price) AS min_order FROM orders WHERE status <> 'Cancelled';
SELECT m.model_name, SUM(o.quantity) AS units, SUM(o.total_price) AS revenue
FROM orders o JOIN models m ON m.model_id = o.model_id GROUP BY m.model_name ORDER BY revenue DESC;
SELECT customer_id, SUM(total_price) AS spent FROM orders GROUP BY customer_id HAVING SUM(total_price) > 500000;

-- ---------------- PART D: SUB-QUERIES ----------------
SELECT * FROM models WHERE base_price > (SELECT AVG(base_price) FROM models);                 -- scalar
SELECT * FROM bikes WHERE bike_id NOT IN (SELECT bike_id FROM service_records);                -- NOT IN
SELECT order_no, total_price FROM orders o
WHERE total_price > (SELECT COALESCE(SUM(amount),0) FROM payments p WHERE p.order_id = o.order_id);  -- correlated

-- ---------------- PART E: VIEWS ----------------
SELECT * FROM v_order_details WHERE status = 'Booked';
SELECT * FROM v_bike_service_summary ORDER BY total_service_cost DESC;

-- ---------------- PART F: DDL (ALTER / DROP) ----------------
ALTER TABLE customers ADD COLUMN loyalty_points INT DEFAULT 0;
ALTER TABLE customers DROP COLUMN loyalty_points;
CREATE TABLE temp_demo (id INT PRIMARY KEY, note VARCHAR(30));
DROP TABLE temp_demo;

-- ---------------- PART G: STORED PROCEDURE + FUNCTION ----------------
DELIMITER //
DROP PROCEDURE IF EXISTS sp_customer_history//
CREATE PROCEDURE sp_customer_history(IN p_customer_id INT)
BEGIN
    SELECT o.order_no, m.model_name, m.variant, o.status, o.total_price
    FROM orders o JOIN models m ON m.model_id = o.model_id
    WHERE o.customer_id = p_customer_id ORDER BY o.order_date;
END//

DROP FUNCTION IF EXISTS fn_order_balance//
CREATE FUNCTION fn_order_balance(p_order_id INT) RETURNS DECIMAL(12,2) READS SQL DATA
BEGIN
    DECLARE v_total DECIMAL(12,2);
    DECLARE v_paid  DECIMAL(12,2);
    SELECT total_price INTO v_total FROM orders WHERE order_id = p_order_id;
    SELECT COALESCE(SUM(amount),0) INTO v_paid FROM payments WHERE order_id = p_order_id;
    RETURN v_total - v_paid;
END//
DELIMITER ;
CALL sp_customer_history(1);
SELECT order_no, fn_order_balance(order_id) AS balance_due FROM orders;

-- ---------------- PART H: TRIGGERS ----------------
CREATE TABLE IF NOT EXISTS order_status_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY, order_id INT, old_status VARCHAR(20),
    new_status VARCHAR(20), changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
DELIMITER //
DROP TRIGGER IF EXISTS trg_order_delivered//
CREATE TRIGGER trg_order_delivered BEFORE UPDATE ON orders FOR EACH ROW
BEGIN
    IF NEW.status = 'Delivered' AND OLD.status <> 'Delivered' AND NEW.delivery_date IS NULL THEN
        SET NEW.delivery_date = CURDATE();
    END IF;
END//
DROP TRIGGER IF EXISTS trg_order_status_log//
CREATE TRIGGER trg_order_status_log AFTER UPDATE ON orders FOR EACH ROW
BEGIN
    IF NEW.status <> OLD.status THEN
        INSERT INTO order_status_log (order_id, old_status, new_status) VALUES (NEW.order_id, OLD.status, NEW.status);
    END IF;
END//
DELIMITER ;
UPDATE orders SET status = 'Delivered' WHERE order_no = 'RVN-2026-0009';
SELECT order_no, status, delivery_date FROM orders WHERE order_no = 'RVN-2026-0009';
SELECT * FROM order_status_log;

-- ---------------- PART I: TRANSACTIONS ----------------
START TRANSACTION;
UPDATE bikes SET status = 'Sold' WHERE vin = 'REVNX26A000108';
SELECT vin, status FROM bikes WHERE vin = 'REVNX26A000108';
ROLLBACK;                                   -- undo
START TRANSACTION;
INSERT INTO payments (order_id, amount, method, payment_date) VALUES (11, 50000, 'Cash', CURDATE());
COMMIT;                                     -- keep

-- ---------------- PART J: CONSTRAINT TESTS (each statement must FAIL) ----------------
INSERT INTO orders (order_no, customer_id, model_id, items_desc, quantity, order_date, total_price)
VALUES ('RVN-2026-0001', 1, 1, 'dup', 1, '2026-10-01', 1);               -- UNIQUE
INSERT INTO orders (order_no, customer_id, model_id, items_desc, quantity, order_date, total_price)
VALUES ('RVN-TEST-1', 1, 1, 'bad qty', -5, '2026-10-01', 1);             -- CHECK quantity > 0
UPDATE orders SET delivery_date = '2020-01-01' WHERE order_id = 1;       -- CHECK delivery >= order date
INSERT INTO orders (order_no, customer_id, model_id, items_desc, quantity, order_date, total_price)
VALUES ('RVN-TEST-2', 999, 1, 'no customer', 1, '2026-10-01', 1);        -- FOREIGN KEY
DELETE FROM customers WHERE customer_id = 1;                             -- ON DELETE RESTRICT
DELETE FROM bikes WHERE bike_id = 1;                                     -- SET NULL on orders (succeeds)
DELETE FROM orders WHERE order_id = 2;                                   -- CASCADE payments (succeeds)

-- ---------------- PART K: DCL ----------------
CREATE USER IF NOT EXISTS 'revon_viewer'@'localhost' IDENTIFIED BY 'View#1234';
GRANT SELECT ON revon_db.* TO 'revon_viewer'@'localhost';
SHOW GRANTS FOR 'revon_viewer'@'localhost';
REVOKE SELECT ON revon_db.* FROM 'revon_viewer'@'localhost';
DROP USER 'revon_viewer'@'localhost';
