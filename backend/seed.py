from api.app import create_app, db
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from api.models import (
    Employee, Category, Product, Customer,
    Transaction, SaleItem, InventoryTransaction,
    MpesaToken, AuditLog
)

app = create_app()

def seed_database():
    with app.app_context():
        # Clear existing data and create tables
        db.drop_all()
        db.create_all()
        
        print("🗑️ Cleared existing data!")
        print("🛠️ Creating tables...")

        # Seed Employees
        if Employee.query.count() == 0:
            employee1 = Employee(
                username='admin',
                email='admin@example.com',
                role='manager'
            )
            employee1.password = 'admin_password'  # Use password setter
            
            employee2 = Employee(
                username='cashier',
                email='cashier@example.com',
                role='cashier'
            )
            employee2.password = 'cashier_password'
            
            db.session.add_all([employee1, employee2])
            db.session.commit()

        # Seed Categories
        categories = [
            Category(name="Electronics"),
            Category(name="Groceries"),
            Category(name="Clothing"),
            Category(name="Home Appliances")
        ]
        db.session.add_all(categories)
        db.session.commit()  # Commit to get IDs

        # Seed Products with SKUs
        products = [
            Product(
                sku="ELEC-LP-001",
                name="Laptop",
                price=899.99,
                stock_quantity=15,
                min_stock_level=5,
                category_id=categories[0].id
            ),
            Product(
                sku="GROC-ML-002",
                name="Milk",
                price=3.99,
                stock_quantity=40,
                min_stock_level=20,
                category_id=categories[1].id
            ),
            Product(
                sku="CLOTH-TS-003",
                name="T-Shirt",
                price=19.99,
                stock_quantity=50,
                min_stock_level=30,
                category_id=categories[2].id
            ),
            Product(
                sku="HOME-BL-004",
                name="Blender",
                price=49.99,
                stock_quantity=10,
                min_stock_level=5,
                category_id=categories[3].id
            )
        ]
        db.session.add_all(products)
        db.session.commit()

        # Seed Customers
        customers = [
            Customer(
                name="John Doe",
                email="john@example.com",
                phone="555-1234"
            ),
            Customer(
                name="Jane Smith",
                email="jane@example.com",
                phone="555-5678"
            )
        ]
        db.session.add_all(customers)

        # Seed Transactions and Sale Items
        transaction1 = Transaction(
            employee_id=employee1.id,
            total_amount=899.99,
            discount=0.0
        )
        sale_item1 = SaleItem(
            product_id=products[0].id,
            quantity=1,
            price=899.99,
            transaction=transaction1
        )
        products[0].stock_quantity -= 1

        transaction2 = Transaction(
            employee_id=employee2.id,
            total_amount=(3.99 * 5) + 49.99 - 5.00,
            discount=5.00
        )
        sale_items2 = [
            SaleItem(
                product_id=products[1].id,
                quantity=5,
                price=3.99,
                transaction=transaction2
            ),
            SaleItem(
                product_id=products[3].id,
                quantity=1,
                price=49.99,
                transaction=transaction2
            )
        ]
        products[1].stock_quantity -= 5
        products[3].stock_quantity -= 1

        db.session.add_all([transaction1, transaction2, sale_item1] + sale_items2)

        # Seed Inventory Transactions
        inventory_transactions = [
            InventoryTransaction(
                product_id=products[0].id,
                change_quantity=15,
                transaction_type='add',
                reason="Initial stock"
            ),
            InventoryTransaction(
                product_id=products[1].id,
                change_quantity=40,
                transaction_type='add',
                reason="Weekly restock"
            ),
            InventoryTransaction(
                product_id=products[3].id,
                change_quantity=-1,
                transaction_type='remove',
                reason="Damaged item"
            )
        ]
        db.session.add_all(inventory_transactions)

        # Seed Audit Logs
        audit_logs = [
            AuditLog(
                user_id=employee1.id,
                action="System initialization"
            ),
            AuditLog(
                user_id=employee1.id,
                action="Processed daily sales report"
            )
        ]
        db.session.add_all(audit_logs)

        # Seed Mpesa Token
        mpesa_token = MpesaToken(
            access_token="dummy_access_token",
            expiration_time=datetime.utcnow() + timedelta(hours=1))
        db.session.add(mpesa_token)

        # Final commit
        db.session.commit()
        print("✅ Database seeded successfully!")

if __name__ == "__main__":
    seed_database()