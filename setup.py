#!/usr/bin/env python3
"""
Setup script for PetNest Network Flask Backend
Run this file first to install dependencies and setup database
"""

import os
import sys
import subprocess
import mysql.connector
from mysql.connector import Error
import getpass

def print_header():
    print("\n" + "="*60)
    print("PETNEST NETWORK - FLASK BACKEND SETUP")
    print("="*60)

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    requirements = [
        'Flask>=2.3.3',
        'Flask-CORS>=4.0.0',
        'Flask-Session>=0.5.0',
        'mysql-connector-python>=8.1.0',
        'python-dotenv>=1.0.0',
        'werkzeug>=2.3.7',
        'bcrypt>=4.0.1',
        'PyJWT>=2.8.0'
    ]
    
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Installed: {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install: {package}")
    
    print("\n✅ All dependencies installed!")

def create_database():
    """Create database and tables using your exact schema"""
    print("\n🗄️  Setting up MySQL database with your exact schema...")
    
    try:
        # Get MySQL credentials
        print("\nEnter MySQL credentials (XAMPP default is root with no password):")
        host = input("Host [localhost]: ") or "localhost"
        user = input("Username [root]: ") or "root"
        password = getpass.getpass("Password (press Enter if none): ") or ""
        
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Drop and create database
            cursor.execute("DROP DATABASE IF EXISTS petnest_db")
            cursor.execute("CREATE DATABASE petnest_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✓ Database 'petnest_db' created")
            
            # Use database
            cursor.execute("USE petnest_db")
            
            # Read and execute your exact SQL schema
            sql_file_path = os.path.join(os.path.dirname(__file__), 'database', 'petnest_db.sql')
            
            if os.path.exists(sql_file_path):
                print("✓ Found your SQL file, executing...")
                with open(sql_file_path, 'r', encoding='utf-8') as file:
                    sql_script = file.read()
                
                # Split the script by semicolons
                sql_commands = sql_script.split(';')
                
                for command in sql_commands:
                    command = command.strip()
                    if command:
                        try:
                            cursor.execute(command)
                        except Error as e:
                            print(f"  ⚠ Skipping: {e}")
                
                print("✓ All tables created successfully!")
            else:
                print("⚠ SQL file not found, creating minimal schema...")
                # Create minimal schema if file doesn't exist
                create_minimal_schema(cursor)
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print("\n✅ Database setup completed successfully!")
            
            # Save database credentials to .env file
            create_env_file(host, user, password)
            
    except Error as e:
        print(f"\n❌ Database setup failed: {e}")
        print("\nPlease make sure:")
        print("1. XAMPP is running with MySQL")
        print("2. MySQL service is started")
        print("3. You have correct credentials")
        return False
    
    return True

def create_minimal_schema(cursor):
    """Create minimal schema if SQL file is missing"""
    # Your exact users table
    users_table = """
    CREATE TABLE users (
        user_id INT PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
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
    )
    """
    cursor.execute(users_table)
    print("✓ Table 'users' created")
    
    # Your exact shelters table
    shelters_table = """
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
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    """
    cursor.execute(shelters_table)
    print("✓ Table 'shelters' created")
    
    # Create user_sessions table for Flask sessions
    sessions_table = """
    CREATE TABLE IF NOT EXISTS user_sessions (
        session_id VARCHAR(255) PRIMARY KEY,
        user_id INT NOT NULL,
        session_data TEXT,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id),
        INDEX idx_expires (expires_at)
    )
    """
    cursor.execute(sessions_table)
    print("✓ Table 'user_sessions' created")

def create_env_file(host, user, password):
    """Create .env file with database configuration"""
    env_content = f"""# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=petnest_dev_secret_key_2025_change_this_in_production

# Database Configuration
DB_HOST={host}
DB_USER={user}
DB_PASSWORD={password}
DB_NAME=petnest_db

# Session Configuration
SESSION_TYPE=filesystem
SESSION_PERMANENT=False
SESSION_USE_SIGNER=True

# Security
BCRYPT_LOG_ROUNDS=12
JWT_SECRET_KEY=petnest_jwt_secret_2025_change_this

# File Uploads
MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max upload
UPLOAD_FOLDER=static/uploads
ALLOWED_EXTENSIONS=*.jpg,*.jpeg,*.png,*.gif
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    print("✓ .env file created with database configuration")

def create_app_structure():
    """Create the Flask application structure"""
    print("\n📁 Creating application structure...")
    
    folders = [
        'models',
        'routes',
        'utils',
        'static/uploads/profiles',
        'static/uploads/pets',
        'static/uploads/products',
        'static/temp',
        'middleware',
        'database'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"✓ Created folder: {folder}")
    
    # Save your SQL to database folder
    sql_content = """-- Your exact SQL schema here"""
    
    with open('database/petnest_db.sql', 'w') as f:
        f.write(sql_content)
    
    print("✓ Saved SQL schema file")
    
    print("\n✅ Application structure created!")

def main():
    print_header()
    
    # Check if Python is available
    print(f"Python executable: {sys.executable}")
    
    # Install dependencies
    install_dependencies()
    
    # Create app structure
    create_app_structure()
    
    # Setup database
    if create_database():
        print("\n" + "="*60)
        print("SETUP COMPLETED SUCCESSFULLY! 🎉")
        print("="*60)
        print("\nNext steps:")
        print("1. Start MySQL in XAMPP Control Panel")
        print("2. Run: python app.py")
        print("3. Open http://127.0.0.1:5000")
        print("4. Your signup form should connect to: http://127.0.0.1:5000/api/auth/register")
        print("\nTest credentials:")
        print("- Username: admin")
        print("- Password: admin123")
        print("\nTo test:")
        print("- Open your signup.html page")
        print("- Fill the form and submit")
        print("- Check phpMyAdmin to see the user record")
    else:
        print("\n❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()