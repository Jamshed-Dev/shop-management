from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import (
    Product, ProductVariant, Order, OrderItem, 
    OrderStatusLog, InventoryTransaction
)

class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(user, items_data, customer_data, payment_method, financials=None):
        """
        items_data format: [{'product_id': 1, 'variant_id': 2, 'quantity': 2}, ...]
        financials format: {'discount': 0, 'shipping_cost': 0, 'tax': 0}
        """
        if financials is None:
            financials = {}
            
        discount = Decimal(str(financials.get('discount', '0.00')))
        shipping_cost = Decimal(str(financials.get('shipping_cost', '0.00')))
        tax = Decimal(str(financials.get('tax', '0.00')))

        if discount < 0 or shipping_cost < 0 or tax < 0:
            raise ValidationError("Financial fields cannot be negative.")

        # Create Order first
        order = Order.objects.create(
            user=user if user and user.is_authenticated else None,
            payment_method=payment_method,
            status='pending',
            discount=discount,
            shipping_cost=shipping_cost,
            tax=tax,
            **customer_data
        )

        subtotal = Decimal('0.00')
        order_items = []

        for item_data in items_data:
            product_id = item_data.get('product_id')
            variant_id = item_data.get('variant_id')
            quantity = item_data.get('quantity', 1)

            if quantity <= 0:
                raise ValidationError("Quantity must be greater than zero.")

            # Validate Product
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                raise ValidationError(f"Product ID {product_id} is invalid or inactive.")

            # Validate Variant
            variant = None
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
                except ProductVariant.DoesNotExist:
                    raise ValidationError(f"Variant ID {variant_id} is invalid for this product.")

            # Calculate Price
            if variant and variant.price_override is not None:
                unit_price = variant.price_override
            else:
                unit_price = product.current_price

            sku = variant.sku if variant else product.sku
            title = f"{product.title} - {variant.sku}" if variant else product.title
            
            # Note: We do NOT deduct stock here. Stock is deducted upon dispatch.
            item_subtotal = unit_price * Decimal(str(quantity))
            subtotal += item_subtotal

            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    variant=variant,
                    product_title_snapshot=title,
                    sku_snapshot=sku,
                    unit_price=unit_price,
                    quantity=quantity,
                    subtotal=item_subtotal
                )
            )

        # Bulk create items
        OrderItem.objects.bulk_create(order_items)

        if discount > subtotal:
            raise ValidationError("Discount cannot exceed subtotal.")

        # Calculate final totals
        order.subtotal = subtotal
        order.total = subtotal + shipping_cost + tax - discount
        
        if order.total < 0:
            raise ValidationError("Order total cannot be negative.")
            
        order.save()

        # Log Status
        OrderStatusLog.objects.create(
            order=order,
            old_status='',
            new_status='pending',
            changed_by=user if user and user.is_authenticated else None,
            note="Order created."
        )

        return order

    @staticmethod
    @transaction.atomic
    def update_order(order, user, items_data=None, customer_data=None, payment_data=None, financials=None):
        """
        Updates an existing order. Handles rewriting OrderItems if items_data is provided.
        Only supports orders that have NOT been dispatched (otherwise stock logic is messy).
        """
        if order.status in ['dispatched', 'delivered', 'returned', 'partially_returned', 'cancelled']:
            # If the order is already dispatched or further, we should ideally restrict item editing
            # to avoid stock desync unless we build a complex adjustment system.
            # However, the user requested the ability to change shipping charge. 
            # We will allow updating customer_data and financials, but prevent item changes if dispatched.
            if items_data is not None:
                raise ValidationError(f"Cannot edit order items when status is {order.status}.")

        if customer_data:
            for key, value in customer_data.items():
                setattr(order, key, value)
        
        if payment_data:
            if 'payment_method' in payment_data:
                order.payment_method = payment_data['payment_method']
            if 'payment_status' in payment_data:
                order.payment_status = payment_data['payment_status']
                
        if financials:
            if 'discount' in financials:
                order.discount = Decimal(str(financials['discount']))
            if 'shipping_cost' in financials:
                order.shipping_cost = Decimal(str(financials['shipping_cost']))
            if 'tax' in financials:
                order.tax = Decimal(str(financials['tax']))

        # If items_data is provided and order is pre-dispatch, completely rewrite the items
        if items_data is not None and order.status in ['pending', 'confirmed', 'processing']:
            order.items.all().delete()
            subtotal = Decimal('0.00')
            order_items = []
            
            if len(items_data) == 0:
                raise ValidationError("Order must have at least one item.")

            for item_data in items_data:
                product_id = item_data.get('product_id')
                variant_id = item_data.get('variant_id')
                quantity = item_data.get('quantity', 1)

                if quantity <= 0:
                    raise ValidationError("Quantity must be greater than zero.")

                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    raise ValidationError(f"Product ID {product_id} is invalid.")

                variant = None
                if variant_id:
                    try:
                        variant = ProductVariant.objects.get(id=variant_id, product=product)
                    except ProductVariant.DoesNotExist:
                        raise ValidationError(f"Variant ID {variant_id} is invalid.")

                unit_price = Decimal(str(item_data.get('unit_price', variant.price_override if variant and variant.price_override else product.current_price)))
                
                sku = variant.sku if variant else product.sku
                title = f"{product.title} - {variant.sku}" if variant else product.title
                
                item_subtotal = unit_price * Decimal(str(quantity))
                subtotal += item_subtotal

                order_items.append(
                    OrderItem(
                        order=order,
                        product=product,
                        variant=variant,
                        product_title_snapshot=title,
                        sku_snapshot=sku,
                        unit_price=unit_price,
                        quantity=quantity,
                        subtotal=item_subtotal
                    )
                )

            OrderItem.objects.bulk_create(order_items)
            order.subtotal = subtotal

        if order.discount > order.subtotal:
            raise ValidationError("Discount cannot exceed subtotal.")

        order.total = order.subtotal + order.shipping_cost + order.tax - order.discount
        
        if order.total < 0:
            raise ValidationError("Order total cannot be negative.")

        order.save()
        return order

