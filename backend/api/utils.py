# # utils.py where i have stored the functions that are used in the app
# import logging
# import os
# import requests
# from requests.auth import HTTPBasicAuth
# from datetime import datetime, timedelta
from models import db,MpesaToken,Product,Transaction,InventoryTransaction,Employee,SaleItem,AuditLog
# --------------- utils.py ---------------
import logging
import os
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from sqlalchemy import asc, desc

# Logging Configuration
logging.basicConfig(level=logging.INFO)

# ------------------- DSA Algorithms -------------------
def binary_search(sorted_list, target, key=lambda x: x):
    """Binary search implementation for POS operations."""
    low = 0
    high = len(sorted_list) - 1
    while low <= high:
        mid = (low + high) // 2
        mid_val = key(sorted_list[mid])
        if mid_val == target:
            return sorted_list[mid]
        elif mid_val < target:
            low = mid + 1
        else:
            high = mid - 1
    return None

def quicksort(arr, key=lambda x: x):
    """Quicksort implementation for efficient sorting."""
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if key(x) < key(pivot)]
    middle = [x for x in arr if key(x) == key(pivot)]
    right = [x for x in arr if key(x) > key(pivot)]
    return quicksort(left, key) + middle + quicksort(right, key)

# ------------------- POS Utilities -------------------
def process_transaction(products, employee_id):
    """Process a transaction using optimized sorting and searching."""
    sorted_products = quicksort(products, key=lambda x: x.sku)
    total = sum(p.price for p in products)
    
    transaction = Transaction(
        employee_id=employee_id,
        total_amount=total,
        transaction_date=datetime.utcnow()
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    for product in products:
        product.stock_quantity -= 1
        db.session.add(SaleItem(
            transaction_id=transaction.id,
            product_id=product.id,
            quantity=1,
            price=product.price
        ))
    
    db.session.commit()
    return transaction

def find_product(sku):
    """Find product using binary search with sorted inventory."""
    products = quicksort(Product.query.all(), key=lambda x: x.sku)
    return binary_search(products, sku, key=lambda x: x.sku)

def generate_sales_report(start_date, end_date):
    """Generate sales report with optimized data processing."""
    transactions = Transaction.query.filter(
        Transaction.transaction_date.between(start_date, end_date)
    ).all()
    
    sorted_transactions = quicksort(transactions, key=lambda x: x.transaction_date)
    return {
        'total_sales': sum(t.total_amount for t in sorted_transactions),
        'transaction_count': len(sorted_transactions),
        'transactions': sorted_transactions
    }

# ------------------- Payment Processing -------------------
def fetch_mpesa_token():
    """Fetch and return M-Pesa access token."""
    try:
        ckey = os.getenv('MPESA_CKEY')
        csecret = os.getenv('MPESA_CSECRET')
        apiurl = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

        if not ckey or not csecret:
            logging.error("M-Pesa credentials are missing.")
            return None

        # Try to get an existing token from database first
        mpesa_token = MpesaToken.query.filter(MpesaToken.is_expired()).first()
        if mpesa_token:
            return mpesa_token.access_token  # Return the cached token

        # Fetch a new token if not found or expired
        response = requests.get(apiurl, auth=HTTPBasicAuth(ckey, csecret))
        response.raise_for_status()

        token_data = response.json()
        access_token = token_data['access_token']
        expires_in = token_data['expires_in']

        expiration_time = datetime.utcnow() + timedelta(seconds=expires_in)

        # Save the new token in the database
        new_token = MpesaToken(access_token=access_token, expiration_time=expiration_time)
        db.session.add(new_token)
        db.session.commit()

        return access_token
    except Exception as e:
        logging.error(f"Error fetching M-Pesa token: {str(e)}")
        return None

def make_api_request(url, method='GET', data=None, headers=None):
    """Helper function to handle external API requests."""
    try:
        response = requests.request(method, url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {str(e)}")
        return None
def process_mpesa_payment(phone, amount, reference):
    """Process MPesa payment integration."""
    token = fetch_mpesa_token()
    headers = {'Authorization': f'Bearer {token}'}
    data = {
        'BusinessShortCode': os.getenv('MPESA_SHORTCODE'),
        'Password': generate_mpesa_password(),
        'Timestamp': datetime.now().strftime('%Y%m%d%H%M%S'),
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': amount,
        'PartyA': phone,
        'PartyB': os.getenv('MPESA_SHORTCODE'),
        'PhoneNumber': phone,
        'CallBackURL': os.getenv('MPESA_CALLBACK'),
        'AccountReference': reference,
        'TransactionDesc': 'POS Payment'
    }
    return make_api_request(
        'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
        method='POST',
        data=data,
        headers=headers
    )

# ------------------- Helper Functions -------------------
def validate_inventory_levels():
    """Check inventory levels using efficient search."""
    products = quicksort(Product.query.all(), key=lambda x: x.stock_quantity)
    low_stock = [p for p in products if p.stock_quantity <= p.min_stock_level]
    return quicksort(low_stock, key=lambda x: x.name)

def restock_product(product_id, quantity):
    """Restock product with inventory tracking."""
    product = Product.query.get(product_id)
    product.stock_quantity += quantity
    db.session.add(InventoryTransaction(
        product_id=product_id,
        change_quantity=quantity,
        transaction_type='add',
        reason='Restock'
    ))
    db.session.commit()
    return product

def get_employee_performance(employee_id):
    """Calculate employee performance metrics."""
    employee = Employee.query.get(employee_id)
    transactions = Transaction.query.filter_by(employee_id=employee_id).all()
    sorted_transactions = quicksort(transactions, key=lambda x: x.transaction_date)
    return {
        'employee': employee,
        'total_sales': sum(t.total_amount for t in sorted_transactions),
        'transactions': sorted_transactions
    }