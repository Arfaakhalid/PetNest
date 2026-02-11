from flask import Flask, request, jsonify, session, make_response, send_from_directory
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv
import os
import mysql.connector
from mysql.connector import Error
import bcrypt
import jwt
import datetime
from functools import wraps
import re
import uuid

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'petnest_dev_secret_key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Configure CORS to allow credentials
CORS(app, 
     supports_credentials=True,
     origins=['http://127.0.0.1:5500', 'http://localhost:5500', 'http://127.0.0.1:5501', 'http://localhost:5501', 'http://127.0.0.1:5000', 'http://localhost:5000'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'])

# Initialize session
Session(app)

# ========== DATABASE CONNECTION ==========
def get_db_connection():
    """Get MySQL database connection"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='petnest_db',
            port=3306,
            autocommit=False
        )
        return connection
    except Error as e:
        print(f"❌ Database connection error: {e}")
        return None

# ========== UTILITY FUNCTIONS ==========
def hash_password(password):
    """Hash a password using bcrypt"""
    try:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"❌ Password hashing error: {e}")
        return None

def verify_password(password, hashed_password):
    """Verify a password against its hash"""
    try:
        if not password or not hashed_password:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"❌ Password verification error: {e}")
        return False

def generate_session_token(user_id):
    """Generate a JWT session token"""
    try:
        payload = {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(
            payload, 
            os.getenv('JWT_SECRET_KEY', 'petnest_jwt_secret_2025'), 
            algorithm='HS256'
        )
        return token
    except Exception as e:
        print(f"❌ JWT generation error: {e}")
        return None

def create_session_in_db(user_id, session_token, request):
    """Create a session record in database"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = None
    try:
        cursor = connection.cursor()
        expires_at = datetime.datetime.now() + datetime.timedelta(days=7)
        
        # Create user_sessions table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                user_id INT NOT NULL,
                session_data TEXT,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Delete old sessions for this user
        cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,))
        
        # Insert new session
        cursor.execute("""
            INSERT INTO user_sessions 
            (session_id, user_id, session_data, expires_at)
            VALUES (%s, %s, %s, %s)
        """, (
            session_token,
            user_id,
            str({'ip': request.remote_addr, 'agent': request.user_agent.string}),
            expires_at
        ))
        
        connection.commit()
        return True
    except Error as e:
        print(f"❌ Session creation error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        connection.close()

# ========== AUTH MIDDLEWARE ==========
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from cookies
        if 'session_token' in request.cookies:
            token = request.cookies.get('session_token')
        
        # Get token from headers
        if not token and request.headers.get('Authorization'):
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'success': False, 'message': 'Session token is missing'}), 401
        
        try:
            # Decode token
            payload = jwt.decode(
                token, 
                os.getenv('JWT_SECRET_KEY', 'petnest_jwt_secret_2025'), 
                algorithms=['HS256']
            )
            
            # Check session in database
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM user_sessions 
                    WHERE session_id = %s AND expires_at > NOW()
                """, (token,))
                session_data = cursor.fetchone()
                cursor.close()
                connection.close()
                
                if not session_data:
                    return jsonify({'success': False, 'message': 'Invalid or expired session'}), 401
            
            # Store user_id in request context
            request.user_id = payload['user_id']
            
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Session has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
        except Exception as e:
            print(f"❌ Token verification error: {e}")
            return jsonify({'success': False, 'message': 'Token error'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

# ========== HELPER FUNCTIONS ==========
def create_cors_response():
    """Create CORS preflight response"""
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", request.headers.get('Origin', '*'))
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization,X-Requested-With")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS,PATCH")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

def get_redirect_url(role):
    """Get redirect URL based on user role"""
    role_urls = {
        'admin': '/pages/admin/admin-dashboard.html',
        'reporter': '/pages/reporter/reporter-dashboard.html',
        'adopter': '/pages/adopter/adopter-dashboard.html',
        'seller': '/pages/seller/seller-dashboard.html',
        'shelter': '/pages/shelter/shelter-dashboard.html',
        'store': '/pages/store/store-dashboard.html'
    }
    return role_urls.get(role, '/index.html')

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'mkv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, upload_type='profiles'):
    """Save uploaded file and return its path"""
    try:
        if file and file.filename and allowed_file(file.filename):
            # Generate unique filename
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
            
            # Create directory if not exists
            upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], upload_type)
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, unique_filename)
            file.save(file_path)
            
            # Return relative path
            return f"/static/uploads/{upload_type}/{unique_filename}"
    except Exception as e:
        print(f"❌ File save error: {e}")
    return None

# ========== STATIC FILE SERVING ==========
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

# ========== PASSWORD RESET ROUTES ==========
@app.route('/api/auth/verify_identity', methods=['POST', 'OPTIONS'])
def verify_identity():
    """Verify user identity for password reset"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        
        if not username or not email or not phone:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Check if user exists with matching credentials
        cursor.execute("""
            SELECT user_id, username, email, phone, role 
            FROM users 
            WHERE username = %s AND email = %s AND phone = %s
            AND is_active = TRUE
        """, (username, email, phone))
        
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if not user:
            return jsonify({'success': False, 'message': 'Invalid credentials. Please check your details.'}), 401
        
        # Return user_id for next steps
        return jsonify({
            'success': True,
            'message': 'Identity verified successfully',
            'user_id': user['user_id'],
            'role': user['role']
        })
        
    except Error as e:
        print(f"❌ Database error in verify_identity: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500
    except Exception as e:
        print(f"❌ Identity verification error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/auth/direct_reset', methods=['POST', 'OPTIONS'])
def direct_reset_password():
    """Direct password reset with user_id (after identity verification)"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        user_id = data.get('user_id')
        password = data.get('password', '')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID is required'}), 400
        
        if not password or len(password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor()
        
        # Check if user exists and is active
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s AND is_active = TRUE", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'User not found or inactive'}), 404
        
        # Hash new password
        hashed_pw = hash_password(password)
        if not hashed_pw:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'Password processing error'}), 500
        
        # Update password
        cursor.execute("""
            UPDATE users 
            SET password = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE user_id = %s
        """, (hashed_pw, user_id))
        
        connection.commit()
        
        # Log the activity
        try:
            ip_address = request.remote_addr
            user_agent = request.user_agent.string
            
            cursor.execute("""
                INSERT INTO activity_logs (user_id, action, details, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, 'PASSWORD_RESET', 'User reset password via forgot password flow', ip_address, user_agent))
            connection.commit()
        except Exception as log_error:
            print(f"⚠️ Failed to log activity: {log_error}")
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Password has been reset successfully'
        })
        
    except Error as e:
        print(f"❌ Database error in direct_reset: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500
    except Exception as e:
        print(f"❌ Password reset error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/auth/check_username', methods=['POST', 'OPTIONS'])
def check_username():
    """Check if username exists (for form validation)"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'success': False, 'message': 'Username is required'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT user_id, email, phone, role 
            FROM users 
            WHERE username = %s AND is_active = TRUE
        """, (username,))
        
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if user:
            # Mask email for security
            email = user['email']
            masked_email = email[0] + '***' + email[email.find('@'):] if email else 'No email'
            
            # Mask phone for security
            phone = user['phone']
            masked_phone = '***' + phone[-4:] if phone and len(phone) > 4 else 'No phone'
            
            return jsonify({
                'success': True,
                'exists': True,
                'user_id': user['user_id'],
                'email': user['email'],
                'masked_email': masked_email,
                'phone': user['phone'],
                'masked_phone': masked_phone,
                'role': user['role'],
                'email_hint': f"Email ends with {email[email.find('@'):]}" if email else "No email on file",
                'phone_hint': f"Phone ends with {phone[-4:]}" if phone else "No phone on file"
            })
        else:
            return jsonify({
                'success': True,
                'exists': False,
                'message': 'Username not found'
            })
        
    except Exception as e:
        print(f"❌ Check username error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/auth/get_user_by_email', methods=['POST', 'OPTIONS'])
def get_user_by_email():
    """Get user info by email (for email verification step)"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT user_id, username, email, phone, role 
            FROM users 
            WHERE email = %s AND is_active = TRUE
        """, (email,))
        
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if user:
            # Mask phone for security
            phone = user['phone']
            masked_phone = '***' + phone[-4:] if phone and len(phone) > 4 else '***'
            
            return jsonify({
                'success': True,
                'exists': True,
                'user_id': user['user_id'],
                'username': user['username'],
                'phone_hint': f"Phone ends with {phone[-4:]}" if phone else "No phone on file",
                'masked_phone': masked_phone,
                'role': user['role']
            })
        else:
            return jsonify({
                'success': True,
                'exists': False,
                'message': 'Email not found'
            })
        
    except Exception as e:
        print(f"❌ Get user by email error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/auth/get_user_roles', methods=['POST', 'OPTIONS'])
def get_user_roles():
    """Get all roles for a user (if multiple roles supported)"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # In your current schema, each user has only one role
        # Return the single role from users table
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if user:
            return jsonify({
                'success': True,
                'roles': [user['role']]  # Single role as array
            })
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
    except Exception as e:
        print(f"❌ Get user roles error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

# ========== MAIN AUTH ROUTES ==========
@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    """Handle user registration"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Required fields
        required = ['username', 'email', 'password', 'role', 'full_name', 'phone', 'city']
        for field in required:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # Basic validation
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', data['email']):
            return jsonify({'success': False, 'message': 'Invalid email'}), 400
        
        if len(data['password']) < 8:
            return jsonify({'success': False, 'message': 'Password must be 8+ characters'}), 400
        
        # Connect to database
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Check duplicates
        cursor.execute("SELECT user_id FROM users WHERE username = %s OR email = %s", 
                      (data['username'], data['email']))
        if cursor.fetchone():
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'Username or email already exists'}), 409
        
        # Hash password
        hashed_pw = hash_password(data['password'])
        if not hashed_pw:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'Password processing error'}), 500
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (username, email, password, role, full_name, phone, city, address, cnic)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['username'],
            data['email'],
            hashed_pw,
            data['role'],
            data['full_name'],
            data['phone'],
            data['city'],
            data.get('address', ''),
            data.get('cnic')
        ))
        
        user_id = cursor.lastrowid
        
        # Handle shelter-specific data
        if data['role'] == 'shelter' and data.get('shelter_name'):
            cursor.execute("""
                INSERT INTO shelters (user_id, organization_name, license_number, contact_person)
                VALUES (%s, %s, %s, %s)
            """, (
                user_id,
                data['shelter_name'],
                data.get('license', ''),
                data['full_name']
            ))
        
        connection.commit()
        
        # Generate token and session
        token = generate_session_token(user_id)
        if token:
            create_session_in_db(user_id, token, request)
        
        # Get user data
        cursor.execute("""
            SELECT user_id, username, email, role, full_name, phone, city, 
                   profile_picture, badge, is_verified
            FROM users WHERE user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        # Create response
        response = jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': user,
            'token': token
        })
        
        # Set cookie
        if token:
            response.set_cookie(
                'session_token',
                token,
                expires=datetime.datetime.now() + datetime.timedelta(days=7),
                httponly=True,
                secure=False,
                samesite='Lax'
            )
        
        return response
        
    except mysql.connector.IntegrityError:
        return jsonify({'success': False, 'message': 'Duplicate entry'}), 409
    except Error as e:
        print(f"❌ Database error in register: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """Handle user login with email/username"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data'}), 400
        
        identifier = data.get('identifier', '').strip()
        password = data.get('password', '')
        
        if not identifier or not password:
            return jsonify({'success': False, 'message': 'Identifier and password required'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Find user by email or username
        cursor.execute("""
            SELECT * FROM users 
            WHERE (email = %s OR username = %s) AND is_active = TRUE
        """, (identifier, identifier))
        
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        # Verify password
        if not verify_password(password, user['password']):
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        # Generate token
        token = generate_session_token(user['user_id'])
        if token:
            create_session_in_db(user['user_id'], token, request)
        
        # Prepare user data
        user_data = {
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'full_name': user['full_name'],
            'phone': user['phone'],
            'city': user['city'],
            'profile_picture': user['profile_picture'],
            'badge': user['badge'],
            'is_verified': user['is_verified']
        }
        
        # Get shelter info if applicable
        if user['role'] == 'shelter':
            cursor.execute("SELECT * FROM shelters WHERE user_id = %s", (user['user_id'],))
            shelter = cursor.fetchone()
            if shelter:
                user_data['shelter_info'] = shelter
        
        cursor.close()
        connection.close()
        
        # Create response
        response = jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user_data,
            'redirect_url': get_redirect_url(user['role']),
            'token': token
        })
        
        # Set cookie
        if token:
            response.set_cookie(
                'session_token',
                token,
                expires=datetime.datetime.now() + datetime.timedelta(days=7),
                httponly=True,
                secure=False,
                samesite='Lax'
            )
        
        return response
        
    except Error as e:
        print(f"❌ Database error in login: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/auth/check', methods=['GET', 'OPTIONS'])
@token_required
def check_auth():
    """Check authentication status and get user data"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT user_id, username, email, role, full_name, phone, city,
                   profile_picture, badge, is_verified, is_active
            FROM users WHERE user_id = %s
        """, (request.user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Get shelter info if applicable
        if user['role'] == 'shelter':
            cursor.execute("SELECT * FROM shelters WHERE user_id = %s", (user['user_id'],))
            shelter = cursor.fetchone()
            if shelter:
                user['shelter_info'] = shelter
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'authenticated': True,
            'user': user,
            'redirect_url': get_redirect_url(user['role'])
        })
        
    except Exception as e:
        print(f"❌ Auth check error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/auth/logout', methods=['POST', 'OPTIONS'])
@token_required
def logout():
    """Logout user"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        token = request.cookies.get('session_token')
        
        # Delete session from database
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM user_sessions WHERE session_id = %s", (token,))
            connection.commit()
            cursor.close()
            connection.close()
        
        response = jsonify({'success': True, 'message': 'Logged out'})
        response.set_cookie('session_token', '', expires=0)
        
        return response
        
    except Exception as e:
        print(f"❌ Logout error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

# ========== CHANGE PASSWORD (AUTHENTICATED USER) ==========
@app.route('/api/auth/change_password', methods=['POST', 'OPTIONS'])
@token_required
def change_password():
    """Change password for authenticated user"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not current_password or not new_password or not confirm_password:
            return jsonify({'success': False, 'message': 'All password fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match'}), 400
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'message': 'New password must be at least 8 characters'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Get current password hash
        cursor.execute("SELECT password FROM users WHERE user_id = %s", (request.user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Verify current password
        if not verify_password(current_password, user['password']):
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401
        
        # Hash new password
        hashed_pw = hash_password(new_password)
        if not hashed_pw:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'Password processing error'}), 500
        
        # Update password
        cursor.execute("""
            UPDATE users 
            SET password = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE user_id = %s
        """, (hashed_pw, request.user_id))
        
        connection.commit()
        
        # Log the activity
        try:
            ip_address = request.remote_addr
            user_agent = request.user_agent.string
            
            cursor.execute("""
                INSERT INTO activity_logs (user_id, action, details, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            """, (request.user_id, 'PASSWORD_CHANGE', 'User changed password', ip_address, user_agent))
            connection.commit()
        except Exception as log_error:
            print(f"⚠️ Failed to log activity: {log_error}")
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Error as e:
        print(f"❌ Database error in change_password: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500
    except Exception as e:
        print(f"❌ Change password error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

# ========== PROFILE ROUTES ==========
@app.route('/api/profile/get', methods=['GET', 'OPTIONS'])
@token_required
def get_profile():
    """Get user profile data"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Get user data
        cursor.execute("""
            SELECT 
                u.user_id, u.username, u.email, u.role, u.full_name, u.phone, 
                u.city, u.address, u.cnic, u.profile_picture, u.badge, 
                u.is_verified, u.created_at,
                rs.total_reports, rs.verified_reports, rs.resolved_reports
            FROM users u
            LEFT JOIN reporter_stats rs ON u.user_id = rs.reporter_id
            WHERE u.user_id = %s AND u.is_active = TRUE
        """, (request.user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Get user's reports count
        cursor.execute("""
            SELECT 
                COUNT(*) as total_reports,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_reports,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_reports
            FROM animal_reports 
            WHERE reporter_id = %s
        """, (request.user_id,))
        
        report_stats = cursor.fetchone()
        
        # Format dates
        if user['created_at']:
            user['joined_date'] = user['created_at'].strftime('%B %Y')
        
        # Prepare response
        profile_data = {
            'personal_info': {
                'user_id': user['user_id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'email': user['email'],
                'phone': user['phone'],
                'cnic': user['cnic'],
                'role': user['role'],
                'badge': user['badge'] or 'Reporter',
                'city': user['city'],
                'address': user['address'],
                'profile_picture': user['profile_picture'] or 'https://randomuser.me/api/portraits/men/32.jpg',
                'is_verified': user['is_verified'],
                'joined_date': user.get('joined_date', '2023')
            },
            'stats': {
                'total_reports': report_stats['total_reports'] if report_stats else 0,
                'completed_reports': report_stats['completed_reports'] if report_stats else 0,
                'pending_reports': report_stats['pending_reports'] if report_stats else 0,
                'verified_reports': user['verified_reports'] or 0,
                'resolved_reports': user['resolved_reports'] or 0
            }
        }
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'profile': profile_data
        })
        
    except Error as e:
        print(f"❌ Database error in get_profile: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500
    except Exception as e:
        print(f"❌ Get profile error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/profile/update', methods=['POST', 'OPTIONS'])
@token_required
def update_profile():
    """Update user profile"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Extract data
        personal_info = data.get('personal_info', {})
        
        if not personal_info:
            return jsonify({'success': False, 'message': 'Personal information required'}), 400
        
        # Validate required fields
        required_fields = ['full_name', 'email', 'phone']
        for field in required_fields:
            if field not in personal_info or not personal_info[field]:
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # Validate email
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', personal_info['email']):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Check if email is already taken by another user
        cursor.execute("""
            SELECT user_id FROM users 
            WHERE email = %s AND user_id != %s AND is_active = TRUE
        """, (personal_info['email'], request.user_id))
        
        if cursor.fetchone():
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'Email already taken by another user'}), 409
        
        # Update user profile
        cursor.execute("""
            UPDATE users 
            SET full_name = %s, email = %s, phone = %s, 
                city = %s, address = %s, cnic = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
        """, (
            personal_info['full_name'],
            personal_info['email'],
            personal_info['phone'],
            personal_info.get('city', ''),
            personal_info.get('address', ''),
            personal_info.get('cnic'),
            request.user_id
        ))
        
        # Log the activity
        try:
            ip_address = request.remote_addr
            user_agent = request.user_agent.string
            
            cursor.execute("""
                INSERT INTO activity_logs (user_id, action, details, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            """, (request.user_id, 'PROFILE_UPDATE', 'User updated profile information', ip_address, user_agent))
        except Exception as log_error:
            print(f"⚠️ Failed to log activity: {log_error}")
        
        connection.commit()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })
        
    except Error as e:
        print(f"❌ Database error in update_profile: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500
    except Exception as e:
        print(f"❌ Update profile error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/profile/upload_picture', methods=['POST', 'OPTIONS'])
@token_required
def upload_profile_picture():
    """Upload profile picture"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        # Check if file is in request
        if 'profile_picture' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400
        
        file = request.files['profile_picture']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not '.' in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400
        
        # Validate file size (max 5MB)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        if file_size > 5 * 1024 * 1024:  # 5MB
            return jsonify({'success': False, 'message': 'File too large (max 5MB)'}), 400
        
        # Generate unique filename
        unique_filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Update database with file path
        connection = get_db_connection()
        if not connection:
            # Delete the uploaded file if database connection fails
            os.remove(file_path)
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor()
        
        # Get old profile picture to delete later
        cursor.execute("SELECT profile_picture FROM users WHERE user_id = %s", (request.user_id,))
        old_picture = cursor.fetchone()
        
        # Update profile picture
        profile_pic_url = f'/static/uploads/profiles/{unique_filename}'
        cursor.execute("""
            UPDATE users 
            SET profile_picture = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE user_id = %s
        """, (profile_pic_url, request.user_id))
        
        # Delete old profile picture if it exists and is not default
        if old_picture and old_picture[0] and 'randomuser.me' not in old_picture[0]:
            try:
                old_file_path = old_picture[0].replace('/static/', '').replace('/', os.sep)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            except Exception as e:
                print(f"⚠️ Failed to delete old profile picture: {e}")
        
        connection.commit()
        
        # Log the activity
        try:
            ip_address = request.remote_addr
            user_agent = request.user_agent.string
            
            cursor.execute("""
                INSERT INTO activity_logs (user_id, action, details, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            """, (request.user_id, 'PROFILE_PICTURE_UPDATE', 'User updated profile picture', ip_address, user_agent))
            connection.commit()
        except Exception as log_error:
            print(f"⚠️ Failed to log activity: {log_error}")
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Profile picture updated successfully',
            'profile_picture': profile_pic_url
        })
        
    except Error as e:
        print(f"❌ Database error in upload_profile_picture: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500
    except Exception as e:
        print(f"❌ Upload profile picture error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/profile/stats', methods=['GET', 'OPTIONS'])
@token_required
def get_profile_stats():
    """Get detailed profile statistics"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Get detailed report statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_reports,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_reports,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_reports,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_reports,
                SUM(CASE WHEN status = 'assigned' THEN 1 ELSE 0 END) as assigned_reports,
                SUM(CASE WHEN status = 'seen' THEN 1 ELSE 0 END) as seen_reports
            FROM animal_reports 
            WHERE reporter_id = %s
        """, (request.user_id,))
        
        report_stats = cursor.fetchone() or {}
        
        # Get recent reports
        cursor.execute("""
            SELECT 
                report_id, animal_type, animal_condition, location, status, 
                reported_at, assigned_to
            FROM animal_reports 
            WHERE reporter_id = %s
            ORDER BY reported_at DESC
            LIMIT 5
        """, (request.user_id,))
        
        recent_reports = cursor.fetchall()
        
        # Format dates for recent reports
        for report in recent_reports:
            if report['reported_at']:
                report['reported_date'] = report['reported_at'].strftime('%b %d, %Y')
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'stats': report_stats,
            'recent_reports': recent_reports
        })
        
    except Error as e:
        print(f"❌ Database error in get_profile_stats: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500
    except Exception as e:
        print(f"❌ Get profile stats error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

# ========== DASHBOARD ROUTES ==========
@app.route('/api/dashboard/stats', methods=['GET', 'OPTIONS'])
@token_required
def get_dashboard_stats():
    """Get dashboard statistics for reporter"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Get user info
        cursor.execute("""
            SELECT 
                u.user_id, u.username, u.email, u.role, u.full_name, u.phone, 
                u.city, u.profile_picture, u.badge, u.is_verified, u.created_at
            FROM users u
            WHERE u.user_id = %s AND u.is_active = TRUE
        """, (request.user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Get report statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_reports,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_reports,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_reports,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_reports,
                SUM(CASE WHEN urgency_level = 'high' THEN 1 ELSE 0 END) as urgent_reports
            FROM animal_reports 
            WHERE reporter_id = %s
        """, (request.user_id,))
        
        report_stats = cursor.fetchone()
        
        # Get recent reports
        cursor.execute("""
            SELECT 
                report_id, animal_type, animal_condition, location, status, 
                urgency_level, reported_at
            FROM animal_reports 
            WHERE reporter_id = %s
            ORDER BY reported_at DESC
            LIMIT 5
        """, (request.user_id,))
        
        recent_reports = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        # Format response
        dashboard_data = {
            'user': user,
            'stats': {
                'total_reports': report_stats['total_reports'] or 0,
                'completed_reports': report_stats['completed_reports'] or 0,
                'pending_reports': report_stats['pending_reports'] or 0,
                'in_progress_reports': report_stats['in_progress_reports'] or 0,
                'urgent_reports': report_stats['urgent_reports'] or 0,
                'completion_rate': round((report_stats['completed_reports'] or 0) / max(report_stats['total_reports'] or 1, 1) * 100, 1)
            },
            'recent_reports': recent_reports
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
        
    except Exception as e:
        print(f"❌ Get dashboard stats error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

# ========== REPORT ROUTES ==========
@app.route('/api/reports/create', methods=['POST', 'OPTIONS'])
@token_required
def create_report():
    """Create a new animal report"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        # Get form data
        reporter_id = request.user_id
        
        # Get text fields
        animal_type = request.form.get('animal_type', '').strip()
        breed = request.form.get('breed', '').strip()
        condition = request.form.get('condition', '').strip()
        description = request.form.get('description', '').strip()
        urgency = request.form.get('urgency', 'medium').strip()
        city = request.form.get('city', '').strip()
        area = request.form.get('area', '').strip()
        street = request.form.get('street', '').strip()
        exact_location = request.form.get('exact_location', '').strip()
        
        # Validate required fields
        required_fields = ['animal_type', 'condition', 'description', 'city', 'area']
        for field in required_fields:
            if not locals()[field]:
                return jsonify({'success': False, 'message': f'{field.replace("_", " ").title()} is required'}), 400
        
        # Validate condition
        if condition not in ['stray', 'sick', 'dead']:
            return jsonify({'success': False, 'message': 'Invalid condition'}), 400
        
        # Check for uploaded files
        photos = []
        for key in request.files:
            if key.startswith('photos_'):
                file = request.files[key]
                if file.filename:
                    # Validate file type
                    if file.content_type not in ['image/jpeg', 'image/png', 'image/jpg']:
                        return jsonify({'success': False, 'message': 'Only JPG/PNG images allowed'}), 400
                    
                    # Validate file size (5MB max)
                    file.seek(0, 2)  # Seek to end
                    file_size = file.tell()
                    file.seek(0)  # Reset file pointer
                    if file_size > 5 * 1024 * 1024:
                        return jsonify({'success': False, 'message': 'File too large (max 5MB)'}), 400
                    
                    # Generate unique filename
                    filename = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
                    
                    # Save file
                    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'reports')
                    os.makedirs(upload_dir, exist_ok=True)
                    file_path = os.path.join(upload_dir, filename)
                    file.save(file_path)
                    
                    photos.append(f'/static/uploads/reports/{filename}')
        
        if not photos:
            return jsonify({'success': False, 'message': 'At least one photo is required'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor()
        
        # Insert report
        cursor.execute("""
            INSERT INTO animal_reports 
            (reporter_id, animal_type, breed, animal_condition, description, 
             urgency_level, city, street, region, photos, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
        """, (
            reporter_id,
            animal_type,
            breed,
            condition,
            description,
            urgency,
            city,
            street,
            area,  # Using region field for area
            ','.join(photos)  # Store as comma-separated string
        ))
        
        report_id = cursor.lastrowid
        
        # Update reporter stats
        cursor.execute("""
            INSERT INTO reporter_stats (reporter_id, total_reports)
            VALUES (%s, 1)
            ON DUPLICATE KEY UPDATE 
            total_reports = total_reports + 1,
            last_updated = CURRENT_TIMESTAMP
        """, (reporter_id,))
        
        # Log activity
        try:
            ip_address = request.remote_addr
            user_agent = request.user_agent.string
            
            cursor.execute("""
                INSERT INTO activity_logs (user_id, action, details, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            """, (reporter_id, 'REPORT_CREATED', f'Created animal report #{report_id}', ip_address, user_agent))
        except Exception as log_error:
            print(f"⚠️ Failed to log activity: {log_error}")
        
        connection.commit()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Report submitted successfully',
            'report_id': report_id
        })
        
    except Error as e:
        print(f"❌ Database error in create_report: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500
    except Exception as e:
        print(f"❌ Create report error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/reports/recent', methods=['GET', 'OPTIONS'])
@token_required
def get_recent_reports():
    """Get recent reports for current user"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                report_id, animal_type, breed, animal_condition, 
                city, region as area, street, description,
                urgency_level, status, reported_at
            FROM animal_reports 
            WHERE reporter_id = %s
            ORDER BY reported_at DESC
            LIMIT 10
        """, (request.user_id,))
        
        reports = cursor.fetchall()
        
        # Format dates
        for report in reports:
            if report['reported_at']:
                report['reported_at'] = report['reported_at'].isoformat()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'reports': reports
        })
        
    except Error as e:
        print(f"❌ Database error in get_recent_reports: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500
    except Exception as e:
        print(f"❌ Get recent reports error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/reports/<int:report_id>', methods=['GET', 'OPTIONS'])
@token_required
def get_report_details(report_id):
    """Get detailed information for a specific report"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                r.*, u.full_name as reporter_name, u.phone as reporter_phone,
                s.organization_name as assigned_shelter
            FROM animal_reports r
            LEFT JOIN users u ON r.reporter_id = u.user_id
            LEFT JOIN shelters s ON r.assigned_to = s.shelter_id
            WHERE r.report_id = %s AND r.reporter_id = %s
        """, (report_id, request.user_id))
        
        report = cursor.fetchone()
        
        if not report:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'Report not found'}), 404
        
        # Convert photos string to array
        if report['photos']:
            report['photos'] = report['photos'].split(',')
        else:
            report['photos'] = []
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Error as e:
        print(f"❌ Database error in get_report_details: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500
    except Exception as e:
        print(f"❌ Get report details error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/reports/all', methods=['GET', 'OPTIONS'])
@token_required
def get_all_reports():
    """Get all reports for current user"""
    if request.method == 'OPTIONS':
        return create_cors_response()
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                report_id, animal_type, breed, animal_condition,
                city, region as area, status, reported_at
            FROM animal_reports 
            WHERE reporter_id = %s
            ORDER BY reported_at DESC
        """, (request.user_id,))
        
        reports = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'reports': reports,
            'count': len(reports)
        })
        
    except Error as e:
        print(f"❌ Database error in get_all_reports: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500
    except Exception as e:
        print(f"❌ Get all reports error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

# ========== TEST ENDPOINTS ==========
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'success': True,
        'message': 'API is working',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/test-login', methods=['GET'])
def test_login():
    return jsonify({
        'success': True,
        'message': 'Login system is ready',
        'endpoints': {
            'POST /api/auth/login': 'User login',
            'GET /api/auth/check': 'Check session',
            'POST /api/auth/logout': 'Logout'
        }
    })

@app.route('/api/db/test', methods=['GET'])
def test_db():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            cursor.close()
            connection.close()
            return jsonify({
                'success': True,
                'tables': tables,
                'message': f'Found {len(tables)} tables'
            })
        except Error as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': False, 'message': 'No connection'}), 500

# ========== HEALTH CHECK ==========
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        connection = get_db_connection()
        db_status = 'connected' if connection else 'disconnected'
        if connection:
            connection.close()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.datetime.now().isoformat(),
            'database': db_status,
            'endpoints': {
                'auth': {
                    'register': 'POST /api/auth/register',
                    'login': 'POST /api/auth/login',
                    'check': 'GET /api/auth/check',
                    'logout': 'POST /api/auth/logout',
                    'change_password': 'POST /api/auth/change_password',
                    'verify_identity': 'POST /api/auth/verify_identity',
                    'direct_reset': 'POST /api/auth/direct_reset',
                    'check_username': 'POST /api/auth/check_username'
                },
                'profile': {
                    'get': 'GET /api/profile/get',
                    'update': 'POST /api/profile/update',
                    'upload_picture': 'POST /api/profile/upload_picture',
                    'stats': 'GET /api/profile/stats'
                },
                'dashboard': {
                    'stats': 'GET /api/dashboard/stats'
                },
                'reports': {
                    'create': 'POST /api/reports/create',
                    'recent': 'GET /api/reports/recent',
                    'details': 'GET /api/reports/<id>',
                    'all': 'GET /api/reports/all'
                }
            }
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# ========== ERROR HANDLERS ==========
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'success': False, 'message': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    print(f"❌ Internal server error: {error}")
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

# ========== INITIALIZATION ==========
def initialize_directories():
    """Create necessary directories"""
    directories = ['profiles', 'reports', 'pets', 'products']
    
    for directory in directories:
        dir_path = os.path.join(app.config['UPLOAD_FOLDER'], directory)
        os.makedirs(dir_path, exist_ok=True)
        print(f"📁 Created directory: {dir_path}")

# ========== MAIN ==========
if __name__ == '__main__':
    # Create necessary directories
    initialize_directories()
    
    print("=" * 60)
    print("🐾 PETNEST NETWORK BACKEND - COMPLETE API")
    print("=" * 60)
    print("🚀 Server: http://127.0.0.1:5000")
    print("📦 Authentication Endpoints:")
    print("  POST /api/auth/register          - User registration")
    print("  POST /api/auth/login             - User login")
    print("  GET  /api/auth/check             - Check session")
    print("  POST /api/auth/logout            - User logout")
    print("  POST /api/auth/change_password   - Change password")
    print("\n📦 Profile Endpoints:")
    print("  GET  /api/profile/get            - Get profile")
    print("  POST /api/profile/update         - Update profile")
    print("  POST /api/profile/upload_picture - Upload profile picture")
    print("  GET  /api/profile/stats          - Get profile stats")
    print("\n📦 Dashboard Endpoints:")
    print("  GET  /api/dashboard/stats        - Get dashboard stats")
    print("\n📦 Report Endpoints:")
    print("  POST /api/reports/create         - Create report")
    print("  GET  /api/reports/recent         - Get recent reports")
    print("  GET  /api/reports/<id>           - Get report details")
    print("  GET  /api/reports/all            - Get all reports")
    print("\n📦 Password Reset Endpoints:")
    print("  POST /api/auth/verify_identity   - Verify identity")
    print("  POST /api/auth/direct_reset      - Reset password")
    print("  POST /api/auth/check_username    - Check username")
    print("  POST /api/auth/get_user_by_email - Get user by email")
    print("  POST /api/auth/get_user_roles    - Get user roles")
    print("\n✅ Ready to accept connections!")
    print("=" * 60)
    
    try:
        app.run(debug=True, host='127.0.0.1', port=5000)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("⚠️  Make sure port 5000 is not in use by another application.")
        print("⚠️  Try: netstat -ano | findstr :5000 (Windows) or lsof -i :5000 (Mac/Linux)")