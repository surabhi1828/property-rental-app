from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import Database
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback_secret_key')

db = Database()

# Initialize database connection when app starts
with app.app_context():
    db.connect()


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
            o.phone as owner_phone,
            (SELECT AVG(r.rating) FROM REVIEW r WHERE r.property_id = p.property_id) as avg_rating
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
    
    try:
        result = db.execute_query(query, tuple(params))
        properties = result['data'] if result['success'] else []
        return render_template('home.html', properties=properties)
        
    except Exception as e:
        print(f"!!! ERROR in /: {e}")
        return render_template('home.html', properties=[])


@app.route('/login')
def index():
    """MOVED Role selection page (was at '/')"""
    session.clear()
    return render_template('index.html')

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
        if data.get('username') == 'admin' and data.get('password') == 'admin':
            session['role'] = 'admin'
            session['user_id'] = 0
            session['user_name'] = 'Administrator'
            return jsonify({'success': True, 'redirect': '/admin'})
        else:
            return jsonify({'success': False, 'error': 'Invalid admin credentials'})
    
    elif role in ['owner', 'tenant']:
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        
        if not name or not email:
            return jsonify({'success': False, 'error': 'Name and Email are required'})
            
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

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template('admin_dashboard.html')


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
        
        # Removed the review count as requested
        stats = {
            'total_users': (users_result['data'][0]['count'] or 0) if (users_result['success'] and users_result['data']) else 0,
            'total_properties': (props_result['data'][0]['count'] or 0) if (props_result['success'] and props_result['data']) else 0
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
    

@app.route('/api/admin/rating_report')
def admin_rating_report():
    """
    Fetches all properties and calculates their average rating
    by explicitly calling the fn_get_avg_rating() SQL function.
    This is a perfect demo for showing the use of SQL functions.
    """
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        # This query calls your function for every row
        query = """
        SELECT 
            p.property_id, 
            p.address, 
            p.city, 
            o.name AS owner_name,
            fn_get_avg_rating(p.property_id) AS average_rating
        FROM PROPERTY p
        JOIN OWNER o ON p.owner_id = o.owner_id
        ORDER BY average_rating DESC;
        """
        
        result = db.execute_query(query, ())
        return jsonify(result)
        
    except Exception as e:
        print(f"!!! ERROR in /api/admin/rating_report: {e}")
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
    """Get owner's properties. NO NESTED QUERIES."""
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'error': 'Unauthorized'})
        
    owner_id = session.get('user_id')
    
    query = """
    SELECT 
        p.property_id, p.address, p.city, p.description, p.sq_footage,
        p.monthly_rent, p.status,
        t.tenant_id, t.name AS tenant_name, t.email AS tenant_email, t.phone AS tenant_phone,
        occ.occupancy_id, occ.start_date, occ.end_date
    FROM PROPERTY p
    LEFT JOIN OCCUPANCY occ ON p.property_id = occ.property_id AND occ.end_date IS NULL
    LEFT JOIN TENANT t ON occ.tenant_id = t.tenant_id
    WHERE p.owner_id = %s
    ORDER BY p.property_id
    """
    
    try:
        result = db.execute_query(query, (owner_id,))
        return jsonify(result)
    except Exception as e:
        print(f"!!! ERROR in /api/owner/properties: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/owner/stats')
def owner_stats():
    """Get dashboard stats for the logged-in owner."""
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    owner_id = session.get('user_id')
    
    try:
        query_total = "SELECT COUNT(*) AS count FROM PROPERTY WHERE owner_id = %s"
        total_result = db.execute_query(query_total, (owner_id,))
        
        query_rented = "SELECT COUNT(*) AS count FROM PROPERTY WHERE owner_id = %s AND status = 'Rented'"
        rented_result = db.execute_query(query_rented, (owner_id,))
        
        stats = {
            'total_properties': (total_result['data'][0]['count'] or 0) if (total_result['success'] and total_result['data']) else 0,
            'rented_properties': (rented_result['data'][0]['count'] or 0) if (rented_result['success'] and rented_result['data']) else 0
        }
        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        print(f"!!! ERROR in /api/owner/stats: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/owner/property/<int:property_id>', methods=['GET'])
def get_owner_property_details(property_id):
    """Get details for a single property, verifying ownership."""
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'error': 'Unauthorized'})
        
    owner_id = session.get('user_id')
    
    try:
        query = "SELECT * FROM PROPERTY WHERE property_id = %s AND owner_id = %s"
        result = db.execute_query(query, (property_id, owner_id))
        
        if result['success'] and len(result['data']) > 0:
            return jsonify({'success': True, 'data': result['data'][0]})
        elif result['success']:
            return jsonify({'success': False, 'error': 'Property not found or not owned by you'})
        else:
            return jsonify(result) # Send back the database error
            
    except Exception as e:
        print(f"!!! ERROR in /api/owner/property/<id>: {e}")
        return jsonify({'success': False, 'error': str(e)})


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
    
    # fetch=False is correct for a simple INSERT
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
    
    try:
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
    except Exception as e:
        print(f"!!! ERROR in /api/owner/property/PUT: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/owner/property/<int:property_id>', methods=['DELETE'])
def delete_property(property_id):
    """Delete property"""
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    owner_id = session.get('user_id')
    
    try:
        check_query = "SELECT owner_id FROM PROPERTY WHERE property_id = %s"
        check = db.execute_query(check_query, (property_id,))
        
        if not check['success'] or len(check['data']) == 0:
            return jsonify({'success': False, 'error': 'Property not found'})
        
        if check['data'][0]['owner_id'] != owner_id:
            return jsonify({'success': False, 'error': 'Unauthorized'})
        
        # We must delete child records first
        
        # Find occupancy records to delete payments
        occ_query = "SELECT occupancy_id FROM OCCUPANCY WHERE property_id = %s"
        occ_result = db.execute_query(occ_query, (property_id,))
        
        if occ_result['success'] and occ_result['data']:
            occ_ids = [row['occupancy_id'] for row in occ_result['data']]
            if occ_ids:
                occ_id_list = ','.join(map(str, occ_ids))
                pay_query = f"DELETE FROM PAYMENTS WHERE occupancy_id IN ({occ_id_list})"
                db.execute_query(pay_query, (), fetch=False)

        # Now delete reviews, occupancy, and finally the property
        db.execute_query("DELETE FROM REVIEW WHERE property_id = %s", (property_id,), fetch=False)
        db.execute_query("DELETE FROM OCCUPANCY WHERE property_id = %s", (property_id,), fetch=False)
        result = db.execute_query("DELETE FROM PROPERTY WHERE property_id = %s", (property_id,), fetch=False)
        
        if result['success']:
            result['message'] = 'Property and all related records deleted successfully'
        
        return jsonify(result)
        
    except Exception as e:
        print(f"!!! ERROR in /api/owner/property/DELETE: {e}")
        return jsonify({'success': False, 'error': 'A database error occurred during deletion.'})


@app.route('/api/owner/all_tenants')
def get_all_tenants():
    """Fetches all tenants to populate a dropdown."""
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        query = "SELECT tenant_id, name, email FROM TENANT ORDER BY name"
        result = db.execute_query(query, ())
        return jsonify(result)
    except Exception as e:
        print(f"!!! ERROR in /api/owner/all_tenants: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/owner/assign_tenant', methods=['POST'])
def assign_tenant():
    """Assigns a tenant to a property by creating an OCCUPANCY record."""
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'error': 'Unauthorized'})
        
    data = request.json
    property_id = data.get('property_id')
    tenant_id = data.get('tenant_id')
    owner_id = session.get('user_id')

    try:
        check_query = "SELECT owner_id, status FROM PROPERTY WHERE property_id = %s"
        check = db.execute_query(check_query, (property_id,))
        
        if not check['success'] or not check['data']:
            return jsonify({'success': False, 'error': 'Property not found'})
        if check['data'][0]['owner_id'] != owner_id:
            return jsonify({'success': False, 'error': 'Unauthorized'})
        if check['data'][0]['status'] != 'Available':
             return jsonify({'success': False, 'error': 'Property is already rented'})

        # Check for same-day re-assignment
        check_duplicate_query = """
            SELECT occupancy_id FROM OCCUPANCY 
            WHERE tenant_id = %s AND property_id = %s AND start_date = CURDATE()
        """
        duplicate_check = db.execute_query(check_duplicate_query, (tenant_id, property_id))
        
        if duplicate_check['success'] and len(duplicate_check['data']) > 0:
            return jsonify({
                'success': False, 
                'error': 'This tenant was already assigned to this property today.'
            })

        query = """
            INSERT INTO OCCUPANCY (tenant_id, property_id, start_date)
            VALUES (%s, %s, CURDATE())
        """
        # This INSERT fires a trigger, so fetch=True is CRITICAL
        result = db.execute_query(query, (tenant_id, property_id), fetch=True)
        
        if result['success']:
            result['message'] = 'Tenant assigned successfully! Property is now Rented.'
            
        return jsonify(result)

    except Exception as e:
        print(f"!!! ERROR in /api/owner/assign_tenant: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/owner/end_tenancy', methods=['POST'])
def end_tenancy():
    """Ends a tenancy by calling the sp_checkout_tenant stored procedure."""
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'error': 'Unauthorized'})
        
    data = request.json
    occupancy_id = data.get('occupancy_id')
    owner_id = session.get('user_id')

    try:
        check_query = """
            SELECT p.owner_id 
            FROM OCCUPANCY o
            JOIN PROPERTY p ON o.property_id = p.property_id
            WHERE o.occupancy_id = %s
        """
        check = db.execute_query(check_query, (occupancy_id,))
        
        if not check['success'] or not check['data']:
             return jsonify({'success': False, 'error': 'Occupancy record not found.'})
        if check['data'][0]['owner_id'] != owner_id:
            return jsonify({'success': False, 'error': 'Unauthorized'})

        query = "CALL sp_checkout_tenant(%s, CURDATE())"
        
        # CALLing a procedure requires fetch=True to clear the connection
        result = db.execute_query(query, (occupancy_id,), fetch=True)
        
        if result['success']:
            result['message'] = 'Tenancy ended. Property is now Available.'
            
        return jsonify(result)

    except Exception as e:
        print(f"!!! ERROR in /api/owner/end_tenancy: {e}")
        return jsonify({'success': False, 'error': str(e)})
    

