import os
import secrets
import re
import logging
from datetime import timedelta, datetime
from flask import Flask, jsonify, request, session
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from flask_migrate import Migrate
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from models import Employee, Product, InventoryTransaction, Transaction, SaleItem, Customer, MpesaToken, AuditLog, Category, Inventory, SalesReport
import requests
import base64
import jwt
from utils import (
    binary_search, quicksort, process_transaction,
    validate_inventory_levels, restock_product, generate_sales_report
)
from requests.auth import HTTPBasicAuth
from sqlalchemy.exc import SQLAlchemyError, DatabaseError
from marshmallow import ValidationError
from functools import wraps


from extensions import db,limiter
from marshmallow import Schema, fields, validate, ValidationError
 # Import the seed function
from functools import wraps
from decimal import Decimal
    

# Load environment variables
load_dotenv()

# Initialize extensions



# Initialize extensions
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pos.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = True

    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_COOKIE_SECURE'] = True
    app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
    app.config['JWT_CSRF_IN_COOKIES'] = True


    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=["http://localhost:5173"], supports_credentials=True)
    JWTManager(app)

    # app.register_blueprint(auth_blueprint, url_prefix='/auth')
    # app.register_blueprint(product_blueprint, url_prefix='/products')

    # Swagger UI setup
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': "Flask API"})
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    return app

# Create the app instance
app = create_app()


# Create database tables
with app.app_context():
    db.create_all()
 
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-3D-POS-TOKEN')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = Employee.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated


def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            logging.error(f"Validation error: {e.messages}")
            return jsonify({"error": e.messages}), 400
        except DatabaseError:
            logging.error("Database failure")
            return jsonify({"error": "Database failure"}), 500
    return wrapper


# Centralized error handling
class SignupSchema(Schema):
    username = fields.Str(required=True, validate=[
        validate.Length(min=3, max=20),
        validate.Regexp(r'^[a-zA-Z0-9_]+$', error="Only letters, numbers and underscores allowed")
    ])
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=[
        validate.Length(min=8),
        validate.Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])', 
                      error="Must contain uppercase, number, and special character")
    ])
    role = fields.Str(required=True, validate=validate.OneOf(['cashier', 'manager']))
    recaptchaToken = fields.Str(required=True)
# Sign up route

