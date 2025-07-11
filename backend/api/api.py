import os
import logging
from flask import request, jsonify
from flask_jwt_extended import (
    jwt_required, 
    get_jwt, 
    create_access_token, 
    create_refresh_token, 
    JWTManager
)
from flask_restful import Api, Resource, reqparse
from requests.auth import HTTPBasicAuth
import requests
from marshmallow import Schema, fields, ValidationError
from dotenv import load_dotenv
from datetime import timedelta
from models import  Employee, Product, Transaction, SaleItem, Category, InventoryTransaction, MpesaToken, Customer
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from extensions import db
# Load environment variables from .env file
load_dotenv()

# Initialize Flask-Limiter for rate-limiting
limiter = Limiter(get_remote_address)

# JWT blacklist for token revocation (Consider replacing with Redis for scalability)
blacklist = set()

# Correct way to register token_in_blocklist_loader with JWTManager
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    """Check if the JWT token is blacklisted (revoked), returns True if it is."""
    jti = jwt_payload['jti']
    return jti in blacklist


# Input validation schema for login
class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)


# Helper function: Error response with consistent format
def error_response(message, status_code):
    return jsonify({'message': message}), status_code


# Login route for generating tokens
class LoginResource(Resource):
    def post(self):
        """Authenticate user and generate JWT tokens."""
        schema = LoginSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return error_response(err.messages, 400)

        username = data['username']
        password = data['password']

        # Authenticate user
        employee = Employee.query.filter_by(name=username).first()
        if employee and employee.check_password(password):
            access_token = create_access_token(identity=employee.id, expires_delta=timedelta(hours=1))
            refresh_token = create_refresh_token(identity=employee.id)
            return {
                'access_token': access_token,
                'refresh_token': refresh_token
            }, 200
        else:
            return error_response('Invalid credentials', 401)


# Logout route for revoking the token
class LogoutResource(Resource):
    @jwt_required()
    def delete(self):
        """Revoke the current JWT token."""
        jti = get_jwt()['jti']
        blacklist.add(jti)
        return jsonify({'message': 'Logged out successfully'}), 200




# Employee Resource for managing employees
class EmployeeResource(Resource):
    @jwt_required()
    def post(self):
        """Create a new employee."""
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, help='Username is required')
        parser.add_argument('email', type=str, required=True, help='Email is required')
        parser.add_argument('password', type=str, required=True, help='Password is required')
        parser.add_argument('role', type=str, required=True, help='Role is required')
        args = parser.parse_args()

        # Check if the employee already exists
        if Employee.query.filter_by(username=args['username']).first():
            return {'error': 'Employee already exists'}, 400

        try:
            employee = Employee(
                username=args['username'],
                email=args['email'],
                role=args['role']
            )
            employee.password = args['password']  # Hashes the password
            db.session.add(employee)
            db.session.commit()
            return {'message': 'Employee created', 'employee_id': employee.id}, 201
        except Exception as e:
            logging.error(f"Error creating employee: {str(e)}")
            db.session.rollback()
            return {'error': 'Internal server error'}, 500

    @jwt_required()
    def get(self):
        """Fetch all employees."""
        try:
            employees = Employee.query.all()
            return [
                {'id': e.id, 'username': e.username, 'role': e.role}
                for e in employees
            ], 200
        except Exception as e:
            logging.error(f"Error fetching employees: {str(e)}")
            return {'error': 'Internal server error'}, 500