class InventoryService:
    @staticmethod
    @transaction.atomic
    def dispatch_order(order, user):
        """
        Changes order status to 'dispatched' and strictly deducts stock using select_for_update.
        """
        if order.status == 'dispatched':
            raise ValidationError("Order is already dispatched.")
        
        if order.status in ['cancelled', 'returned', 'return_requested', 'partially_returned']:
            raise ValidationError(f"Cannot dispatch order from status: {order.status}")

        order_items = order.items.all()

        for item in order_items:
            if item.variant:
                # Lock variant
                variant = ProductVariant.objects.select_for_update().get(id=item.variant.id)
                if variant.stock < item.quantity:
                    raise ValidationError(f"Insufficient stock for variant: {variant.sku}")
                
                stock_before = variant.stock
                variant.stock -= item.quantity
                variant.save()

                InventoryTransaction.objects.create(
                    product=item.product,
                    variant=variant,
                    transaction_type='order_dispatch',
                    quantity=-item.quantity,
                    stock_before=stock_before,
                    stock_after=variant.stock,
                    order=order,
                    order_item=item,
                    reason=f"Order {order.order_number} dispatched",
                    created_by=user if user.is_authenticated else None
                )
            elif item.product:
                # Lock product
                product = Product.objects.select_for_update().get(id=item.product.id)
                if product.stock < item.quantity:
                    raise ValidationError(f"Insufficient stock for product: {product.sku}")
                
                stock_before = product.stock
                product.stock -= item.quantity
                product.save()

                InventoryTransaction.objects.create(
                    product=product,
                    transaction_type='order_dispatch',
                    quantity=-item.quantity,
                    stock_before=stock_before,
                    stock_after=product.stock,
                    order=order,
                    order_item=item,
                    reason=f"Order {order.order_number} dispatched",
                    created_by=user if user.is_authenticated else None
                )

        old_status = order.status
        order.status = 'dispatched'
        order.save()

        OrderStatusLog.objects.create(
            order=order,
            old_status=old_status,
            new_status='dispatched',
            changed_by=user if user.is_authenticated else None,
            note="Order dispatched, stock deducted."
        )
        return order

    @staticmethod
    @transaction.atomic
    def return_order_items(order, returns_data, user, reason=""):
        """
        returns_data format: [{'order_item_id': 1, 'quantity': 2}]
        Restores stock for returned items and updates order status.
        """
        if order.status not in ['dispatched', 'delivered', 'partially_returned']:
            raise ValidationError("Order must be dispatched or delivered to be returned.")

        total_returned_in_this_request = 0
        
        for return_info in returns_data:
            item_id = return_info.get('order_item_id')
            return_quantity = return_info.get('quantity', 0)

            if return_quantity <= 0:
                continue
                
            # Lock order item
            item = OrderItem.objects.select_for_update().get(id=item_id, order=order)
            
            # Validate return quantity against dispatched quantity
            if item.returned_quantity + return_quantity > item.quantity:
                raise ValidationError(f"Cannot return {return_quantity} for item {item.id}. Only {item.quantity - item.returned_quantity} remaining.")

            # Update returned quantity on item
            item.returned_quantity += return_quantity
            item.save()
            total_returned_in_this_request += return_quantity

            # Restore Stock
            if item.variant:
                variant = ProductVariant.objects.select_for_update().get(id=item.variant.id)
                stock_before = variant.stock
                variant.stock += return_quantity
                variant.save()

                InventoryTransaction.objects.create(
                    product=item.product,
                    variant=variant,
                    transaction_type='return',
                    quantity=return_quantity,
                    stock_before=stock_before,
                    stock_after=variant.stock,
                    order=order,
                    order_item=item,
                    reason=reason or f"Return for order {order.order_number}",
                    created_by=user if user.is_authenticated else None
                )
            elif item.product:
                product = Product.objects.select_for_update().get(id=item.product.id)
                stock_before = product.stock
                product.stock += return_quantity
                product.save()

                InventoryTransaction.objects.create(
                    product=product,
                    transaction_type='return',
                    quantity=return_quantity,
                    stock_before=stock_before,
                    stock_after=product.stock,
                    order=order,
                    order_item=item,
                    reason=reason or f"Return for order {order.order_number}",
                    created_by=user if user.is_authenticated else None
                )

        if total_returned_in_this_request == 0:
            raise ValidationError("No valid quantities provided for return.")

        # Check if entire order is returned
        all_items_fully_returned = True
        for item in order.items.all():
            if item.returned_quantity < item.quantity:
                all_items_fully_returned = False
                break
        
        old_status = order.status
        new_status = 'returned' if all_items_fully_returned else 'partially_returned'
        
        order.status = new_status
        order.save()

        OrderStatusLog.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_status,
            changed_by=user if user.is_authenticated else None,
            note=reason or "Items returned and stock restored."
        )
        
        return order

class StatusService:
    @staticmethod
    @transaction.atomic
    def change_status(order, new_status, user, note=""):
        """
        Generic status change when special side-effects (like dispatch) are not needed.
        """
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['processing', 'cancelled'],
            'processing': ['dispatched', 'cancelled'],
            'dispatched': ['delivered', 'return_requested', 'returned'],
            'delivered': ['return_requested', 'returned'],
            'return_requested': ['returned', 'partially_returned', 'delivered'],
            'partially_returned': ['returned'],
            'returned': [],
            'cancelled': []
        }

        if new_status == 'dispatched':
            # Redirect to strict dispatch logic
            return InventoryService.dispatch_order(order, user)
            
        old_status = order.status
        if new_status not in valid_transitions.get(old_status, []):
             raise ValidationError(f"Invalid transition from {old_status} to {new_status}")

        order.status = new_status
        order.save()

        OrderStatusLog.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_status,
            changed_by=user if user and user.is_authenticated else None,
            note=note
        )
        return order
