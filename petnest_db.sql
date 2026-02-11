CREATE DATABASE IF NOT EXISTS petnest_db;
USE petnest_db;

-- Users table (Main authentication table)
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL, -- Changed from password_hash to simple password field
    role ENUM('admin', 'reporter', 'adopter', 'seller', 'shelter', 'store') NOT NULL,
    full_name VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(50),
    profile_picture VARCHAR(255),
    cnic VARCHAR(15) UNIQUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    badge VARCHAR(20) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Shelter/Rescue Organizations specific details
CREATE TABLE shelters (
    shelter_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE,
    organization_name VARCHAR(100) NOT NULL,
    license_number VARCHAR(50) UNIQUE,
    contact_person VARCHAR(100),
    total_rescued INT DEFAULT 0,
    total_recovered INT DEFAULT 0,
    total_settled INT DEFAULT 0,
    website VARCHAR(255),
    description TEXT,
    is_approved BOOLEAN DEFAULT FALSE,
    approved_by INT,
    approved_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Animal reports (by reporters)
CREATE TABLE animal_reports (
    report_id INT PRIMARY KEY AUTO_INCREMENT,
    reporter_id INT,
    animal_type VARCHAR(50) NOT NULL,
    breed VARCHAR(50),
    animal_condition ENUM('stray', 'sick', 'dead') NOT NULL,
    location VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    city VARCHAR(50),
    street VARCHAR(100),
    region VARCHAR(50),
    photos VARCHAR(500), -- Comma separated image paths
    description TEXT,
    urgency_level ENUM('low', 'medium', 'high') DEFAULT 'medium',
    status ENUM('pending', 'seen', 'assigned', 'in_progress', 'completed', 'closed') DEFAULT 'pending',
    assigned_to INT, -- shelter_id
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (reporter_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES shelters(shelter_id) ON DELETE SET NULL
);

-- Pets for adoption/sale
CREATE TABLE pets (
    pet_id INT PRIMARY KEY AUTO_INCREMENT,
    seller_id INT, -- Can be individual seller or shelter
    pet_name VARCHAR(50) NOT NULL,
    animal_type VARCHAR(50) NOT NULL,
    breed VARCHAR(50),
    age INT, -- in months
    gender ENUM('male', 'female', 'unknown'),
    color VARCHAR(50),
    weight DECIMAL(5,2),
    health_status ENUM('excellent', 'good', 'fair', 'poor') DEFAULT 'good',
    vaccination_status BOOLEAN DEFAULT FALSE,
    spayed_neutered BOOLEAN DEFAULT FALSE,
    description TEXT,
    price DECIMAL(10,2),
    status ENUM('available', 'reserved', 'adopted', 'sold') DEFAULT 'available',
    is_for_adoption BOOLEAN DEFAULT TRUE,
    is_for_sale BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Pet images
CREATE TABLE pet_images (
    image_id INT PRIMARY KEY AUTO_INCREMENT,
    pet_id INT,
    image_url VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id) ON DELETE CASCADE
);

-- Adoptions table
CREATE TABLE adoptions (
    adoption_id INT PRIMARY KEY AUTO_INCREMENT,
    pet_id INT,
    adopter_id INT,
    seller_id INT,
    adoption_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    adoption_fee DECIMAL(10,2),
    status ENUM('pending', 'approved', 'rejected', 'completed') DEFAULT 'pending',
    approved_by INT, -- admin who approved
    approved_at TIMESTAMP NULL,
    notes TEXT,
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id) ON DELETE CASCADE,
    FOREIGN KEY (adopter_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Favorites/Saved pets
CREATE TABLE favorites (
    favorite_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    pet_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_favorite (user_id, pet_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id) ON DELETE CASCADE
);

-- Chat conversations
CREATE TABLE conversations (
    conversation_id INT PRIMARY KEY AUTO_INCREMENT,
    participant1_id INT,
    participant2_id INT,
    pet_id INT, -- If conversation is about specific pet
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (participant1_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (participant2_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id) ON DELETE SET NULL
);

-- Chat messages
CREATE TABLE messages (
    message_id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT,
    sender_id INT,
    message_text TEXT,
    image_url VARCHAR(255),
    is_read BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Pet accessories/products
CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    store_id INT, -- user_id with role 'store'
    product_name VARCHAR(100) NOT NULL,
    category ENUM('food', 'toy', 'medicine', 'accessory', 'bedding', 'grooming') NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    animal_type VARCHAR(50), -- For which animal (optional)
    brand VARCHAR(50),
    images VARCHAR(500), -- Comma separated
    rating DECIMAL(3,2) DEFAULT 0,
    review_count INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Orders (for accessories)
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    store_id INT,
    total_amount DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    shipping_address TEXT,
    payment_method VARCHAR(50),
    payment_status ENUM('pending', 'paid', 'failed') DEFAULT 'pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_date TIMESTAMP NULL,
    FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (store_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Order items
CREATE TABLE order_items (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    product_id INT,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) AS (quantity * unit_price) STORED,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- Testimonials
CREATE TABLE testimonials (
    testimonial_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    content TEXT NOT NULL,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_by INT,
    approved_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Notifications
CREATE TABLE notifications (
    notification_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    title VARCHAR(100),
    message TEXT,
    type ENUM('info', 'success', 'warning', 'danger'),
    is_read BOOLEAN DEFAULT FALSE,
    related_id INT, -- ID of related entity (report_id, adoption_id, etc)
    related_type VARCHAR(50), -- 'report', 'adoption', 'message', etc
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- User activity logs (for admin monitoring)
CREATE TABLE activity_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Shelter applications (for new shelters waiting approval)
CREATE TABLE shelter_applications (
    application_id INT PRIMARY KEY AUTO_INCREMENT,
    organization_name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT NOT NULL,
    license_number VARCHAR(50),
    website VARCHAR(255),
    description TEXT,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INT,
    reviewed_at TIMESTAMP NULL,
    notes TEXT,
    FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Seller statistics (for PRO seller badge)
CREATE TABLE seller_stats (
    stat_id INT PRIMARY KEY AUTO_INCREMENT,
    seller_id INT UNIQUE,
    total_listings INT DEFAULT 0,
    total_sold INT DEFAULT 0,
    total_adopted INT DEFAULT 0,
    successful_deals INT DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Reporter statistics (for Star Reporter badge)
CREATE TABLE reporter_stats (
    stat_id INT PRIMARY KEY AUTO_INCREMENT,
    reporter_id INT UNIQUE,
    total_reports INT DEFAULT 0,
    verified_reports INT DEFAULT 0,
    resolved_reports INT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (reporter_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Add indexes for better query performance
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_pets_status ON pets(status);
CREATE INDEX idx_pets_seller ON pets(seller_id);
CREATE INDEX idx_reports_status ON animal_reports(status);
CREATE INDEX idx_reports_reporter ON animal_reports(reporter_id);
CREATE INDEX idx_adoptions_status ON adoptions(status);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_products_store ON products(store_id);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);

-- Insert Admin user (password: admin123 - plain text)
INSERT INTO users (username, email, password, role, full_name, phone, is_verified, is_active) 
VALUES ('admin', 'admin@petlink.com', 'admin123', 'admin', 'System Administrator', '1234567890', TRUE, TRUE);

-- Insert some sample users for each role (with plain text passwords)
INSERT INTO users (username, email, password, role, full_name, phone, city, is_verified) VALUES
('john_doe', 'john@email.com', 'password123', 'reporter', 'John Doe', '1234567891', 'New York', TRUE),
('jane_adopter', 'jane@email.com', 'password123', 'adopter', 'Jane Smith', '1234567892', 'Los Angeles', TRUE),
('pet_seller1', 'seller@email.com', 'password123', 'seller', 'Mike Johnson', '1234567893', 'Chicago', TRUE),
('happy_pets_store', 'store@email.com', 'password123', 'store', 'Happy Pets Store', '1234567894', 'Miami', TRUE);

-- Insert shelter user and shelter details
INSERT INTO users (username, email, password, role, full_name, phone, is_verified) 
VALUES ('paws_rescue', 'paws@email.com', 'password123', 'shelter', 'Paws Rescue Org', '1234567895', TRUE);

SET @last_user_id = LAST_INSERT_ID();

INSERT INTO shelters (user_id, organization_name, license_number, contact_person, is_approved) 
VALUES (@last_user_id, 'Paws Rescue Organization', 'LIC12345', 'Sarah Wilson', TRUE);

-- Insert sample pets (using actual user_ids - adjust if needed)
INSERT INTO pets (seller_id, pet_name, animal_type, breed, age, gender, description, price, status) VALUES
(3, 'Max', 'Dog', 'Golden Retriever', 24, 'male', 'Friendly and playful', 0.00, 'available'),
(3, 'Luna', 'Cat', 'Persian', 12, 'female', 'Calm and affectionate', 50.00, 'available'),
(6, 'Rocky', 'Dog', 'German Shepherd', 36, 'male', 'Rescued stray, needs loving home', 0.00, 'available'); -- Changed to user_id 6

-- Insert sample products
INSERT INTO products (store_id, product_name, category, description, price, stock_quantity) VALUES
(4, 'Premium Dog Food', 'food', 'High-quality dog food', 25.99, 100),
(4, 'Cat Toy Set', 'toy', 'Set of 5 cat toys', 15.99, 50),
(4, 'Flea Medicine', 'medicine', 'Monthly flea treatment', 12.99, 75);

-- Insert sample report (using user_id 2 for reporter)
INSERT INTO animal_reports (reporter_id, animal_type, animal_condition, location, city, description, status) VALUES
(2, 'Dog', 'stray', 'Central Park', 'New York', 'Friendly stray dog near fountain', 'pending');

-- Add pet images
INSERT INTO pet_images (pet_id, image_url, is_primary) VALUES
(1, 'uploads/pets/dog1.jpg', TRUE),
(2, 'uploads/pets/cat1.jpg', TRUE),
(3, 'uploads/pets/dog2.jpg', TRUE);

-- Add some testimonials
INSERT INTO testimonials (user_id, content, rating, status) VALUES
(2, 'Great platform! Found my perfect pet here.', 5, 'approved'),
(3, 'Easy to list pets for adoption.', 4, 'approved');

-- Trigger to update reporter stats when new report is added
DELIMITER $$
CREATE TRIGGER after_report_insert
AFTER INSERT ON animal_reports
FOR EACH ROW
BEGIN
    INSERT INTO reporter_stats (reporter_id, total_reports)
    VALUES (NEW.reporter_id, 1)
    ON DUPLICATE KEY UPDATE 
    total_reports = total_reports + 1,
    last_updated = CURRENT_TIMESTAMP;
    
    -- Update badge if conditions met
    UPDATE users u
    JOIN reporter_stats rs ON u.user_id = rs.reporter_id
    SET u.badge = 'Star Reporter'
    WHERE rs.total_reports >= 5 AND u.role = 'reporter' AND u.badge IS NULL;
END$$
DELIMITER ;

-- Trigger to update seller stats when adoption is completed
DELIMITER $$
CREATE TRIGGER after_adoption_complete
AFTER UPDATE ON adoptions
FOR EACH ROW
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        INSERT INTO seller_stats (seller_id, successful_deals)
        VALUES (NEW.seller_id, 1)
        ON DUPLICATE KEY UPDATE 
        successful_deals = successful_deals + 1,
        last_updated = CURRENT_TIMESTAMP;
        
        -- Update PRO seller badge
        UPDATE users u
        JOIN seller_stats ss ON u.user_id = ss.seller_id
        SET u.badge = 'PRO Seller'
        WHERE ss.successful_deals >= 5 AND u.role = 'seller' AND u.badge IS NULL;
    END IF;
END$$
DELIMITER ;

-- View for available pets
CREATE OR REPLACE VIEW available_pets AS
SELECT p.*, u.full_name as seller_name, u.city as seller_city
FROM pets p
JOIN users u ON p.seller_id = u.user_id
WHERE p.status = 'available';

-- View for active reports
CREATE OR REPLACE VIEW active_reports AS
SELECT ar.*, u.full_name as reporter_name, u.phone as reporter_phone,
       s.organization_name as assigned_shelter
FROM animal_reports ar
LEFT JOIN users u ON ar.reporter_id = u.user_id
LEFT JOIN shelters s ON ar.assigned_to = s.shelter_id
WHERE ar.status IN ('pending', 'assigned', 'in_progress');

-- View for user dashboard summary
CREATE OR REPLACE VIEW user_dashboard_summary AS
SELECT 
    u.user_id,
    u.username,
    u.role,
    u.full_name,
    u.badge,
    CASE 
        WHEN u.role = 'reporter' THEN COALESCE(rs.total_reports, 0)
        WHEN u.role = 'seller' THEN COALESCE(ss.successful_deals, 0)
        ELSE 0
    END as activity_count
FROM users u
LEFT JOIN reporter_stats rs ON u.user_id = rs.reporter_id
LEFT JOIN seller_stats ss ON u.user_id = ss.seller_id
WHERE u.is_active = TRUE;

-- Procedure to get user's conversations
DELIMITER $$
CREATE PROCEDURE GetUserConversations(IN userId INT)
BEGIN
    SELECT 
        c.conversation_id,
        CASE 
            WHEN c.participant1_id = userId THEN c.participant2_id
            ELSE c.participant1_id
        END as other_user_id,
        u.full_name as other_user_name,
        u.profile_picture,
        MAX(m.message_text) as last_message,
        MAX(m.sent_at) as last_message_time,
        COUNT(CASE WHEN m.is_read = FALSE AND m.sender_id != userId THEN 1 END) as unread_count
    FROM conversations c
    JOIN users u ON (u.user_id = CASE 
        WHEN c.participant1_id = userId THEN c.participant2_id 
        ELSE c.participant1_id 
    END)
    LEFT JOIN messages m ON m.conversation_id = c.conversation_id
    WHERE c.participant1_id = userId OR c.participant2_id = userId
    GROUP BY c.conversation_id, u.user_id, u.full_name, u.profile_picture
    ORDER BY last_message_time DESC;
END$$
DELIMITER ;

-- Procedure to search pets with filters
DELIMITER $$
CREATE PROCEDURE SearchPets(
    IN animalType VARCHAR(50),
    IN breedName VARCHAR(50),
    IN cityName VARCHAR(50),
    IN minPrice DECIMAL(10,2),
    IN maxPrice DECIMAL(10,2)
)
BEGIN
    SELECT 
        p.*,
        u.full_name as seller_name,
        u.city as seller_city,
        pi.image_url as primary_image
    FROM pets p
    JOIN users u ON p.seller_id = u.user_id
    LEFT JOIN pet_images pi ON p.pet_id = pi.pet_id AND pi.is_primary = TRUE
    WHERE p.status = 'available'
        AND (animalType IS NULL OR p.animal_type = animalType)
        AND (breedName IS NULL OR p.breed LIKE CONCAT('%', breedName, '%'))
        AND (cityName IS NULL OR u.city LIKE CONCAT('%', cityName, '%'))
        AND (minPrice IS NULL OR p.price >= minPrice)
        AND (maxPrice IS NULL OR p.price <= maxPrice);
END$$
DELIMITER ;





-- Add this to your existing SQL file
-- Admin specific tables

-- Admin activity logs table
CREATE TABLE admin_activity_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT,
    action_type VARCHAR(50) NOT NULL, -- 'login', 'user_edit', 'report_processed', etc.
    action_details TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Admin notifications table
CREATE TABLE admin_notifications (
    notification_id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT DEFAULT NULL, -- NULL means for all admins
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    type ENUM('info', 'warning', 'critical', 'success') DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    related_entity_type VARCHAR(50), -- 'user', 'report', 'shelter', etc.
    related_entity_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- System settings table
CREATE TABLE system_settings (
    setting_id INT PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type ENUM('string', 'integer', 'boolean', 'json') DEFAULT 'string',
    description TEXT,
    is_editable BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Statistics cache table (for performance)
CREATE TABLE statistics_cache (
    cache_id INT PRIMARY KEY AUTO_INCREMENT,
    stat_key VARCHAR(100) UNIQUE NOT NULL,
    stat_value INT NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert initial system settings
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
('site_name', 'PetNest Pakistan', 'Website name'),
('maintenance_mode', 'false', 'Enable/disable maintenance mode'),
('max_login_attempts', '5', 'Maximum failed login attempts'),
('session_timeout', '3600', 'Session timeout in seconds'),
('email_notifications', 'true', 'Enable email notifications'),
('auto_approve_shelters', 'false', 'Auto approve new shelters'),
('report_urgency_threshold', '24', 'Report urgency threshold in hours'),
('default_user_city', 'Islamabad', 'Default city for users'),
('admin_theme', 'light', 'Admin panel theme');

-- Create indexes for better performance
CREATE INDEX idx_admin_activity_admin ON admin_activity_logs(admin_id, created_at);
CREATE INDEX idx_admin_notifications ON admin_notifications(admin_id, is_read, created_at);
CREATE INDEX idx_users_created ON users(created_at);
CREATE INDEX idx_reports_created ON animal_reports(created_at);
CREATE INDEX idx_shelters_approved ON shelters(is_approved);
CREATE INDEX idx_pets_created ON pets(created_at);

-- Add country column to users table if not exists
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS country VARCHAR(50) DEFAULT 'Pakistan',
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS login_count INT DEFAULT 0;

-- Update existing users with Pakistan as country
UPDATE users SET country = 'Pakistan' WHERE country IS NULL;

-- Insert default admin notification
INSERT INTO admin_notifications (title, message, type) VALUES
('System Setup Complete', 'PetNest Pakistan admin system is now ready. Welcome!', 'success');

-- Create view for admin dashboard statistics
CREATE OR REPLACE VIEW admin_dashboard_stats AS
SELECT 
    (SELECT COUNT(*) FROM users WHERE is_active = TRUE AND country = 'Pakistan') as total_users,
    (SELECT COUNT(*) FROM animal_reports WHERE status = 'pending') as pending_reports,
    (SELECT COUNT(*) FROM shelters WHERE is_approved = TRUE) as rescue_organizations,
    (SELECT COUNT(DISTINCT report_id) FROM animal_reports WHERE status = 'completed') as animals_rescued,
    (SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = TRUE) as total_admins,
    (SELECT COUNT(*) FROM users WHERE DATE(created_at) = CURDATE()) as new_users_today,
    (SELECT COUNT(*) FROM animal_reports WHERE DATE(reported_at) = CURDATE()) as new_reports_today,
    (SELECT COUNT(*) FROM pets WHERE status = 'available') as available_pets;

-- Create view for recent admin activity
CREATE OR REPLACE VIEW recent_admin_activity AS
SELECT 
    aal.log_id,
    aal.admin_id,
    u.username as admin_name,
    u.full_name as admin_full_name,
    aal.action_type,
    aal.action_details,
    aal.created_at,
    TIMESTAMPDIFF(MINUTE, aal.created_at, NOW()) as minutes_ago
FROM admin_activity_logs aal
LEFT JOIN users u ON aal.admin_id = u.user_id
ORDER BY aal.created_at DESC
LIMIT 50;






-- Add these columns to your users table if they don't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS country VARCHAR(50) DEFAULT 'Pakistan',
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS login_count INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS suspension_reason TEXT,
ADD COLUMN IF NOT EXISTS suspended_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS suspended_by INT,
ADD COLUMN IF NOT EXISTS password_reset_required BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD FOREIGN KEY (suspended_by) REFERENCES users(user_id) ON DELETE SET NULL;

-- Add index for better performance on common queries
CREATE INDEX IF NOT EXISTS idx_users_role_status ON users(role, is_active, is_verified);
CREATE INDEX IF NOT EXISTS idx_users_created_city ON users(created_at, city);
CREATE INDEX IF NOT EXISTS idx_users_email_username ON users(email, username);