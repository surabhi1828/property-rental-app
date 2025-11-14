-- REVIEW 3: TRIGGERS, PROCEDURES, AND FUNCTIONS

DELIMITER //

--                            TRIGGERS                           

-- ---
-- 1. TRIGGER: Update Property Status on Occupancy
-- Ensures a property status changes to 'Rented' the moment a new tenant moves in.
-- ---
CREATE TRIGGER trg_update_property_status
AFTER INSERT ON OCCUPANCY
FOR EACH ROW
BEGIN
    -- Only update status if the property is currently marked as 'Available'
    UPDATE PROPERTY
    SET status = 'Rented'
    WHERE property_id = NEW.property_id
    AND status = 'Available';
END;
//

-- ---
-- 2. TRIGGER: Update Property Status on Occupancy END
-- Ensures a property status changes to 'Available' the moment an occupancy record ends.
-- This is critical for showing the property is ready for the next tenant.
-- ---
CREATE TRIGGER trg_update_status_on_checkout
AFTER UPDATE ON OCCUPANCY
FOR EACH ROW
BEGIN
    -- Check if the end_date was just set and the old end_date was NULL
    IF OLD.end_date IS NULL AND NEW.end_date IS NOT NULL THEN
        UPDATE PROPERTY
        SET status = 'Available'
        WHERE property_id = NEW.property_id;
    END IF;
END;
//

-- ---
-- 3. TRIGGER: Prevent Duplicate Reviews
-- Prevents a single tenant from reviewing the SAME property more than once.
-- Uses a BEFORE INSERT to stop the transaction if a duplicate is found.
-- ---
CREATE TRIGGER trg_prevent_duplicate_review
BEFORE INSERT ON REVIEW
FOR EACH ROW
BEGIN
    DECLARE review_count INT;

    SELECT COUNT(*) INTO review_count
    FROM REVIEW
    WHERE tenant_id = NEW.tenant_id AND property_id = NEW.property_id;

    IF review_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: This tenant has already submitted a review for this property.';
    END IF;
END;
//


--                          STORED PROCEDURES                      

-- ---
-- 1. STORED PROCEDURE: Record Rent Payment
-- Allows the application to cleanly record a new payment in one call.
-- To insert a new payment record into the PAYMENTS table in a clean, encapsulated way.
-- ---
CREATE PROCEDURE sp_record_rent_payment(
    IN p_occupancy_id INT,
    IN p_amount DECIMAL(10, 2),
    IN p_payment_date DATE,
    IN p_month_year VARCHAR(7),
    IN p_method VARCHAR(50),
    IN p_status ENUM('Paid', 'Pending', 'Late')
)
BEGIN
    INSERT INTO PAYMENTS (occupancy_id, amount, payment_date, month_year, method, status)
    VALUES (p_occupancy_id, p_amount, p_payment_date, p_month_year, p_method, p_status);
END;
//

-- ---
-- 2. STORED PROCEDURE: Check Out Tenant
-- This handles the entire 'check out' process in one transaction.
-- It sets the end_date in OCCUPANCY (which triggers the status change via trg_update_status_on_checkout).
-- ---
CREATE PROCEDURE sp_checkout_tenant(
    IN p_occupancy_id INT,
    IN p_checkout_date DATE
)
BEGIN
    -- Update the end_date for the specific occupancy record
    UPDATE OCCUPANCY
    SET end_date = p_checkout_date
    WHERE occupancy_id = p_occupancy_id
    AND end_date IS NULL; -- Only update if they are currently checked in

    -- The trg_update_status_on_checkout trigger automatically sets the PROPERTY status to 'Available'
END;
//

-- ---
-- 3. STORED PROCEDURE: Get Owner's Properties and Total Rent
-- To generate a report showing all properties owned by a specific owner and the total rent collected for each property.
-- ---
CREATE PROCEDURE sp_get_owner_summary(
    IN p_owner_id INT
)
BEGIN
    SELECT
        P.property_id,
        P.address,
        P.monthly_rent,
        P.status,
        -- Calculate total rent collected (simple example)
        (
            SELECT SUM(T2.amount)
            FROM PAYMENTS T2
            JOIN OCCUPANCY O2 ON T2.occupancy_id = O2.occupancy_id
            WHERE O2.property_id = P.property_id
        ) AS total_rent_collected
    FROM PROPERTY P
    WHERE P.owner_id = p_owner_id;
END;
//

--                           FUNCTIONS                          
-- ---
-- 1. FUNCTION: Calculate Average Property Rating
-- Returns the average rating (out of 5) for a given property.
-- ---
CREATE FUNCTION fn_get_avg_rating(p_property_id INT)
RETURNS DECIMAL(3, 2)
READS SQL DATA
BEGIN
    DECLARE avg_rating DECIMAL(3, 2);

    SELECT AVG(rating) INTO avg_rating
    FROM REVIEW
    WHERE property_id = p_property_id;

    -- Return 0.00 if no reviews exist for the property
    RETURN IFNULL(avg_rating, 0.00);
END;
//

-- ---
-- 2. FUNCTION: Check If Property is Currently Occupied
-- Returns a boolean (0 or 1) indicating if a property has a current tenant.
-- ---
CREATE FUNCTION fn_is_property_occupied(p_property_id INT)
RETURNS TINYINT
READS SQL DATA
BEGIN
    DECLARE occupied_count INT;

    SELECT COUNT(*) INTO occupied_count
    FROM OCCUPANCY
    WHERE property_id = p_property_id
    AND end_date IS NULL;

    RETURN IF(occupied_count > 0, 1, 0);
END;
//

-- ---
-- 3. FUNCTION: Get Total Late Payments for a Tenant
-- Returns the count of payments marked 'Late' for a specific tenant across all properties.
-- ---
CREATE FUNCTION fn_get_tenant_late_payments(p_tenant_id INT)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE late_count INT;

    SELECT COUNT(P.payment_id) INTO late_count
    FROM PAYMENTS P
    JOIN OCCUPANCY O ON P.occupancy_id = O.occupancy_id
    WHERE O.tenant_id = p_tenant_id
    AND P.status = 'Late';

    RETURN IFNULL(late_count, 0);
END;
//

DELIMITER ;
