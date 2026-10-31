-- Sample data for REVON Hybrid Motorcycle Management System
-- 11 customers, 9 staff, 9 bikes, 8 models, 15 orders, 13 payments, 8 service records
USE revon_db;

INSERT INTO customers (full_name, company, phone, email, city, address) VALUES
('Ahmed Raza',        NULL,                       '0300-1110001', 'ahmed.raza@example.com',    'Karachi',   'Block 5, Clifton'),
('Sana Malik',        NULL,                       '0301-1110002', 'sana.malik@example.com',    'Lahore',    'Model Town'),
('Bilal Hussain',     NULL,                       '0302-1110003', 'bilal.h@example.com',       'Karachi',   'Gulshan-e-Iqbal'),
('Imran Qureshi',     'Karachi Wheels Dealership','0303-1110004', 'imran@karachiwheels.example','Karachi',  'Shahrah-e-Faisal'),
('Hina Tariq',        NULL,                       '0304-1110005', 'hina.tariq@example.com',    'Islamabad', 'F-8 Markaz'),
('Usman Ali',         NULL,                       '0305-1110006', 'usman.ali@example.com',     'Faisalabad','Peoples Colony'),
('Zain Abbas',        'SwiftCourier Pvt Ltd',     '0306-1110007', 'zain@swiftcourier.example', 'Karachi',   'SITE Area'),
('Fatima Noor',       NULL,                       '0307-1110008', 'fatima.noor@example.com',   'Karachi',   'DHA Phase 6'),
('Hamza Sheikh',      NULL,                       '0308-1110009', 'hamza.s@example.com',       'Lahore',    'Johar Town'),
('Ayesha Khan',       NULL,                       '0309-1110010', 'ayesha.khan@example.com',   'Hyderabad', 'Qasimabad'),
('Omar Farooq',       NULL,                       '0310-1110011', 'omar.farooq@example.com',   'Karachi',   'North Nazimabad');

INSERT INTO staff (full_name, employee_no, phone, role, hire_date, experience_yrs, status) VALUES
('Kamran Siddiqui','EMP-001','0321-2220001','Sales Advisor','2024-02-01',6,'Available'),
('Nida Fatima',    'EMP-002','0321-2220002','Sales Advisor','2024-05-15',4,'Available'),
('Rashid Mehmood', 'EMP-003','0321-2220003','Delivery Rider','2024-07-01',8,'On Delivery'),
('Faisal Iqbal',   'EMP-004','0321-2220004','Delivery Rider','2025-01-10',3,'Available'),
('Tahir Aziz',     'EMP-005','0321-2220005','Delivery Rider','2025-03-20',5,'On Leave'),
('Saba Rehman',    'EMP-006','0321-2220006','Technician','2024-03-01',7,'Available'),
('Adnan Ghani',    'EMP-007','0321-2220007','Technician','2024-09-01',9,'Available'),
('Mariam Butt',    'EMP-008','0321-2220008','Sales Advisor','2025-06-01',2,'Available'),
('Junaid Akhtar',  'EMP-009','0321-2220009','Technician','2025-08-11',1,'Available');

INSERT INTO models (model_name, variant, engine_cc, battery_kwh, range_km, top_speed_kmh, base_price) VALUES
('REVON City',  '125 Standard', 125, 1.80, 380, 90,  285000),
('REVON City',  '125 Plus',     125, 2.40, 420, 95,  310000),
('REVON City',  '150 Standard', 150, 2.40, 440, 105, 335000),
('REVON Sport', '200 Standard', 200, 3.00, 460, 125, 395000),
('REVON Sport', '200 Pro',      200, 3.60, 480, 135, 445000),
('REVON Eco',   '100 Lite',     100, 1.50, 350, 80,  245000),
('REVON Cargo', '150 Rider',    150, 3.00, 400, 85,  365000),
('REVON Touring','250 Edition', 250, 4.20, 520, 140, 520000);

INSERT INTO bikes (vin, bike_type, model_name, color, make_year, battery_kwh, status) VALUES
('REVNX26A000101','City',   'REVON City 125 Standard', 'Matte Green',  2026, 1.80, 'Sold'),
('REVNX26A000102','City',   'REVON City 150 Standard', 'Graphite',     2026, 2.40, 'Sold'),
('REVNX26A000103','Sport',  'REVON Sport 200 Standard','Racing Red',   2026, 3.00, 'Sold'),
('REVNX26A000104','Eco',    'REVON Eco 100 Lite',      'Pearl White',  2026, 1.50, 'Sold'),
('REVNX26A000105','Sport',  'REVON Sport 200 Pro',     'Midnight Black',2026,3.60, 'Reserved'),
('REVNX26A000106','Cargo',  'REVON Cargo 150 Rider',   'Safety Orange',2026, 3.00, 'In Service'),
('REVNX26A000107','Touring','REVON Touring 250 Edition','Titanium',    2026, 4.20, 'Reserved'),
('REVNX26A000108','City',   'REVON City 150 Standard', 'Ocean Blue',   2026, 2.40, 'Reserved'),
('REVNX26A000109','Demo',   'REVON Sport 200 Standard','Racing Red',   2026, 3.00, 'Demo');