@app.route('/api/owner/payments')
def get_owner_payments():
    """Get all payments for a specific owner, filterable by month."""
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'error': 'Unauthorized'})
        
    owner_id = session.get('user_id')
    
    # Get the month from the query string, e.g., /api/owner/payments?month=2025-11
    # Default to the current month if not provided
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    try:
        query = """
        SELECT 
            pay.payment_id,
            pay.amount,
            pay.payment_date,
            pay.month_year,
            pay.method,
            pay.status,
            t.name AS tenant_name,
            p.address AS property_address
        FROM PAYMENTS pay
        JOIN OCCUPANCY occ ON pay.occupancy_id = occ.occupancy_id
        JOIN PROPERTY p ON occ.property_id = p.property_id
        JOIN TENANT t ON occ.tenant_id = t.tenant_id
        WHERE 
            p.owner_id = %s 
            AND pay.month_year = %s
        ORDER BY pay.payment_date DESC
        """
        
        result = db.execute_query(query, (owner_id, selected_month))
        return jsonify(result)
        
    except Exception as e:
        print(f"!!! ERROR in /api/owner/payments: {e}")
        return jsonify({'success': False, 'error': str(e)})

# ... (rest of your app.py file) ...


# ==================== TENANT ROUTES ====================

@app.route('/tenant')
def tenant_dashboard():
    """Tenant dashboard"""
    if session.get('role') != 'tenant':
        return redirect(url_for('index'))
    return render_template('tenant_dashboard.html')