@app.route('/auth/signup', methods=['POST'])
@limiter.limit("10 per minute")
def signup():
    try:
        data = request.get_json()
        
        # Validate role
        role = data.get("role", "").strip().lower()
        if role not in {"cashier", "manager"}:
            return jsonify({
                "error": "Validation failed",
                "errors": {"role": ["Must be one of: cashier, manager"]}
            }), 400
        
        # Validate password
        if (password_error := validate_password(data.get("password", ""))):
            return jsonify({
                "error": "Validation failed",
                "errors": {"password": [password_error]}
            }), 400

        # Clean and normalize data
        clean_data = {
            'username': data.get('username', '').strip(),
            'email': data.get('email', '').lower().strip(),
            'password': data.get('password', ''),
            'role': role
        }

        # Check for existing user
        if existing := Employee.find_by_username_or_email(clean_data['username'], clean_data['email']):
            errors = {}
            if existing.username == clean_data['username']:
                errors['username'] = ["Username already exists"]
            if existing.email == clean_data['email']:
                errors['email'] = ["Email already exists"]
            return jsonify({"error": "Validation failed", "errors": errors}), 400

        # Create new employee
        new_employee = Employee(
            username=clean_data['username'],
            email=clean_data['email'],
            role=role
        )
        new_employee.password = clean_data['password']

        db.session.add(new_employee)
        db.session.commit()

        return jsonify({
            'message': 'User created successfully',
            'user': {
                'id': new_employee.id,
                'username': new_employee.username,
                'email': new_employee.email,
                'role': new_employee.role
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

# Password validation function
def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"\d", password):
        return "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character."
    return None  # No errors
@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
    else:
        username = request.form.get('username')
        password = request.form.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    employee = Employee.query.filter_by(username=username).first()
    app.logger.debug(f"Found employee: {employee}")
    if employee:
        app.logger.debug(f"Stored hash: {employee.password_hash}, Salt: {employee.salt}, Provided password: {password}")
    if employee and employee.verify_password(password):
        access_token = create_access_token(identity={'id': employee.id, 'role': employee.role})
        return jsonify({'message': 'Login successful', 'token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401



# Logout route
@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logs the user out by returning a success message."""
    return jsonify({'message': 'Successfully logged out'}), 200



@app.route('/inventory', methods=['GET'])
def get_inventory_transactions():
    try:
        # Fetch all inventory transactions
        transactions = InventoryTransaction.query.all()
        
        # Return the data as a JSON response
        return jsonify({
            'transactions': [
                {
                    'id': transaction.id,
                    'product_name': transaction.product.name,
                    'change_quantity': transaction.change_quantity,
                    'transaction_type': transaction.transaction_type,
                    'reason': transaction.reason,
                    'timestamp': transaction.timestamp
                } for transaction in transactions
            ]
        }), 200
    except Exception as e:
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

# Products route



@app.route('/products', methods=['GET', 'POST'])
@jwt_required()
def manage_products():
    try:
        # Verify valid JWT exists
        current_user = get_jwt_identity()
        if not current_user:
            return jsonify({"message": "Invalid credentials"}), 401

        if request.method == 'GET':
            products = Product.query.all()
            product_list = [
                {
                    'id': product.id,
                    'name': product.name,
                    'price': float(product.price),  # Convert Decimal to float
                    'stock': product.stock_quantity,
                    'category_id': product.category_id or None
                } for product in products
            ]
            return jsonify({'products': product_list}), 200

        elif request.method == 'POST':
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['name', 'price', 'stock']
            if not all(field in data for field in required_fields):
                return jsonify({'message': 'Missing required fields'}), 400

            # Generate unique SKU if not provided
            sku = data.get('sku')
            if not sku:
                # Generate unique SKU using name and random string
                name_part = data['name'][:3].upper()
                random_part = secrets.token_hex(2).upper()
                sku = f"{name_part}-{random_part}"
                
                # Ensure uniqueness
                while Product.query.filter_by(sku=sku).first():
                    random_part = secrets.token_hex(2).upper()
                    sku = f"{name_part}-{random_part}"

            try:
                new_product = Product(
                    sku=sku,  # Add generated SKU
                    name=data['name'],
                    price=Decimal(str(data['price'])),
                    stock_quantity=int(data['stock']),
                    category_id=data.get('category_id')
                )
                db.session.add(new_product)
                db.session.commit()
                
                return jsonify({
                    'message': 'Product added',
                    'product': {
                        'id': new_product.id,
                        'name': new_product.name,
                        'price': float(new_product.price),
                        'sku': new_product.sku  # Return generated SKU
                    }
                }), 201
                
            except (ValueError, TypeError) as e:
                db.session.rollback()
                return jsonify({'message': 'Invalid data format', 'error': str(e)}), 422

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Server error', 'error': str(e)}), 500

# Routes
@app.route('/reports/sales', methods=['GET'])
def get_sales_report():
    granularity = request.args.get('granularity', 'hourly')
    now = datetime.now()

    if granularity == 'hourly':
        start_time = now - timedelta(hours=24)
        sales_data = SalesReport.query.filter(SalesReport.timestamp >= start_time).all()
    else:
        return jsonify({"error": "Invalid granularity"}), 400

    report = [
        {
            'timestamp': sale.timestamp.isoformat(),
            'total_sales': sale.total_sales,
            'transaction_count': sale.transaction_count
        } for sale in sales_data
    ]

    return jsonify({ 'report': report })

@app.route('/inventory-monitoring', methods=['POST'])
@jwt_required()
def post_inventory_monitoring():
    try:
        critical_items = Inventory.query.filter(Inventory.stock_level < Inventory.critical_stock).all()
        total_products = Inventory.query.count()

        return jsonify({
            "critical_stock": len(critical_items),
            "total_products": total_products,
            "critical_items": [
                {"name": item.name, "stock_level": item.stock_level}
                for item in critical_items
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/products_search', methods=['GET'])
@jwt_required()
@handle_errors
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    category_id = request.args.get('category_id', type=int)

    query = Product.query
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if min_price:
        query = query.filter(Product.price >= min_price)
    if max_price:
        query = query.filter(Product.price <= max_price)
    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'products': [product.to_dict() for product in products.items],
        'total': products.total,
        'pages': products.pages,
        'current_page': page
    }), 200

# Cart route
@app.route('/cart', methods=['GET'])
@jwt_required()
def cart():
    """Fetch the cart details for the current user."""
    cart_items = session.get('cart', [])
    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)

    return jsonify({'cart_items': cart_items, 'total_amount': total_amount}), 200

# Checkout route
@app.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    """Process the checkout for the current user's cart."""
    current_user = get_jwt_identity()
    employee_id = current_user['id']

    # Retrieve cart from session
    cart = session.get('cart', [])
    if not cart:
        return jsonify({'message': 'Cart is empty!'}), 400

    total_amount = sum(item['price'] * item['quantity'] for item in cart)
    transaction = Transaction(employee_id=employee_id, total_amount=total_amount, transaction_date=datetime.now())
    db.session.add(transaction)
    db.session.commit()

    for item in cart:
        sale_item = SaleItem(
            transaction_id=transaction.id,
            product_id=item['id'],
            quantity=item['quantity'],
            price=item['price']
        )
        product = Product.query.get(item['id'])
        if product.stock_quantity < item['quantity']:
            return jsonify({'message': f"Not enough stock for product ID {item['id']}"}), 400

        # Adjust product stock
        product.adjust_stock(-item['quantity'])

        # Log the inventory transaction
        inventory_transaction = InventoryTransaction(
            product_id=item['id'],
            change_quantity=-item['quantity'],  # Negative as stock is removed
            transaction_type='remove',  # Stock removal
            reason='sale'
        )
        db.session.add(inventory_transaction)
        db.session.add(sale_item)

    db.session.commit()
    session.pop('cart', None)  # Clear the cart after checkout

    return jsonify({'message': 'Transaction completed successfully!', 'transaction_id': transaction.id}), 200

@app.route('/reports/sales', methods=['GET'])
@jwt_required()
@handle_errors
def sales_report():
    start_date = request.args.get('start_date', default=(datetime.now() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', default=datetime.now().isoformat())
    granularity = request.args.get('granularity', 'daily')  # daily/weekly/monthly

    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError:
        raise ValueError("Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")

    # Generate report data
    report_data = Transaction.generate_sales_report(start, end, granularity)
    
    return jsonify({
        'start_date': start.isoformat(),
        'end_date': end.isoformat(),
        'granularity': granularity,
        'report': report_data
    }), 200

# Receipt route
@app.route('/receipt/<int:transaction_id>', methods=['GET'])
@jwt_required()
def receipt(transaction_id):
    """Retrieve the receipt for a specific transaction."""
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        return jsonify({'message': 'Transaction not found'}), 404

    sale_items = SaleItem.query.filter_by(transaction_id=transaction_id).all()
    items = [
        {'product_id': item.product_id, 'quantity': item.quantity, 'price': item.price}
        for item in sale_items
    ]

    return jsonify({
        'transaction_id': transaction.id,
        'employee_id': transaction.employee_id,
        'total_amount': transaction.total_amount,
        'transaction_date': transaction.transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
        'items': items
    }), 200

@app.route('/customers/<int:customer_id>/loyalty', methods=['POST'])
@jwt_required()
@handle_errors
def update_loyalty(customer_id):
    current_user = get_jwt_identity()
    if current_user['role'] not in ['admin', 'manager']:
        raise PermissionError("Insufficient privileges")
    
    data = request.get_json()
    customer = Customer.query.get_or_404(customer_id)
    points = data.get('points')
    
    if not isinstance(points, int):
        raise ValueError("Invalid points value")
    
    customer.loyalty_points += points
    db.session.commit()
    
    return jsonify({
        'customer_id': customer_id,
        'new_balance': customer.loyalty_points,
        'message': 'Loyalty points updated successfully'
    }), 200

# Admin route
@app.route('/admin', methods=['GET'])
@jwt_required()
def admin_only():
    """Admin-only route, restricted to users with the admin role."""
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Access denied'}), 403

    return jsonify({'message': 'Welcome, admin!'}), 200

@app.route('/payments', methods=['POST'])
def process_payment():
    """Process a payment using M-Pesa."""
    try:
        # Fetch request data
        data = request.get_json()
        payment_method = data.get('paymentMethod')
        amount = data.get('amount')

        if not payment_method or not amount:
            return jsonify({'message': 'Payment method and amount are required'}), 400

        # Fetch M-Pesa access token
        access_token = fetch_mpesa_token()
        if not access_token:
            return jsonify({'message': 'Failed to fetch M-Pesa access token'}), 500

        # Simulate payment processing (replace with actual M-Pesa API calls)
        payment_response = {
            'status': 'success',
            'paymentMethod': payment_method,
            'amount': amount,
            'transaction_id': '1234567890',
        }

        return jsonify({'message': 'Payment processed successfully', 'data': payment_response}), 200

    except Exception as e:
        logging.error(f"Error processing payment: {str(e)}")
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

@app.route('/sales', methods=['POST'])
@jwt_required()
def add_sale():
    data = request.get_json()
    customer_id = data.get('customerId')
    products = data.get('products')  # Assuming products is a list of dictionaries with `productId`, `quantity`, and `price`

    # Validation
    if not customer_id or not products:
        return jsonify({'message': 'Customer ID and product list are required'}), 400

    # Check if the customer exists
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'message': 'Customer not found'}), 404

    # Create a new transaction record
    new_transaction = Transaction(customer_id=customer_id)

    # Process each product in the sale
    sale_items = []
    total_amount = 0  # Total amount for the transaction

    for item in products:
        product_id = item.get('productId')
        quantity = item.get('quantity')
        price = item.get('price')

        if not product_id or not quantity or not price:
            return jsonify({'message': 'Each product must have productId, quantity, and price'}), 400

        # Check if the product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'message': f'Product {product_id} not found'}), 404

        # Check if there is enough stock for the product
        if product.stock_quantity < quantity:
            return jsonify({'message': f'Insufficient stock for product {product.name}'}), 400

        # Create the SaleItem record
        sale_item = SaleItem(
            transaction=new_transaction,  # Associate with the transaction
            product_id=product_id,
            quantity=quantity,
            price=price
        )

        sale_items.append(sale_item)

        # Adjust the stock for the product
        try:
            product.adjust_stock(-quantity)  # Reduce stock based on the quantity sold
        except ValueError as e:
            return jsonify({'message': str(e)}), 400

        # Calculate total amount
        total_amount += price * quantity

    # Add sale items to the transaction
    new_transaction.sale_items = sale_items
    new_transaction.total_amount = total_amount

    # Commit the transaction to the database
    try:
        db.session.add(new_transaction)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error processing sale', 'error': str(e)}), 500

    return jsonify({'message': 'Sale added successfully', 'transaction_id': new_transaction.id, 'total_amount': total_amount}), 200

@app.route('/reorder-alerts', methods=['GET'])
def reorder_alerts():
    """API endpoint to get products that need restocking."""
    alerts = Product.get_reorder_alerts()
    return jsonify([{"id": p.id, "name": p.name, "stock_quantity": p.stock_quantity} for p in alerts])

@app.route('/inventory-monitoring', methods=['GET'])
def inventory_monitoring():
    """API endpoint to get inventory monitoring summary."""
    summary = Product.monitor_inventory()
    return jsonify({
        "total_products": summary["total_products"],
        "critical_stock": summary["critical_stock"],
        "critical_items": [
            {"id": p.id, "name": p.name, "stock_quantity": p.stock_quantity}
            for p in summary["critical_items"]
        ]
    })

@app.route('/inventory/alerts', methods=['GET'])
@jwt_required()
@handle_errors
def get_inventory_alerts():
    threshold = request.args.get('threshold', default=10, type=int)
    products = Product.query.filter(Product.stock_quantity < threshold).all()
    
    return jsonify([{
        'product_id': p.id,
        'product_name': p.name,
        'current_stock': p.stock_quantity,
        'recommended_reorder': p.reorder_level
    } for p in products]), 200

# Fetch M-Pesa token
def fetch_mpesa_token():
    """
    Fetch and return M-Pesa access token.

    Parameters:
    None

    Returns:
    str: The M-Pesa access token if successful, None otherwise.
    """
    try:
        ckey = os.getenv('MPESA_CKEY')  # Consumer Key
        csecret = os.getenv('MPESA_CSECRET')  # Consumer Secret
        apiurl = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

        if not ckey or not csecret:
            logging.error("M-Pesa credentials are missing.")
            return None

        logging.info("Attempting to fetch M-Pesa token from the database.")
        mpesa_token = MpesaToken.query.filter(MpesaToken.expiration_time > datetime.now()).first()
        if (mpesa_token):
            logging.info("Using existing M-Pesa token from the database.")
            return mpesa_token.access_token

        logging.info("Fetching a new M-Pesa token from the API.")
        response = requests.get(apiurl, auth=HTTPBasicAuth(ckey, csecret))
        response.raise_for_status()

        token_data = response.json()
        access_token = token_data['access_token']
        expires_in = token_data['expires_in']
        expiration_time = datetime.now(datetime.timezone.utc) + timedelta(seconds=expires_in)
        logging.info("Saving the new M-Pesa token to the database.")
        
        # Save the new token to the database
        new_token = MpesaToken(access_token=access_token, expiration_time=expiration_time)
        db.session.add(new_token)
        db.session.commit()

        logging.info("M-Pesa token fetched and saved successfully.")
        return access_token
    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP error fetching M-Pesa token: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching M-Pesa token: {str(e)}")
        return None

# Route to add a new customer
@app.route('/addcustomer', methods=['POST'])
def add_customer():
    try:
        # Get the data from the incoming request
        data = request.get_json()

        # Extract fields
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')

        # Check if all required fields are provided
        if not name or not email or not phone:
            return jsonify({'message': 'Name, email, and phone are required'}), 400

        # Check for an existing customer by email
        existing_customer = Customer.query.filter_by(email=email).first()
        if existing_customer:
            return jsonify({'message': 'Customer with this email already exists'}), 400

        # Create a new customer object
        new_customer = Customer(name=name, email=email, phone=phone)

        # Add the new customer to the database
        db.session.add(new_customer)
        db.session.commit()

        return jsonify({'message': 'Customer added successfully', 'customer': {'id': new_customer.id, 'name': new_customer.name}}), 201

    except Exception as e:
        # Handle unexpected errors
        db.session.rollback()  # Rollback any partial changes to the database
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

@app.route('/payments/mpesa', methods=['POST'])
@jwt_required()
@handle_errors
def process_mpesa_payment():
    data = request.get_json()
    phone = data['phone']
    amount = data['amount']
    transaction_id = data['transaction_id']

    # Validate transaction
    transaction = Transaction.query.get(transaction_id)
    if transaction is None:
        return jsonify({'message': 'Transaction not found'}), 404
    
    # Process M-Pesa payment
    access_token = fetch_mpesa_token()
    if not access_token:
        return jsonify({'message': 'Failed to fetch M-Pesa access token'}), 500

    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'BusinessShortCode': os.getenv('MPESA_SHORTCODE'),
        'Password': generate_mpesa_password(),
        'Timestamp': datetime.now().strftime('%Y%m%d%H%M%S'),
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': amount,
        'PartyA': phone,
        'PartyB': os.getenv('MPESA_SHORTCODE'),
        'PhoneNumber': phone,
        'CallBackURL': f"{os.getenv('BASE_URL')}/mpesa-callback",
        'AccountReference': f"TX{transaction_id}",
        'TransactionDesc': 'POS Payment'
    }

    response = requests.post(
        'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
        json=payload,
        headers=headers
    )

    if response.status_code == 200:
        transaction.payment_reference = response.json()['CheckoutRequestID']
        transaction.payment_method = 'M-Pesa'
        db.session.commit()
        return jsonify({'message': 'Payment initiated successfully'}), 200

def generate_mpesa_password():
    """Generate the M-Pesa password for the STK push request."""
    shortcode = os.getenv('MPESA_SHORTCODE')
    passkey = os.getenv('MPESA_PASSKEY')
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = shortcode + passkey + timestamp
    encoded_string = base64.b64encode(data_to_encode.encode('utf-8')).decode('utf-8')
    return encoded_string

@app.route('/mpesa-callback', methods=['POST'])
def mpesa_callback():
    """Handle M-Pesa callback."""
    data = request.get_json()
    logging.info(f"M-Pesa callback data received: {data}")

    # Process the callback data here
    # Example: Update transaction status based on the callback data

    return jsonify({'message': 'Callback received successfully'}), 200

@app.route('/audit-logs', methods=['GET'])
@jwt_required()
@handle_errors
def get_audit_logs():
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        raise PermissionError("Access denied")
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page, per_page)
    
    return jsonify({
        'logs': [{
            'id': log.id,
            'user_id': log.user_id,
            'action': log.action,
            'timestamp': log.timestamp.isoformat(),
            'details': log.details
        } for log in logs.items],
        'total': logs.total,
        'pages': logs.pages
    }), 200

@app.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@handle_errors
def update_user(user_id):
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin' and current_user['id'] != user_id:
        raise PermissionError("Unauthorized access")

    user = Employee.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'password' in data:
        if not validate_password(data['password']):
            raise ValueError("Password does not meet security requirements")
        user.password_hash = generate_password_hash(data['password'])
    
    if 'role' in data and current_user['role'] == 'admin':
        user.role = data['role']
    
    db.session.commit()
    
    return jsonify({
        'message': 'User updated successfully',
        'user': {
            'id': user.id,
            'username': user.name,
            'role': user.role
        }
    }), 200

# Function to validate input fields
def validate_required_fields(data, required_fields):
    """Validate that all required fields are present in the request data."""
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
    return None
# ------------------- Holographic POS Routes -------------------
@app.route('/api/3d-auth', methods=['POST'])
def quantum_auth():
    auth_data = request.get_json()
    user = Employee.query.filter_by(username=auth_data['username']).first()
    
    if user and user.verify_password(auth_data['password']):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=8)
        }, app.config['SECRET_KEY'])
        return jsonify({
            'token': token,
            'hologram_token': secrets.token_hex(32),
            'user_role': user.role
        })
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/quantum-products', methods=['GET'])
@token_required
def get_quantum_products(current_user):
    products = Product.query.all()
    sorted_products = quicksort(products, key=lambda x: x.sku)
    return jsonify([{
        'id': p.id,
        'sku': p.sku,
        'name': p.name,
        'price': p.price,
        'stock': p.stock_quantity,
        'hologram': f'3d_{p.sku}_model.glb'
    } for p in sorted_products])