INSERT INTO orders (order_no, customer_id, model_id, bike_id, staff_id, items_desc, quantity, order_date, delivery_date, status, total_price) VALUES
('RVN-2026-0001', 1, 1, 1,    1,    'Helmet and phone mount',      1,  '2026-01-12','2026-01-20','Delivered',   285000),
('RVN-2026-0002', 2, 3, 2,    2,    'Riding gear set',             1,  '2026-02-03','2026-02-10','Delivered',   335000),
('RVN-2026-0003', 3, 4, 3,    1,    'Extended warranty add-on',    1,  '2026-02-18','2026-02-26','Delivered',   395000),
('RVN-2026-0004', 4, 2, NULL, NULL, 'Dealer stock order',          5,  '2026-03-05','2026-03-25','Delivered',  1550000),
('RVN-2026-0005', 5, 6, 4,    3,    'Fast charger',                1,  '2026-03-22','2026-03-30','Delivered',   245000),
('RVN-2026-0006', 6, 5, 5,    2,    'Pro tuning pack',             1,  '2026-04-08', NULL,       'In Assembly', 445000),
('RVN-2026-0007', 1, 7, 6,    3,    'Cargo box fitting',           1,  '2026-04-15','2026-04-22','Delivered',   365000),
('RVN-2026-0008', 7, 1, NULL, NULL, 'Corporate fleet order',       10, '2026-05-02', NULL,       'In Assembly',2850000),
('RVN-2026-0009', 8, 8, 7,    4,    'Touring luggage kit',         1,  '2026-05-20', NULL,       'Booked',      520000),
('RVN-2026-0010', 2, 6, NULL, NULL, 'Spare battery',               1,  '2026-06-03','2026-06-10','Delivered',   245000),
('RVN-2026-0011', 9, 3, 8,    1,    'Anti-theft tracker',          1,  '2026-06-18', NULL,       'Booked',      335000),
('RVN-2026-0012', 3, 4, NULL, NULL, 'Test ride follow-up',         1,  '2026-07-07', NULL,       'Cancelled',   395000),
('RVN-2026-0013', 10,2, NULL, 5,    'Windshield',                  1,  '2026-07-21', NULL,       'Booked',      310000),
('RVN-2026-0014', 5, 5, NULL, NULL, 'Sport seat upgrade',          1,  '2026-08-09', NULL,       'Booked',      445000),
('RVN-2026-0015', 4, 7, NULL, NULL, 'Delivery fleet order',        3,  '2026-09-01', NULL,       'Booked',     1095000);

INSERT INTO payments (order_id, amount, method, payment_date, reference_no) VALUES
(1,  285000,'Bank Transfer','2026-01-12','BT-1001'),
(2,  100000,'Cash',         '2026-02-03','CSH-2001'),
(2,  235000,'Bank Transfer','2026-02-12','BT-1002'),
(3,  395000,'Card',         '2026-02-18','CARD-3301'),
(4,  800000,'Bank Transfer','2026-03-05','BT-1003'),
(4,  750000,'Cheque',       '2026-03-25','CHQ-778812'),
(5,  245000,'Online',       '2026-03-22','ONL-5521'),
(6,  200000,'Cash',         '2026-04-08','CSH-2002'),
(7,  365000,'Bank Transfer','2026-04-15','BT-1004'),
(8, 1000000,'Bank Transfer','2026-05-02','BT-1005'),
(9,  100000,'Online',       '2026-05-20','ONL-5522'),
(10, 245000,'Cash',         '2026-06-03','CSH-2003'),
(11, 150000,'Installment',  '2026-06-18','INS-0001');

INSERT INTO service_records (bike_id, service_date, service_type, description, cost) VALUES
(1,'2026-03-01','General Service','First free service',2500),
(2,'2026-04-10','Battery Check','Battery health and capacity test',1500),
(3,'2026-05-15','Tyre','Rear tyre replaced',6500),
(6,'2026-06-01','Battery Check','Capacity test after heavy cargo use',1500),
(1,'2026-07-20','Brakes','Brake pad replacement',3200),
(4,'2026-08-02','Software Update','Mode-controller firmware update (Eco/City/Sport)',0),
(9,'2026-08-15','Oil Change','Demo bike service - ICE side',1800),
(5,'2026-09-10','General Service','Pre-delivery inspection',2000);