@app.route('/api/tenant/rentals')
def tenant_rentals():
    """Get tenant's current and past rentals. NO NESTED QUERIES."""
    if session.get('role') != 'tenant':
        return jsonify({'success': False, 'error': 'Unauthorized'})
        
    tenant_id = session.get('user_id')
    
    try:
        # First, get all rental (occupancy) details
        query = """
        SELECT 
            p.property_id, p.address, p.city, p.description, p.sq_footage,
            p.monthly_rent, p.status,
            o.name AS owner_name, o.phone AS owner_phone,
            occ.occupancy_id, occ.start_date, occ.end_date
        FROM OCCUPANCY occ
        JOIN PROPERTY p ON occ.property_id = p.property_id
        JOIN OWNER o ON p.owner_id = o.owner_id
        WHERE occ.tenant_id = %s
        ORDER BY occ.start_date DESC
        """
        rental_result = db.execute_query(query, (tenant_id,))
        if not rental_result['success']:
            return jsonify(rental_result)

        # Now, get ALL payments for this tenant in ONE query
        payment_query = """
            SELECT p.payment_id, p.amount, p.payment_date, p.month_year, p.method, p.status, p.occupancy_id
            FROM PAYMENTS p
            JOIN OCCUPANCY o ON p.occupancy_id = o.occupancy_id
            WHERE o.tenant_id = %s
        """
        payment_result = db.execute_query(payment_query, (tenant_id,))
        
        payments_map = {}
        if payment_result['success'] and payment_result['data']:
            for payment in payment_result['data']:
                occ_id = payment['occupancy_id']
                if occ_id not in payments_map:
                    payments_map[occ_id] = []
                payments_map[occ_id].append(payment)

        # Now, combine the data in Python (fast, no nested queries)
        current_month = datetime.now().strftime('%Y-%m')
        for rental in rental_result['data']:
            # Assign payments
            rental['payments'] = payments_map.get(rental['occupancy_id'], [])
            
            # Calculate rent_due
            rental['rent_due'] = True
            if rental['end_date'] is not None: # If tenancy is over, rent is not due
                rental['rent_due'] = False
            else:
                for payment in rental['payments']:
                    if payment['month_year'] == current_month and payment['status'] in ['Paid', 'Pending']:
                        rental['rent_due'] = False
                        break
        
        return jsonify(rental_result)

    except Exception as e:
        print(f"!!! ERROR in /api/tenant/rentals: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/tenant/make_payment', methods=['POST'])
def make_payment():
    """Simulates making a payment for a specific occupancy."""
    if session.get('role') != 'tenant':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.json
    occupancy_id = data.get('occupancy_id')
    tenant_id = session.get('user_id')

    try:
        check_query = "SELECT tenant_id FROM OCCUPANCY WHERE occupancy_id = %s"
        check = db.execute_query(check_query, (occupancy_id,))
        
        if not check['success'] or not check['data']:
            return jsonify({'success': False, 'error': 'Occupancy record not found.'})
        if check['data'][0]['tenant_id'] != tenant_id:
            return jsonify({'success': False, 'error': 'Unauthorized action.'})

        query = """
            INSERT INTO PAYMENTS (occupancy_id, amount, payment_date, month_year, method, status)
            VALUES (%s, %s, CURDATE(), %s, %s, 'Paid')
        """
        params = (
            occupancy_id,
            data.get('amount'),
            data.get('month_year'),
            data.get('method')
        )
        
        result = db.execute_query(query, params, fetch=False)
        
        if result['success']:
            result['message'] = 'Payment successful!'
        
        return jsonify(result)

    except Exception as e:
        print(f"!!! ERROR in /api/tenant/make_payment: {e}")
        return jsonify({'success': False, 'error': str(e)})


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
    
    # We use fetch=False, just like your working signup() function.
    # This will allow your database.py to handle the commit correctly.
    result = db.execute_query(query, params, fetch=False)
    
    if result['success']:
        result['message'] = 'Review submitted successfully'
    else:
        # Check if the trigger fired (which is an error we expect)
        if result.get('error') and 'trg_prevent_duplicate_review' in result.get('error', ''):
            result['message'] = 'You have already reviewed this property'
            result['error'] = 'You have already reviewed this property' # Make error clear
        elif result.get('error'):
             result['error'] = 'You have already reviewed this property' # General error
        
    return jsonify(result)


@app.route('/api/tenant/request-rent', methods=['POST'])
def request_rent():
    """Request to rent a property"""
    if session.get('role') != 'tenant':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.json
    tenant_id = session.get('user_id')
    property_id = data.get('property_id')
    
    try:
        check_query = "SELECT status FROM PROPERTY WHERE property_id = %s"
        check = db.execute_query(check_query, (property_id,))
        
        if not check['success'] or len(check['data']) == 0:
            return jsonify({'success': False, 'error': 'Property not found'})
        
        if check['data'][0]['status'] != 'Available':
            return jsonify({'success': False, 'error': 'Property is not available'})
        
        query = """
        INSERT INTO OCCUPANCY (tenant_id, property_id, start_date, end_date)
        VALUES (%s, %s, CURDATE(), NULL)
        """
        
        # This INSERT fires a trigger, so fetch=True is CRITICAL
        result = db.execute_query(query, (tenant_id, property_id), fetch=True)
        
        if result['success']:
            result['message'] = 'Rental request successful! Property status updated to Rented.'
        
        return jsonify(result)
        
    except Exception as e:
        print(f"!!! ERROR in /api/tenant/request-rent: {e}")
        return jsonify({'success': False, 'error': str(e)})

# ==================== BROWSE PROPERTIES ====================

@app.route('/api/properties/browse')
def browse_properties():
    """Browse all available properties, NO NESTED QUERIES."""
    
    # This query now joins a subquery to get the avg_rating
    # This is efficient and avoids nested loops.
    query = """
    SELECT 
        p.property_id, p.address, p.city, p.description, p.sq_footage,
        p.monthly_rent, p.status,
        o.name AS owner_name,
        o.phone AS owner_phone,
        COALESCE(r.avg_rating, 0) AS avg_rating
    FROM PROPERTY p
    JOIN OWNER o ON p.owner_id = o.owner_id
    LEFT JOIN (
        SELECT property_id, AVG(rating) as avg_rating
        FROM REVIEW
        GROUP BY property_id
    ) r ON p.property_id = r.property_id
    WHERE p.status = 'Available'
    ORDER BY p.city, p.monthly_rent
    """
    try:
        result = db.execute_query(query, ())
        return jsonify(result)
    except Exception as e:
        print(f"!!! ERROR in /api/properties/browse: {e}")
        return jsonify({'success': False, 'error': str(e)})

# ==================== MAIN RUN ====================

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False') == 'True'
    app.run(debug=debug_mode, port=5000)