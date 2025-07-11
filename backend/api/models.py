from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import MetaData, Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship, validates
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import logging
import secrets
import random
from extensions import db


metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

class SalesReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_sales = db.Column(db.Float, nullable=False)
    transaction_count = db.Column(db.Integer, nullable=False)

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    critical_threshold = db.Column(db.Integer, nullable=False, default=5)
def generate_sample_data():
    if not SalesReport.query.first():
        for i in range(24):
            db.session.add(SalesReport(
                timestamp=datetime.now() - timedelta(hours=i),
                total_sales=random.uniform(500, 2000),
                transaction_count=random.randint(10, 50)
            ))
        db.session.commit()

    if not Inventory.query.first():
        for i in range(50):
            db.session.add(Inventory(
                product_name=f'Product {i+1}',
                stock=random.randint(0, 100),
                critical_threshold=random.randint(3, 10)
            ))
        db.session.commit()
class RoleEnum(db.TypeDecorator):
    impl = db.String(20)
    def process_bind_param(self, value, dialect):
        return value if value in ['cashier', 'manager'] else 'cashier'

class TransactionTypeEnum(db.TypeDecorator):
    impl = db.String(10)
    def process_bind_param(self, value, dialect):
        return value if value in ['add', 'remove'] else 'add'


class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.Enum('cashier', 'manager', name='role_enum'), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    salt = db.Column(db.String(32), nullable=False)  # Ensure this column exists
    verified = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    transactions = db.relationship('Transaction', back_populates='employee', lazy=True)
    audit_logs = db.relationship('AuditLog', back_populates='employee', lazy=True)

    def __repr__(self):
        return f"<Employee {self.username}>"

    # Password handling
    @property
    def password(self):
        raise AttributeError("Password is not readable")

    @password.setter
    def password(self, password):
        self.salt = secrets.token_hex(16)  # Generate salt
        self.password_hash = generate_password_hash(
            f"{password}{self.salt}",  # Salted password
            method='pbkdf2:sha256:100000'
        )

    def verify_password(self, password):
        return check_password_hash(self.password_hash, f"{password}{self.salt}")

    @staticmethod
    def find_by_username_or_email(username, email):
        return Employee.query.filter(
            (Employee.username == username) | (Employee.email == email)
        ).first()

class Transaction(db.Model):
    __tablename__ = 'transactions'  # Changed to plural for consistency

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    discount = db.Column(db.Float, default=0.0)
    payment_method = Column(Enum('cash', 'mpesa', 'card'))
    
    employee = db.relationship('Employee', back_populates='transactions')
    sale_items = db.relationship('SaleItem', back_populates='transaction', cascade='all, delete-orphan')
    

    def __repr__(self):
        return f"<Transaction {self.id} - {self.total_amount}>"  

class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    transaction = db.relationship('Transaction', back_populates='sale_items')
    product = db.relationship('Product')

    def __repr__(self):
        return f"<SaleItem {self.product.name} - {self.quantity}>"




class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    products = db.relationship('Product', back_populates='category', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Category {self.name}>"

# 1. Define InventoryTransaction first
class InventoryTransaction(db.Model):
    __tablename__ = 'inventory_transactions'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    change_quantity = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.Enum('add', 'remove', name='transaction_type_enum'), nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationship back to Product (using backref)
    # No need for separate relationship definition here if using backref

    def __repr__(self):
        return f"<InventoryTransaction {self.id}>"

# 2. Define SaleTransaction BEFORE Product
class SaleTransaction(db.Model):
    __tablename__ = 'sales_transactions'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity_sold = db.Column(db.Integer, nullable=False)
    sale_time = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationship to Product
    product = db.relationship('Product', backref='sales_transactions')

    def __repr__(self):
        return f"<SaleTransaction {self.id}>"

# 3. Now define Product
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=5)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "price": self.price,
            "stock_quantity": self.stock_quantity,
            "min_stock_level": self.min_stock_level,
            "category_id": self.category_id
        }
    
    # Relationships
    category = db.relationship('Category', back_populates='products')
    
    # Inventory transactions (using backref)
    inventory_transactions = db.relationship(
        'InventoryTransaction',
        backref='product',  # Creates backref to Product from InventoryTransaction
        lazy=True
    )

    # Sales transactions are handled by SaleTransaction's backref

    def __repr__(self):
        return f"<Product {self.name}>"

    # Keep your inventory monitoring methods
    @staticmethod
    def get_reorder_alerts():
        return Product.query.filter(Product.stock_quantity <= Product.min_stock_level).all()

    @staticmethod
    def monitor_inventory():
        products = Product.query.all()
        critical_stock = [p for p in products if p.stock_quantity <= p.min_stock_level]
        return {
            "total_products": len(products),
            "critical_stock": len(critical_stock),
            "critical_items": critical_stock
        }


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<Customer {self.id}: {self.name}, {self.email}, {self.phone}>"
  


class MpesaToken(db.Model):
    __tablename__ = 'mpesa_tokens'

    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String(255), nullable=False)
    expiration_time = db.Column(db.DateTime, nullable=False)

    def is_expired(self):
        return datetime.utcnow() > self.expiration_time

    def refresh(self, new_token, new_expiration_time):
        self.access_token = new_token
        self.expiration_time = new_expiration_time
        db.session.commit()



class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    employee = db.relationship('Employee', back_populates='audit_logs')  # Fixed missing relationship
    details = Column(db.JSON)

    def __repr__(self):
        return f"<AuditLog {self.id} - {self.action}>"



def log_db_error(e):
    logging.error(f"Database error: {str(e)}")