@app.route('/api/neuro-transaction', methods=['POST'])
@token_required
def create_neuro_transaction(current_user):
    data = request.get_json()
    try:
        products = [binary_search(Product.query.all(), sku, key=lambda x: x.sku) 
                   for sku in data['items']]
        transaction = process_transaction(products, current_user.id)
        return jsonify({
            'id': transaction.id,
            'total': transaction.total_amount,
            'hologram_summary': generate_sales_report(transaction)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/tesseract-report/<report_type>', methods=['GET'])
@token_required
def generate_tesseract_report(current_user, report_type):
    days = int(request.args.get('days', 7))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    report_data = generate_sales_report(start_date, datetime.utcnow())
    return jsonify({
        'report': quicksort(report_data['transactions'], key=lambda x: x.transaction_date),
        '3d_visualization': generate_sales_report(report_data)
    })

@app.route('/api/singularity-inventory', methods=['GET'])
@token_required
def check_singularity_inventory(current_user):
    inventory_status = validate_inventory_levels()
    return jsonify([{
        'sku': p.sku,
        'name': p.name,
        'stock': p.stock_quantity,
        'status': 'critical' if p.stock_quantity <= p.min_stock_level else 'ok',
        'quantum_restock': generate_sales_report(p)
    } for p in inventory_status])
# Function to send notifications (example function)
def send_notification(message, recipient):
    """Send notifications (e.g., via email or SMS)."""                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
    # Placeholder: Can integrate email/SMS APIs here
    logging.info(f"Notification sent to {recipient}: {message}")

# Utility to format error messages consistently
def format_error(message):
    """Format error messages for API response."""
    return {"status": "error", "message": message}


if __name__ == '__main__':
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    app.run(debug=True)
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
