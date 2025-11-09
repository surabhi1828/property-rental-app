from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import Database
from datetime import datetime
import os
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback_secret_key')

db = Database()

# Initialize database connection when app starts
with app.app_context():
    db.connect()


# ==================== AUTHENTICATION ROUTES ====================

# ==================== PUBLIC HOME & AUTH ROUTES ====================

@app.route('/', methods=['GET', 'POST'])
def home():
    """NEW Public-facing homepage with property search."""
    
    # Base query joins PROPERTY and OWNER tables
    query = """
        SELECT 
            p.property_id, p.address, p.city, p.description, p.sq_footage, 
            p.monthly_rent, p.status,
            o.name as owner_name, 
            o.email as owner_email, 
            o.phone as owner_phone
        FROM PROPERTY p
        JOIN OWNER o ON p.owner_id = o.owner_id
    """
    
    params = []
    conditions = []

    if request.method == 'POST':
        # Handle search logic from form
        keyword = request.form.get('keyword', '')
        city = request.form.get('city', '')
        
        if keyword:
            # Search in description, address
            conditions.append("(p.description LIKE %s OR p.address LIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
            
        if city:
            conditions.append("p.city LIKE %s")
            params.append(f"%{city}%")
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
    else:
        # Default GET request: Show only AVAILABLE properties
        conditions.append("p.status = 'Available'")
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY p.monthly_rent ASC"
    
    # Use your db.execute_query method
    result = db.execute_query(query, tuple(params))
    
    properties = result['data'] if result['success'] else []

    return render_template('home.html', properties=properties)


@app.route('/login')
def index():
    """MOVED Role selection page (was at '/')"""
    session.clear()
    return render_template('index.html')

# @app.route('/login/<role>')
@app.route('/login-form/<role>')
def login_page(role):
    """Login page for different roles"""
    if role not in ['admin', 'owner', 'tenant']:
        return redirect(url_for('index'))
    return render_template('login.html', role=role)

@app.route('/api/login', methods=['POST'])
def login():
    """Handle login for all roles"""
    data = request.json
    role = data.get('role')
    
    if role == 'admin':
        # Hardcoded admin credentials
        if data.get('username') == 'admin' and data.get('password') == 'admin':
            session['role'] = 'admin'
            session['user_id'] = 0
            session['user_name'] = 'Administrator'
            return jsonify({'success': True, 'redirect': '/admin'})
        else:
            return jsonify({'success': False, 'error': 'Invalid admin credentials'})
    
    elif role in ['owner', 'tenant']:
        name = data.get('name')
        email = data.get('email')
        
        # Query appropriate table
        table = 'OWNER' if role == 'owner' else 'TENANT'
        id_field = 'owner_id' if role == 'owner' else 'tenant_id'
        
        query = f"SELECT {id_field}, name, email FROM {table} WHERE name = %s AND email = %s"
        result = db.execute_query(query, (name, email))
        
        if result['success'] and len(result['data']) > 0:
            user = result['data'][0]
            session['role'] = role
            session['user_id'] = user[id_field]
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            return jsonify({'success': True, 'redirect': f'/{role}'})
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'})
    
    return jsonify({'success': False, 'error': 'Invalid role'})

@app.route('/signup')
def signup_page():
    """Signup page"""
    return render_template('signup.html')

@app.route('/api/signup', methods=['POST'])
def signup():
    """Handle signup for owner/tenant"""
    data = request.json
    role = data.get('role')
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    
    if role == 'owner':
        bank_details = data.get('bank_details', '')
        query = "INSERT INTO OWNER (name, email, phone, bank_details) VALUES (%s, %s, %s, %s)"
        result = db.execute_query(query, (name, email, phone, bank_details), fetch=False)
    elif role == 'tenant':
        id_proof = data.get('id_proof', '')
        query = "INSERT INTO TENANT (name, email, phone, id_proof) VALUES (%s, %s, %s, %s)"
        result = db.execute_query(query, (name, email, phone, id_proof), fetch=False)
    else:
        return jsonify({'success': False, 'error': 'Invalid role'})
    
    if result['success']:
        return jsonify({'success': True, 'message': 'Account created successfully'})
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Signup failed')})

@app.route('/logout')
def logout():
    """Logout and return to role selection"""
    session.clear()
    return redirect(url_for('index'))

# ==================== ADMIN ROUTES ====================

# ==================== ADMIN ROUTES (Safer Version) ====================

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template('admin_dashboard.html')


# --- NEW ADMIN API ROUTES ---

@app.route('/api/admin/stats')
def admin_stats():
    """Get dashboard card statistics."""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    try:
        query_users = "SELECT COUNT(*) AS count FROM (SELECT owner_id FROM OWNER UNION ALL SELECT tenant_id FROM TENANT) AS users"
        users_result = db.execute_query(query_users, ())
        
        query_props = "SELECT COUNT(*) AS count FROM PROPERTY"
        props_result = db.execute_query(query_props, ())
        
        query_reviews = "SELECT COUNT(*) AS count FROM REVIEW"
        reviews_result = db.execute_query(query_reviews, ())

        stats = {
            'total_users': users_result['data'][0]['count'] if users_result['success'] else 0,
            'total_properties': props_result['data'][0]['count'] if props_result['success'] else 0,
            'total_reviews': (reviews_result['data'][0]['count'] or 0) if (reviews_result['success'] and reviews_result['data']) else 0
        }
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        print(f"!!! ERROR in /api/admin/stats: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/all_users')
def admin_all_users():
    """Get all owners and tenants."""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    try:
        query = """
            (SELECT owner_id AS id, name, email, phone, 'Owner' AS role FROM OWNER)
            UNION ALL
            (SELECT tenant_id AS id, name, email, phone, 'Tenant' AS role FROM TENANT)
            ORDER BY name
        """
        result = db.execute_query(query, ())
        return jsonify(result)
    except Exception as e:
        print(f"!!! ERROR in /api/admin/all_users: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/all_apartments')
def admin_all_apartments():
    """Get all properties with details."""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    try:
        query = """
        SELECT 
            p.property_id, p.address, p.city, p.description, p.sq_footage, 
            p.monthly_rent, p.status,
            o.name AS owner_name, o.email AS owner_email, o.phone AS owner_phone,
            t.name AS tenant_name
        FROM PROPERTY p
        JOIN OWNER o ON p.owner_id = o.owner_id
        LEFT JOIN OCCUPANCY occ ON p.property_id = occ.property_id AND occ.end_date IS NULL
        LEFT JOIN TENANT t ON occ.tenant_id = t.tenant_id
        ORDER BY p.property_id
        """
        result = db.execute_query(query, ())
        return jsonify(result)
    except Exception as e:
        print(f"!!! ERROR in /api/admin/all_apartments: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/all_complaints')
def admin_all_complaints():
    """Get all reviews (complaints)."""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    try:
        query = """
        SELECT 
            r.review_id, 
            r.rating, 
            r.comment, 
            r.review_date,
            t.name AS tenant_name,
            p.address AS address
        FROM REVIEW r
        JOIN TENANT t ON r.tenant_id = t.tenant_id
        JOIN PROPERTY p ON r.property_id = p.property_id
        ORDER BY r.review_date DESC
        """
        result = db.execute_query(query, ())
        return jsonify(result)
    except Exception as e:
        print(f"!!! ERROR in /api/admin/all_complaints: {e}")
        return jsonify({'success': False, 'error': str(e)})
# ==================== OWNER ROUTES ====================

@app.route('/owner')
def owner_dashboard():
    """Owner dashboard"""
    if session.get('role') != 'owner':
        return redirect(url_for('index'))
    return render_template('owner_dashboard.html')

@app.route('/api/owner/properties')
def owner_properties():
    """Get owner's properties"""
    owner_id = session.get('user_id')
    
    query = """
    SELECT 
        p.property_id,
        p.address,
        p.city,
        p.description,
        p.sq_footage,
        p.monthly_rent,
        p.status,
        t.tenant_id,
        t.name AS tenant_name,
        t.email AS tenant_email,
        t.phone AS tenant_phone,
        occ.occupancy_id,
        occ.start_date,
        occ.end_date
    FROM PROPERTY p
    LEFT JOIN OCCUPANCY occ ON p.property_id = occ.property_id AND occ.end_date IS NULL
    LEFT JOIN TENANT t ON occ.tenant_id = t.tenant_id
    WHERE p.owner_id = %s
    ORDER BY p.property_id
    """
    result = db.execute_query(query, (owner_id,))
    
    if result['success']:
        # Get reviews and payments for each property
        for prop in result['data']:
            # Reviews
            review_query = """
            SELECT r.rating, r.comment, r.review_date, t.name AS tenant_name
            FROM REVIEW r
            JOIN TENANT t ON r.tenant_id = t.tenant_id
            WHERE r.property_id = %s
            ORDER BY r.review_date DESC
            """
            reviews = db.execute_query(review_query, (prop['property_id'],))
            prop['reviews'] = reviews['data'] if reviews['success'] else []
            
            # Average rating
            avg_query = "SELECT fn_get_avg_rating(%s) AS avg_rating"
            avg_result = db.execute_query(avg_query, (prop['property_id'],))
            prop['avg_rating'] = avg_result['data'][0]['avg_rating'] if avg_result['success'] else None
            
            # Payment history if occupied
            if prop['occupancy_id']:
                payment_query = """
                SELECT payment_id, amount, payment_date, month_year, method, status
                FROM PAYMENTS
                WHERE occupancy_id = %s
                ORDER BY payment_date DESC
                """
                payments = db.execute_query(payment_query, (prop['occupancy_id'],))
                prop['payments'] = payments['data'] if payments['success'] else []
    
    return jsonify(result)

@app.route('/api/owner/property', methods=['POST'])
def create_property():
    """Create new property"""
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.json
    owner_id = session.get('user_id')
    
    query = """
    INSERT INTO PROPERTY (owner_id, address, city, description, sq_footage, monthly_rent, status)
    VALUES (%s, %s, %s, %s, %s, %s, 'Available')
    """
    params = (
        owner_id,
        data.get('address'),
        data.get('city'),
        data.get('description'),
        data.get('sq_footage'),
        data.get('monthly_rent')
    )
    
    result = db.execute_query(query, params, fetch=False)
    
    if result['success']:
        result['message'] = 'Property created successfully with status: Available'
    
    return jsonify(result)

@app.route('/api/owner/property/<int:property_id>', methods=['PUT'])
def update_property(property_id):
    """Update property"""
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.json
    owner_id = session.get('user_id')
    
    # Verify ownership
    check_query = "SELECT owner_id FROM PROPERTY WHERE property_id = %s"
    check = db.execute_query(check_query, (property_id,))
    
    if not check['success'] or len(check['data']) == 0:
        return jsonify({'success': False, 'error': 'Property not found'})
    
    if check['data'][0]['owner_id'] != owner_id:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    query = """
    UPDATE PROPERTY 
    SET address = %s, city = %s, description = %s, 
        sq_footage = %s, monthly_rent = %s, status = %s
    WHERE property_id = %s
    """
    params = (
        data.get('address'),
        data.get('city'),
        data.get('description'),
        data.get('sq_footage'),
        data.get('monthly_rent'),
        data.get('status'),
        property_id
    )
    
    result = db.execute_query(query, params, fetch=False)
    
    if result['success']:
        result['message'] = 'Property updated successfully'
    
    return jsonify(result)

@app.route('/api/owner/property/<int:property_id>', methods=['DELETE'])
def delete_property(property_id):
    """Delete property"""
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    owner_id = session.get('user_id')
    
    # Verify ownership
    check_query = "SELECT owner_id FROM PROPERTY WHERE property_id = %s"
    check = db.execute_query(check_query, (property_id,))
    
    if not check['success'] or len(check['data']) == 0:
        return jsonify({'success': False, 'error': 'Property not found'})
    
    if check['data'][0]['owner_id'] != owner_id:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    query = "DELETE FROM PROPERTY WHERE property_id = %s"
    result = db.execute_query(query, (property_id,), fetch=False)
    
    if result['success']:
        result['message'] = 'Property deleted successfully'
    
    return jsonify(result)

# ==================== TENANT ROUTES ====================

@app.route('/tenant')
def tenant_dashboard():
    """Tenant dashboard"""
    if session.get('role') != 'tenant':
        return redirect(url_for('index'))
    return render_template('tenant_dashboard.html')

@app.route('/api/tenant/rentals')
def tenant_rentals():
    """Get tenant's current and past rentals"""
    tenant_id = session.get('user_id')
    
    query = """
    SELECT 
        p.property_id,
        p.address,
        p.city,
        p.description,
        p.sq_footage,
        p.monthly_rent,
        p.status,
        o.name AS owner_name,
        o.phone AS owner_phone,
        occ.occupancy_id,
        occ.start_date,
        occ.end_date
    FROM OCCUPANCY occ
    JOIN PROPERTY p ON occ.property_id = p.property_id
    JOIN OWNER o ON p.owner_id = o.owner_id
    WHERE occ.tenant_id = %s
    ORDER BY occ.start_date DESC
    """
    result = db.execute_query(query, (tenant_id,))
    
    if result['success']:
        for rental in result['data']:
            # Get payment history
            payment_query = """
            SELECT payment_id, amount, payment_date, month_year, method, status
            FROM PAYMENTS
            WHERE occupancy_id = %s
            ORDER BY payment_date DESC
            """
            payments = db.execute_query(payment_query, (rental['occupancy_id'],))
            rental['payments'] = payments['data'] if payments['success'] else []
            
            # Calculate if rent is due (simplified - check if current month payment exists)
            current_month = datetime.now().strftime('%Y-%m')
            rental['rent_due'] = True
            for payment in rental['payments']:
                if payment['month_year'] == current_month and payment['status'] in ['Paid', 'Pending']:
                    rental['rent_due'] = False
                    break
    
    return jsonify(result)

@app.route('/api/tenant/review', methods=['POST'])
def submit_review():
    """Submit review for property"""
    if session.get('role') != 'tenant':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.json
    tenant_id = session.get('user_id')
    
    query = """
    INSERT INTO REVIEW (tenant_id, property_id, rating, comment, review_date)
    VALUES (%s, %s, %s, %s, CURDATE())
    """
    params = (
        tenant_id,
        data.get('property_id'),
        data.get('rating'),
        data.get('comment')
    )
    
    result = db.execute_query(query, params, fetch=False)
    
    if result['success']:
        result['message'] = 'Review submitted successfully'
    else:
        # Check if duplicate review trigger fired
        if 'duplicate' in result.get('error', '').lower():
            result['message'] = 'You have already reviewed this property'
    
    return jsonify(result)

@app.route('/api/tenant/request-rent', methods=['POST'])
def request_rent():
    """Request to rent a property"""
    if session.get('role') != 'tenant':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.json
    tenant_id = session.get('user_id')
    property_id = data.get('property_id')
    
    # Check if property is available
    check_query = "SELECT status FROM PROPERTY WHERE property_id = %s"
    check = db.execute_query(check_query, (property_id,))
    
    if not check['success'] or len(check['data']) == 0:
        return jsonify({'success': False, 'error': 'Property not found'})
    
    if check['data'][0]['status'] != 'Available':
        return jsonify({'success': False, 'error': 'Property is not available'})
    
    # Create occupancy record
    query = """
    INSERT INTO OCCUPANCY (tenant_id, property_id, start_date, end_date)
    VALUES (%s, %s, CURDATE(), NULL)
    """
    result = db.execute_query(query, (tenant_id, property_id), fetch=False)
    
    if result['success']:
        # Trigger should have updated property status to 'Rented'
        result['message'] = 'Rental request successful! Property status updated to Rented.'
    
    return jsonify(result)

# ==================== BROWSE PROPERTIES (OWNER & TENANT) ====================

@app.route('/api/properties/browse')
def browse_properties():
    """Browse all available properties"""
    query = """
    SELECT 
        p.property_id,
        p.address,
        p.city,
        p.description,
        p.sq_footage,
        p.monthly_rent,
        p.status,
        o.name AS owner_name,
        o.phone AS owner_phone
    FROM PROPERTY p
    JOIN OWNER o ON p.owner_id = o.owner_id
    ORDER BY p.city, p.monthly_rent
    """
    result = db.execute_query(query)
    
    if result['success']:
        # Get average rating for each property
        for prop in result['data']:
            avg_query = "SELECT fn_get_avg_rating(%s) AS avg_rating"
            avg_result = db.execute_query(avg_query, (prop['property_id'],))
            prop['avg_rating'] = avg_result['data'][0]['avg_rating'] if avg_result['success'] else None
    
    return jsonify(result)

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False') == 'True'
    app.run(debug=debug_mode, port=5000)
