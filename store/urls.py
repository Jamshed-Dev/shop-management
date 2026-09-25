from django.urls import path, include
from . import views

urlpatterns = [
    path('api/', include('store.api.urls')),
    
    # Frontend Routes
    path('', views.HomeView.as_view(), name='frontend-home'),
    path('login/', views.LoginView.as_view(), name='frontend-login'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='frontend-forgot-password'),
    path('verify-code/', views.VerifyCodeView.as_view(), name='frontend-verify-code'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='frontend-reset-password'),
    path('dashboard/', views.DashboardView.as_view(), name='frontend-dashboard'),
    
    path('products/', views.ProductListView.as_view(), name='frontend-product-list'),
    path('products/create/', views.ProductCreateView.as_view(), name='frontend-product-create'),
    path('products/<int:id>/', views.ProductDetailView.as_view(), name='frontend-product-detail'),
    path('products/<int:id>/edit/', views.ProductEditView.as_view(), name='frontend-product-edit'),
    
    path('collections/', views.CollectionListView.as_view(), name='frontend-collection-list'),
    path('collections/create/', views.CollectionCreateView.as_view(), name='frontend-collection-create'),
    path('collections/<int:id>/edit/', views.CollectionEditView.as_view(), name='frontend-collection-edit'),
    
    path('product-types/', views.ProductTypeListView.as_view(), name='frontend-product-type-list'),
    path('product-types/create/', views.ProductTypeCreateView.as_view(), name='frontend-product-type-create'),
    path('product-types/<int:id>/edit/', views.ProductTypeEditView.as_view(), name='frontend-product-type-edit'),
    
    path('product-choices/', views.ProductChoiceListView.as_view(), name='frontend-product-choice-list'),
    
    path('orders/', views.OrderListView.as_view(), name='frontend-order-list'),
    path('orders/create/', views.OrderCreateView.as_view(), name='frontend-order-create'),
    path('orders/<int:id>/', views.OrderDetailView.as_view(), name='frontend-order-detail'),
    path('orders/<int:id>/edit/', views.OrderEditView.as_view(), name='frontend-order-edit'),
    
    path('inventory/', views.InventoryListView.as_view(), name='frontend-inventory-list'),
]
