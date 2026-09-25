from django.urls import path, include
from rest_framework_nested import routers
from .views import (
    CollectionViewSet, ProductTypeViewSet, ProductChoiceViewSet,
    ProductChoiceValueViewSet, ProductViewSet, ProductImageViewSet,
    ProductVariantViewSet, OrderViewSet, InventoryTransactionViewSet,
    DashboardView
)

router = routers.DefaultRouter()
router.register(r'collections', CollectionViewSet)
router.register(r'product-types', ProductTypeViewSet)
router.register(r'product-choices', ProductChoiceViewSet)
router.register(r'products', ProductViewSet, basename='products')
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'inventory-transactions', InventoryTransactionViewSet, basename='inventory')

# Nested Routers
# /collections/{id}/products/
collections_router = routers.NestedDefaultRouter(router, r'collections', lookup='collection')
collections_router.register(r'products', ProductViewSet, basename='collection-products')

# /product-types/{id}/products/
product_types_router = routers.NestedDefaultRouter(router, r'product-types', lookup='product_type')
product_types_router.register(r'products', ProductViewSet, basename='product-type-products')

# /product-choices/{id}/values/
product_choices_router = routers.NestedDefaultRouter(router, r'product-choices', lookup='choice')
product_choices_router.register(r'values', ProductChoiceValueViewSet, basename='product-choice-values')

# /products/{id}/images/
# /products/{id}/variants/
products_router = routers.NestedDefaultRouter(router, r'products', lookup='product')
products_router.register(r'images', ProductImageViewSet, basename='product-images')
products_router.register(r'variants', ProductVariantViewSet, basename='product-variants')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(collections_router.urls)),
    path('', include(product_types_router.urls)),
    path('', include(product_choices_router.urls)),
    path('', include(products_router.urls)),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
