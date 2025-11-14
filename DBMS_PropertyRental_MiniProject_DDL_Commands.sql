-- DDL Commands for Property Rental System
-- (No Sale, No Broker, No Formal Lease)

-- 1. OWNER Table
CREATE TABLE OWNER (
    owner_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100) UNIQUE,
    bank_details VARCHAR(255)
);

-- 2. TENANT Table
CREATE TABLE TENANT (
    tenant_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100) UNIQUE,
    id_proof VARCHAR(255)
);

-- 3. PROPERTY Table
CREATE TABLE PROPERTY (
    property_id INT PRIMARY KEY AUTO_INCREMENT,
    owner_id INT NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    description TEXT,
    sq_footage INT,
    monthly_rent DECIMAL(10, 2) NOT NULL,
    status ENUM('Available', 'Rented', 'Maintenance') NOT NULL,
    
    FOREIGN KEY (owner_id) REFERENCES OWNER(owner_id)
);

-- 4. OCCUPANCY Table (Resolves TENANT <-> PROPERTY N:M)
CREATE TABLE OCCUPANCY (
    occupancy_id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    property_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NULL, -- NULL until the tenant moves out

    FOREIGN KEY (tenant_id) REFERENCES TENANT(tenant_id),
    FOREIGN KEY (property_id) REFERENCES PROPERTY(property_id),
    
    -- Optional: Ensures a tenant cannot occupy the same property multiple times starting on the same date
    UNIQUE KEY (tenant_id, property_id, start_date)
);

-- 5. REVIEW Table (Resolves TENANT <-> PROPERTY N:M)
CREATE TABLE REVIEW (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    property_id INT NOT NULL,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    review_date DATE NOT NULL,

    FOREIGN KEY (tenant_id) REFERENCES TENANT(tenant_id),
    FOREIGN KEY (property_id) REFERENCES PROPERTY(property_id)
);

-- 6. PAYMENTS Table (Links to the specific OCCUPANCY period)
CREATE TABLE PAYMENTS (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    occupancy_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_date DATE NOT NULL,
    month_year VARCHAR(7) NOT NULL, -- Format example: '2025-10'
    method VARCHAR(50),
    status ENUM('Paid', 'Pending', 'Late') NOT NULL,

    FOREIGN KEY (occupancy_id) REFERENCES OCCUPANCY(occupancy_id)
);