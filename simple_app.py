from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import bcrypt
import datetime
import os

app = Flask(__name__)
CORS(app)  # Simple CORS without complex configuration

# Database connection
def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='petnest_db',
        port=3306
    )

# ========== HEALTH CHECK ==========
@app.route('/api/health', methods=['GET'])
def health():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return jsonify({"status": "ok", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== SIMPLE LOGIN ==========
@app.route('/api/simple-login', methods=['POST'])
def simple_login():
    try:
        data = request.json
        identifier = data.get('identifier', '').lower()
        password = data.get('password', '')
        
        # Admin check
        if identifier in ['admin', 'admin@petlink.com'] and password == 'admin123':
            return jsonify({
                "success": True,
                "message": "Login successful",
                "user": {
                    "user_id": 1,
                    "username": "admin",
                    "email": "admin@petlink.com",
                    "role": "admin",
                    "full_name": "Admin User"
                },
                "token": "admin_token_123"
            })
        
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ========== CREATE USER (NO AUTH REQUIRED FOR NOW) ==========
@app.route('/api/create-user', methods=['POST'])
def create_user():
    try:
        data = request.json
        print("Received user data:", data)
        
        # Required fields
        required = ['full_name', 'email', 'phone', 'city', 'role']
        for field in required:
            if not data.get(field):
                return jsonify({"success": False, "message": f"{field} is required"}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Email already exists"}), 400
        
        # Generate username from full name
        username = data['full_name'].lower().replace(' ', '') + str(datetime.datetime.now().timestamp())[-4:]
        
        # Default password
        default_password = 'Temp123!'
        hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (username, email, password, role, full_name, phone, city, country, is_verified, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            username,
            data['email'],
            hashed_password,
            data['role'],
            data['full_name'],
            data['phone'],
            data['city'],
            'Pakistan',
            False,  # Not verified by default
            True    # Active by default
        ))
        
        user_id = cursor.lastrowid
        
        # If shelter, create shelter record
        if data['role'] == 'shelter':
            cursor.execute("""
                INSERT INTO shelters (user_id, organization_name, contact_person, is_approved)
                VALUES (%s, %s, %s, %s)
            """, (
                user_id,
                data.get('organization_name', data['full_name']),
                data['full_name'],
                False  # Not approved by default
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ User created: {username} ({data['email']})")
        
        return jsonify({
            "success": True,
            "message": "User created successfully",
            "user_id": user_id,
            "username": username,
            "temp_password": default_password
        })
        
    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

# ========== GET ALL USERS ==========
@app.route('/api/get-users', methods=['GET'])
def get_users():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT user_id, username, email, role, full_name, phone, city,
                   is_verified, is_active, DATE_FORMAT(created_at, '%Y-%m-%d') as created_at
            FROM users 
            ORDER BY created_at DESC
        """)
        
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "users": users
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ========== UPDATE USER ==========
@app.route('/api/update-user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    try:
        data = request.json
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Build update query
        update_fields = []
        update_values = []
        
        if 'full_name' in data:
            update_fields.append("full_name = %s")
            update_values.append(data['full_name'])
        
        if 'email' in data:
            update_fields.append("email = %s")
            update_values.append(data['email'])
        
        if 'phone' in data:
            update_fields.append("phone = %s")
            update_values.append(data['phone'])
        
        if 'city' in data:
            update_fields.append("city = %s")
            update_values.append(data['city'])
        
        if 'role' in data:
            update_fields.append("role = %s")
            update_values.append(data['role'])
        
        if 'is_verified' in data:
            update_fields.append("is_verified = %s")
            update_values.append(data['is_verified'])
        
        if 'is_active' in data:
            update_fields.append("is_active = %s")
            update_values.append(data['is_active'])
        
        if update_fields:
            update_values.append(user_id)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s"
            cursor.execute(query, update_values)
            conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "User updated"})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ========== DELETE USER ==========
@app.route('/api/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE users SET is_active = FALSE WHERE user_id = %s", (user_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "User deactivated"})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🐾 SIMPLE PETNEST SERVER")
    print("=" * 50)
    print("API Endpoints:")
    print("  POST /api/simple-login   - Login (admin/admin123)")
    print("  POST /api/create-user    - Create new user")
    print("  GET  /api/get-users      - Get all users")
    print("  POST /api/update-user/:id - Update user")
    print("  POST /api/delete-user/:id - Delete user")
    print("=" * 50)
    app.run(debug=True, port=5000)