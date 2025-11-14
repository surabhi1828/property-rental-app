-- ===============================================
-- DML COMMANDS (Data Insertion for Presentation)
-- Executes after the DDL has created the schema.
-- ===============================================

-- Reset AUTO_INCREMENT counters to start IDs from the desired values for demonstration
ALTER TABLE OWNER AUTO_INCREMENT = 101;
ALTER TABLE TENANT AUTO_INCREMENT = 201;
ALTER TABLE PROPERTY AUTO_INCREMENT = 301;
ALTER TABLE OCCUPANCY AUTO_INCREMENT = 1;
ALTER TABLE REVIEW AUTO_INCREMENT = 401;
ALTER TABLE PAYMENTS AUTO_INCREMENT = 501;


-- 1. OWNER DATA (3 Entries)
INSERT INTO OWNER (owner_id, name, phone, email, bank_details) VALUES
(101, 'Anil Sharma', '9876543210', 'anil.sharma@example.com', 'HDFC Bank, A/C: 1234567890'),
(102, 'Bhavna Kulkarni', '8765432109', 'bhavna.k@example.com', 'ICICI Bank, A/C: 0987654321'),
(103, 'Chetan Desai', '7654321098', 'chetan.d@example.com', 'SBI Bank, A/C: 1122334455');

-- 2. TENANT DATA (4 Entries)
INSERT INTO TENANT (tenant_id, name, phone, email, id_proof) VALUES
(201, 'Devika Patel', '6543210987', 'devika.p@example.com', 'Aadhar Card'),
(202, 'Eshan Kapoor', '5432109876', 'eshan.k@example.com', 'Passport'),
(203, 'Farah Ali', '4321098765', 'farah.a@example.com', 'Voter ID'),
(204, 'Gaurav Singh', '3210987654', 'gaurav.s@example.com', 'Driving License');

-- 3. PROPERTY DATA (5 Entries - Linked to OWNER)
INSERT INTO PROPERTY (property_id, owner_id, address, city, description, sq_footage, monthly_rent, status) VALUES
(301, 101, '1A, Green Heights Apts', 'Bengaluru', '2BHK with balcony', 1200, 25000.00, 'Rented'),
(302, 101, '5B, Park View Villa', 'Bengaluru', 'Studio apartment near metro', 600, 15000.00, 'Rented'),
(303, 102, '203, Lake Side Tower', 'Mumbai', '3BHK, fully furnished', 1500, 45000.00, 'Available'),
(304, 103, 'B-4, Royal Residency', 'Delhi', '1BHK, unfurnished', 750, 18000.00, 'Rented'),
(305, 103, 'C-9, Shivaji Nagar', 'Pune', 'Large 4BHK house', 2500, 55000.00, 'Available');

-- 4. OCCUPANCY DATA (5 Entries - Links TENANT and PROPERTY - Historical and Current)
INSERT INTO OCCUPANCY (occupancy_id, tenant_id, property_id, start_date, end_date) VALUES
(1, 201, 301, '2024-01-15', NULL), -- Current: Devika in Prop 301
(2, 202, 302, '2025-03-01', NULL), -- Current: Eshan in Prop 302
(3, 203, 304, '2024-11-20', NULL), -- Current: Farah in Prop 304
(4, 204, 302, '2023-01-01', '2025-02-28'), -- Historical: Gaurav in Prop 302
(5, 201, 304, '2023-05-01', '2024-10-31'); -- Historical: Devika in Prop 304

-- 5. REVIEW DATA (3 Entries - Links TENANT and PROPERTY)
INSERT INTO REVIEW (review_id, tenant_id, property_id, rating, comment, review_date) VALUES
(401, 204, 302, 4, 'Great location, well maintained.', '2025-03-05'),
(402, 201, 304, 2, 'Property was old, lots of maintenance needed.', '2024-11-01'),
(403, 202, 302, 5, 'Perfect studio, quick maintenance response.', '2025-04-10');

-- 6. PAYMENTS DATA (10 Entries - Links to OCCUPANCY ID)
INSERT INTO PAYMENTS (payment_id, occupancy_id, amount, payment_date, month_year, method, status) VALUES
-- Payments for current tenancy (Occu_ID 1)
(501, 1, 25000.00, '2025-08-01', '2025-08', 'UPI', 'Paid'),
(502, 1, 25000.00, '2025-09-03', '2025-09', 'Bank Transfer', 'Late'), 
(503, 1, 25000.00, '2025-10-01', '2025-10', 'UPI', 'Paid'),

-- Payments for current tenancy (Occu_ID 2)
(504, 2, 15000.00, '2025-08-28', '2025-09', 'Cash', 'Pending'), 
(505, 2, 15000.00, '2025-10-01', '2025-10', 'Bank Transfer', 'Paid'),

-- Payments for current tenancy (Occu_ID 3)
(506, 3, 18000.00, '2025-09-30', '2025-10', 'UPI', 'Paid'),

-- Payments for historical tenancy (Occu_ID 4)
(507, 4, 15000.00, '2024-12-01', '2024-12', 'Bank Transfer', 'Paid'),
(508, 4, 15000.00, '2025-01-01', '2025-01', 'Bank Transfer', 'Paid'),
(509, 4, 15000.00, '2025-02-01', '2025-02', 'Bank Transfer', 'Paid'),

-- Payments for historical tenancy (Occu_ID 5)
(510, 5, 18000.00, '2024-10-01', '2024-10', 'Cash', 'Paid');