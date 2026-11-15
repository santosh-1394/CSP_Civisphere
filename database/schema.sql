
CREATE DATABASE IF NOT EXISTS civisphere_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE civisphere_db;

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    user_role VARCHAR(20) DEFAULT 'citizen',
    is_active BOOLEAN DEFAULT TRUE,
    preferred_language VARCHAR(30) DEFAULT 'English',
    theme VARCHAR(20) DEFAULT 'light',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. LOCATIONS TABLE
CREATE TABLE IF NOT EXISTS locations (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    location_name VARCHAR(150) NOT NULL,
    address TEXT,
    district VARCHAR(100),
    phone VARCHAR(20),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. SERVICES TABLE
CREATE TABLE IF NOT EXISTS services (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(150) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    department VARCHAR(150),
    contact_number VARCHAR(20),
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. COMPLAINTS TABLE
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
    tracking_id VARCHAR(50) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100),
    location VARCHAR(255),
    status VARCHAR(30) DEFAULT 'Pending',
    admin_remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 5. COMPLAINT HISTORY TABLE
CREATE TABLE IF NOT EXISTS complaint_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    previous_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    remarks TEXT,
    changed_by INT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id),
    FOREIGN KEY (changed_by) REFERENCES users(user_id)
);

-- 6. COMPLAINT ATTACHMENTS TABLE
CREATE TABLE IF NOT EXISTS complaint_attachments (
    attachment_id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(100),
    file_size BIGINT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
);

-- 7. BLOOD DONORS TABLE
CREATE TABLE IF NOT EXISTS blood_donors (
    donor_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    donor_name VARCHAR(150) NOT NULL,
    blood_group VARCHAR(5) NOT NULL,
    phone VARCHAR(20),
    location VARCHAR(255),
    available BOOLEAN DEFAULT TRUE,
    consent_to_contact BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 8. CONTACTS TABLE
CREATE TABLE IF NOT EXISTS contacts (
    contact_id INT AUTO_INCREMENT PRIMARY KEY,
    contact_name VARCHAR(150) NOT NULL,
    category VARCHAR(150),
    phone VARCHAR(20),
    email VARCHAR(150),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. NOTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    complaint_id INT,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
);

-- 10. FEEDBACK TABLE
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    subject VARCHAR(200),
    message TEXT,
    rating INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 11. CHATBOT FAQ TABLE
CREATE TABLE IF NOT EXISTS chatbot_faq (
    faq_id INT AUTO_INCREMENT PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    keywords TEXT,
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. CHATBOT LOGS TABLE
CREATE TABLE IF NOT EXISTS chatbot_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    question TEXT NOT NULL,
    answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 13. EMERGENCY SERVICES TABLE
CREATE TABLE IF NOT EXISTS emergency_services (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    service_name VARCHAR(200) NOT NULL,
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100),
    city VARCHAR(100),
    address TEXT NOT NULL,
    phone VARCHAR(20),
    alternate_phone VARCHAR(20),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    description TEXT,
    operating_hours VARCHAR(100),
    source VARCHAR(255),
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DEFAULT CITIZEN SERVICES
INSERT INTO services (service_name, category, description)
SELECT 'Water Supply Services', 'Utilities', 'Water supply related services'
WHERE NOT EXISTS (
    SELECT 1 FROM services WHERE service_name = 'Water Supply Services'
);

INSERT INTO services (service_name, category, description)
SELECT 'Electricity', 'Utilities', 'Electricity related services'
WHERE NOT EXISTS (
    SELECT 1 FROM services WHERE service_name = 'Electricity'
);

INSERT INTO services (service_name, category, description)
SELECT 'Sanitation', 'Public Services', 'Sanitation and cleanliness services'
WHERE NOT EXISTS (
    SELECT 1 FROM services WHERE service_name = 'Sanitation'
);

INSERT INTO services (service_name, category, description)
SELECT 'Road Maintenance', 'Public Services', 'Road repair and maintenance services'
WHERE NOT EXISTS (
    SELECT 1 FROM services WHERE service_name = 'Road Maintenance'
);

INSERT INTO services (service_name, category, description)
SELECT 'Street Light', 'Public Services', 'Street light maintenance services'
WHERE NOT EXISTS (
    SELECT 1 FROM services WHERE service_name = 'Street Light'
);

INSERT INTO services (service_name, category, description)
SELECT 'Birth and Death Registration', 'Government Services', 'Birth and death registration services'
WHERE NOT EXISTS (
    SELECT 1 FROM services WHERE service_name = 'Birth and Death Registration'
);
