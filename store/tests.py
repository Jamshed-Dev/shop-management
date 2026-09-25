from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal
from store.models import (
    Collection, ProductType, Product, ProductVariant,
    Order, OrderItem, InventoryTransaction, OrderStatusLog
)
from store.services import OrderService, InventoryService, StatusService

User = get_user_model()

class StoreModelTests(TestCase):
    def setUp(self):
        self.collection = Collection.objects.create(title="Summer Collection")
        self.product_type = ProductType.objects.create(title="T-Shirt")

    def test_product_creation_and_slug_generation(self):
        product1 = Product.objects.create(
            collection=self.collection,
            product_type=self.product_type,
            title="Red Shirt",
            sku="RS-001",
            main_price=Decimal("19.99"),
            stock=10
        )
        self.assertEqual(product1.slug, "red-shirt")
        
        # Test duplicate slug rejection (generates unique slug)
        product2 = Product.objects.create(
            collection=self.collection,
            product_type=self.product_type,
            title="Red Shirt",
            sku="RS-002",
            main_price=Decimal("19.99"),
            stock=10
        )
        self.assertEqual(product2.slug, "red-shirt-1")

class OrderServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@example.com", password="password", full_name="Test User")
        self.collection = Collection.objects.create(title="Summer Collection")
        self.product_type = ProductType.objects.create(title="T-Shirt")
        self.product = Product.objects.create(
            collection=self.collection,
            product_type=self.product_type,
            title="Red Shirt",
            sku="RS-001",
            main_price=Decimal("20.00"),
            stock=10
        )

    def test_order_creation_and_totals(self):
        items_data = [
            {'product_id': self.product.id, 'quantity': 2}
        ]
        customer_data = {
            'customer_name': 'Test User',
            'customer_phone': '1234567890',
            'shipping_address': '123 Test St',
        }
        
        order = OrderService.create_order(
            user=self.user,
            items_data=items_data,
            customer_data=customer_data,
            payment_method='cod'
        )
        
        self.assertEqual(order.subtotal, Decimal("40.00"))
        self.assertEqual(order.total, Decimal("40.00"))
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 2)
        
        # Check that stock was NOT deducted yet
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

class InventoryServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="admin@example.com", password="password", full_name="Admin", is_staff=True)
        self.collection = Collection.objects.create(title="Summer Collection")
        self.product_type = ProductType.objects.create(title="T-Shirt")
        self.product = Product.objects.create(
            collection=self.collection,
            product_type=self.product_type,
            title="Red Shirt",
            sku="RS-001",
            main_price=Decimal("20.00"),
            stock=5
        )
        
        items_data = [{'product_id': self.product.id, 'quantity': 2}]
        customer_data = {
            'customer_name': 'Test User',
            'customer_phone': '1234567890',
            'shipping_address': '123 Test St',
        }
        self.order = OrderService.create_order(
            user=self.user, items_data=items_data, customer_data=customer_data, payment_method='cod'
        )

    def test_dispatch_order_deducts_stock(self):
        self.order.status = 'packed'
        self.order.save()
        
        order = InventoryService.dispatch_order(self.order, self.user)
        self.product.refresh_from_db()
        
        self.assertEqual(order.status, 'dispatched')
        self.assertEqual(self.product.stock, 3)
        
        # Check Inventory Transaction
        transaction = InventoryTransaction.objects.get(order=order)
        self.assertEqual(transaction.transaction_type, 'order_dispatch')
        self.assertEqual(transaction.quantity, -2)

    def test_dispatch_cannot_happen_twice(self):
        self.order.status = 'packed'
        self.order.save()
        
        InventoryService.dispatch_order(self.order, self.user)
        
        with self.assertRaises(ValidationError):
            InventoryService.dispatch_order(self.order, self.user)

    def test_insufficient_stock_prevents_dispatch(self):
        self.product.stock = 1
        self.product.save()
        
        self.order.status = 'packed'
        self.order.save()
        
        with self.assertRaises(ValidationError):
            InventoryService.dispatch_order(self.order, self.user)

    def test_return_adds_stock(self):
        self.order.status = 'packed'
        self.order.save()
        InventoryService.dispatch_order(self.order, self.user)
        
        self.order.status = 'delivered'
        self.order.save()
        
        order_item = self.order.items.first()
        returns_data = [{'order_item_id': order_item.id, 'quantity': 2}]
        
        InventoryService.return_order_items(self.order, returns_data, self.user)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5) # Back to 5
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'returned')

    def test_partial_return(self):
        self.order.status = 'packed'
        self.order.save()
        InventoryService.dispatch_order(self.order, self.user)
        
        self.order.status = 'delivered'
        self.order.save()
        
        order_item = self.order.items.first()
        returns_data = [{'order_item_id': order_item.id, 'quantity': 1}]
        
        InventoryService.return_order_items(self.order, returns_data, self.user)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 4) # 3 + 1
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'partially_returned')

    def test_return_cannot_exceed_dispatched(self):
        self.order.status = 'packed'
        self.order.save()
        InventoryService.dispatch_order(self.order, self.user)
        
        self.order.status = 'delivered'
        self.order.save()
        
        order_item = self.order.items.first()
        returns_data = [{'order_item_id': order_item.id, 'quantity': 3}] # Only 2 dispatched
        
        with self.assertRaises(ValidationError):
            InventoryService.return_order_items(self.order, returns_data, self.user)

class StatusServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="admin@example.com", password="password", full_name="Admin", is_staff=True)
        self.order = Order.objects.create(
            user=self.user, customer_name="Test", customer_phone="123", shipping_address="123", status="pending"
        )
        
    def test_invalid_status_transition_rejected(self):
        with self.assertRaises(ValidationError):
            StatusService.change_status(self.order, 'delivered', self.user)
            
    def test_valid_status_transition(self):
        order = StatusService.change_status(self.order, 'confirmed', self.user)
        self.assertEqual(order.status, 'confirmed')
        self.assertEqual(OrderStatusLog.objects.filter(order=order).count(), 1)