# Product Resource for managing products
class ProductResource(Resource):
    @jwt_required()
    def post(self):
        """Create a new product."""
        data = request.get_json()
        if not data or not all(key in data for key in ['name', 'price']):
            return error_response('Missing required fields', 400)

        try:
            product = Product(
                name=data['name'],
                price=data['price'],
                stock_quantity=data.get('stock_quantity', 0),
                min_stock_level=data.get('min_stock_level', 5)
            )
            db.session.add(product)
            db.session.commit()
            return jsonify({'message': 'Product created', 'product_id': product.id}), 201
        except Exception as e:
            logging.error(f"Error creating product: {str(e)}")
            db.session.rollback()
            return error_response('Internal server error', 500)

    @jwt_required()
    def get(self):
        """Fetch all products."""
        try:
            products = Product.query.all()
            return jsonify([
                {
                    'id': p.id,
                    'name': p.name,
                    'price': p.price,
                    'stock_quantity': p.stock_quantity
                } for p in products
            ]), 200
        except Exception as e:
            logging.error(f"Error fetching products: {str(e)}")
            return error_response('Internal server error', 500)


# Transaction Resource for managing transactions
class TransactionResource(Resource):
    @jwt_required()
    def post(self):
        """Create a new transaction."""
        data = request.get_json()
        if not data or not all(key in data for key in ['employee_id', 'total_amount']):
            return error_response('Missing required fields', 400)

        try:
            transaction = Transaction(
                employee_id=data['employee_id'],
                total_amount=data['total_amount'],
                discount=data.get('discount', 0)
            )
            db.session.add(transaction)
            db.session.commit()
            return jsonify({'message': 'Transaction created', 'transaction_id': transaction.id}), 201
        except Exception as e:
            logging.error(f"Error creating transaction: {str(e)}")
            db.session.rollback()
            return error_response('Internal server error', 500)

    @jwt_required()
    def get(self):
        """Fetch all transactions."""
        try:
            transactions = Transaction.query.all()
            return jsonify([
                {
                    'id': t.id,
                    'employee_id': t.employee_id,
                    'total_amount': t.total_amount
                } for t in transactions
            ]), 200
        except Exception as e:
            logging.error(f"Error fetching transactions: {str(e)}")
            return error_response('Internal server error', 500)


# Function to fetch M-Pesa token
def mpesaToken():
    """Fetch access token for M-Pesa API."""
    ckey = os.getenv('MPESA_CKEY')
    csecret = os.getenv('MPESA_CSECRET')
    apiurl = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    if not ckey or not csecret:
        logging.error("M-Pesa credentials are missing in environment variables.")
        return None

    try:
        r = requests.get(apiurl, auth=HTTPBasicAuth(ckey, csecret))
        r.raise_for_status()
        mptoken = r.json()
        return mptoken['access_token']
    except requests.exceptions.RequestException as e:
        logging.error(f"M-Pesa token request failed: {str(e)}")
        return None


# Function to process payment via M-Pesa
def lipaOnline(order):
    """Process payment via M-Pesa."""
    accesstoken = mpesaToken()
    if not accesstoken:
        return error_response('Failed to get M-Pesa token', 500)

    apiurl = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {accesstoken}"}

    request_body = {
        "BusinessShortCode": os.getenv('BUSINESS_SHORTCODE'),
        "Password": os.getenv('ENCODED_PASSWORD'),
        "Timestamp": os.getenv('TIMESTAMP'),
        "TransactionType": "CustomerPayBillOnline",
        "Amount": order.get_cart_total(),
        "PartyA": order.phone_number,
        "PartyB": os.getenv('BUSINESS_SHORTCODE'),
        "PhoneNumber": order.phone_number,
        "CallBackURL": "https://yourdomain.com/callback",
        "AccountReference": "HAC",
        "TransactionDesc": "testeltd"
    }

    try:
        response = requests.post(apiurl, json=request_body, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"M-Pesa payment request failed: {str(e)}")
        return error_response('Failed to process payment via M-Pesa', 500)


# Registering API resources
def init_api(api):
    """Register API resources."""
    api.add_resource(LoginResource, '/login')
    api.add_resource(LogoutResource, '/logout')
    api.add_resource(EmployeeResource, '/employees')
    api.add_resource(ProductResource, '/products')
    api.add_resource(TransactionResource, '/transactions')
