from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count, Q
from django.utils.timezone import now
from datetime import timedelta

from store.models import (
    Collection, ProductType, ProductChoice, ProductChoiceValue,
    Product, ProductImage, ProductVariant,
    Order, OrderItem, OrderStatusLog, InventoryTransaction
)
from store.serializers import (
    CollectionSerializer, ProductTypeSerializer,
    ProductChoiceSerializer, ProductChoiceValueSerializer,
    ProductListSerializer, ProductDetailSerializer,
    ProductImageSerializer, ProductVariantSerializer,
    OrderSerializer, OrderCreateSerializer, OrderUpdateSerializer, ReturnOrderSerializer,
    StatusChangeSerializer, InventoryTransactionSerializer
)
from store.services import OrderService, InventoryService, StatusService

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)

class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['title', 'slug']

class ProductTypeViewSet(viewsets.ModelViewSet):
    queryset = ProductType.objects.all()
    serializer_class = ProductTypeSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['title', 'slug']

class ProductChoiceViewSet(viewsets.ModelViewSet):
    queryset = ProductChoice.objects.all()
    serializer_class = ProductChoiceSerializer
    permission_classes = [IsAdminOrReadOnly]

class ProductChoiceValueViewSet(viewsets.ModelViewSet):
    queryset = ProductChoiceValue.objects.all()
    serializer_class = ProductChoiceValueSerializer
    permission_classes = [IsAdminOrReadOnly]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('collection', 'product_type')
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['collection', 'product_type', 'is_active', 'is_featured']
    search_fields = ['title', 'sku', 'description']
    ordering_fields = ['main_price', 'created_at', 'title']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs

class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']

class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'is_active']

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'payment_status']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone']
    ordering_fields = ['created_at', 'total']

    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.AllowAny()] # Or IsAuthenticated depending on guest checkout requirements
        if self.action in ['dispatch_order', 'return_order', 'change_status']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.prefetch_related('items', 'status_logs', 'items__product', 'items__variant').select_related('user')
        if user and user.is_staff:
            return qs
        if user and user.is_authenticated:
            return qs.filter(user=user)
        return Order.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            order = OrderService.create_order(
                user=request.user,
                items_data=serializer.validated_data['items'],
                customer_data={
                    'customer_name': serializer.validated_data['customer_name'],
                    'customer_phone': serializer.validated_data['customer_phone'],
                    'customer_email': serializer.validated_data.get('customer_email', ''),
                    'shipping_address': serializer.validated_data['shipping_address'],
                    'billing_address': serializer.validated_data.get('billing_address', ''),
                    'notes': serializer.validated_data.get('notes', '')
                },
                payment_method=serializer.validated_data['payment_method'],
                financials={
                    'discount': serializer.validated_data.get('discount', 0),
                    'shipping_cost': serializer.validated_data.get('shipping_cost', 0),
                    'tax': serializer.validated_data.get('tax', 0)
                }
            )
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = OrderUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            val_data = serializer.validated_data
            customer_data = {}
            for field in ['customer_name', 'customer_phone', 'customer_email', 'shipping_address', 'billing_address', 'notes']:
                if field in val_data:
                    customer_data[field] = val_data[field]
                    
            payment_data = {}
            for field in ['payment_method', 'payment_status']:
                if field in val_data:
                    payment_data[field] = val_data[field]
                    
            financials = {}
            for field in ['discount', 'shipping_cost', 'tax']:
                if field in val_data:
                    financials[field] = val_data[field]
            
            items_data = val_data.get('items', None)

            order = OrderService.update_order(
                order=order,
                user=request.user,
                items_data=items_data,
                customer_data=customer_data if customer_data else None,
                payment_data=payment_data if payment_data else None,
                financials=financials if financials else None
            )
            return Response(OrderSerializer(order).data)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def dispatch_order(self, request, pk=None):
        order = self.get_object()
        try:
            order = InventoryService.dispatch_order(order, request.user)
            return Response(OrderSerializer(order).data)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def return_order(self, request, pk=None):
        order = self.get_object()
        serializer = ReturnOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = InventoryService.return_order_items(
                order, 
                serializer.validated_data['items'], 
                request.user,
                serializer.validated_data.get('reason', '')
            )
            return Response(OrderSerializer(order).data)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        order = self.get_object()
        serializer = StatusChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = StatusService.change_status(
                order, 
                serializer.validated_data['status'], 
                request.user,
                serializer.validated_data.get('note', '')
            )
            return Response(OrderSerializer(order).data)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class InventoryTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryTransaction.objects.select_related('product', 'variant', 'order', 'created_by')
    serializer_class = InventoryTransactionSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['transaction_type', 'product', 'variant']
    ordering_fields = ['created_at']

class DashboardView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        orders = Order.objects.all()
        if start_date:
            orders = orders.filter(created_at__gte=start_date)
        if end_date:
            orders = orders.filter(created_at__lte=end_date)

        # Basic Stats
        overview = {
            'total_products': Product.objects.count(),
            'active_products': Product.objects.filter(is_active=True).count(),
            'total_collections': Collection.objects.count(),
            'total_orders': orders.count(),
        }

        # Order Statuses
        status_counts = orders.values('status').annotate(count=Count('id'))
        overview['order_statuses'] = {item['status']: item['count'] for item in status_counts}

        # Sales
        delivered_orders = orders.filter(status='delivered')
        sales = {
            'total_sales': delivered_orders.aggregate(Sum('total'))['total__sum'] or 0,
            'total_shipping': delivered_orders.aggregate(Sum('shipping_cost'))['shipping_cost__sum'] or 0,
        }

        # Low Stock Products
        # Filter products where stock is <= low_stock_threshold and active
        from django.db.models import F
        low_stock_qs = Product.objects.filter(is_active=True, stock__lte=F('low_stock_threshold')).order_by('stock')[:10]
        low_stock_products = ProductListSerializer(low_stock_qs, many=True).data

        # Top Selling Products (from delivered orders)
        top_products = []
        if delivered_orders.exists():
            top_selling = OrderItem.objects.filter(order__in=delivered_orders)\
                .values('product__id', 'product_title_snapshot', 'sku_snapshot')\
                .annotate(units_sold=Sum('quantity'), revenue=Sum('subtotal'))\
                .order_by('-units_sold')[:5]
            top_products = list(top_selling)

        # Sales Chart Data (Aggregate by Date for delivered orders)
        from django.db.models.functions import TruncDate
        chart_data_qs = delivered_orders.annotate(date=TruncDate('created_at'))\
            .values('date')\
            .annotate(daily_sales=Sum('total'))\
            .order_by('date')
        
        sales_chart = [
            {'date': item['date'].strftime('%Y-%m-%d'), 'sales': item['daily_sales']}
            for item in chart_data_qs
        ]

        return Response({
            'overview': overview,
            'sales': sales,
            'recent_orders': OrderSerializer(orders.order_by('-created_at')[:5], many=True).data,
            'low_stock_products': low_stock_products,
            'top_products': top_products,
            'sales_chart': sales_chart
        })
