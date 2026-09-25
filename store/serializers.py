from rest_framework import serializers
from .models import (
    Collection, ProductType, ProductChoice, ProductChoiceValue,
    Product, ProductImage, ProductVariant,
    Order, OrderItem, OrderStatusLog, InventoryTransaction
)
from auth_app.serializers import UserProfileSerializer as UserSerializer

class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = '__all__'
        read_only_fields = ('slug', 'created_at', 'updated_at')


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = '__all__'
        read_only_fields = ('slug', 'created_at', 'updated_at')


class ProductChoiceValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductChoiceValue
        fields = '__all__'
        read_only_fields = ('slug', 'created_at', 'updated_at')


class ProductChoiceSerializer(serializers.ModelSerializer):
    values = ProductChoiceValueSerializer(many=True, read_only=True)

    class Meta:
        model = ProductChoice
        fields = '__all__'
        read_only_fields = ('slug', 'created_at', 'updated_at')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'


class ProductVariantSerializer(serializers.ModelSerializer):
    choices_details = ProductChoiceValueSerializer(source='choices', many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class ProductListSerializer(serializers.ModelSerializer):
    collection_title = serializers.CharField(source='collection.title', read_only=True)
    product_type_title = serializers.CharField(source='product_type.title', read_only=True)
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'title', 'slug', 'sku', 'image_url', 'image', 'short_description',
            'main_price', 'new_price', 'current_price', 'stock', 
            'is_active', 'is_featured', 'collection_title', 'product_type_title'
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    collection = serializers.PrimaryKeyRelatedField(queryset=Collection.objects.all(), required=False, allow_null=True)
    product_type = serializers.PrimaryKeyRelatedField(queryset=ProductType.objects.all())
    
    collection_details = CollectionSerializer(source='collection', read_only=True)
    product_type_details = ProductTypeSerializer(source='product_type', read_only=True)
    
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('slug', 'created_at', 'updated_at')


class OrderItemProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'title', 'sku', 'image', 'image_url')

class OrderItemSerializer(serializers.ModelSerializer):
    product_detail = OrderItemProductSerializer(source='product', read_only=True)

    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ('subtotal', 'product_title_snapshot', 'sku_snapshot', 'returned_quantity')


class OrderStatusLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)

    class Meta:
        model = OrderStatusLog
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_logs = OrderStatusLogSerializer(many=True, read_only=True)
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('order_number', 'subtotal', 'total', 'created_at', 'updated_at')


class OrderCreateItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)


class OrderCreateSerializer(serializers.Serializer):
    items = OrderCreateItemSerializer(many=True)
    customer_name = serializers.CharField(max_length=255)
    customer_phone = serializers.CharField(max_length=50)
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    shipping_address = serializers.CharField()
    billing_address = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.CharField(max_length=100)
    notes = serializers.CharField(required=False, allow_blank=True)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, min_value=0)
    shipping_cost = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, min_value=0)
    tax = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, min_value=0)

class OrderUpdateSerializer(serializers.Serializer):
    items = OrderCreateItemSerializer(many=True, required=False)
    customer_name = serializers.CharField(max_length=255, required=False)
    customer_phone = serializers.CharField(max_length=50, required=False)
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    shipping_address = serializers.CharField(required=False)
    billing_address = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.CharField(max_length=100, required=False)
    payment_status = serializers.ChoiceField(choices=Order.PAYMENT_STATUS_CHOICES, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, min_value=0)
    shipping_cost = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, min_value=0)
    tax = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, min_value=0)




class ReturnItemSerializer(serializers.Serializer):
    order_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class ReturnOrderSerializer(serializers.Serializer):
    items = ReturnItemSerializer(many=True)
    reason = serializers.CharField(required=False, allow_blank=True)


class StatusChangeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True)


class InventoryTransactionSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    variant_sku = serializers.CharField(source='variant.sku', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)

    class Meta:
        model = InventoryTransaction
        fields = '__all__'
