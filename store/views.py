from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from auth_app.authentication import JWTAuthentication

class JWTRequiredMixin:
    """
    Mixin to protect TemplateViews using the custom JWTAuthentication class.
    It reads from cookies or headers and validates the JWT.
    """
    def dispatch(self, request, *args, **kwargs):
        jwt_auth = JWTAuthentication()
        try:
            auth_result = jwt_auth.authenticate(request)
            if auth_result is not None:
                user, token = auth_result
                if user.is_staff or user.is_superuser:
                    request.user = user
                    return super().dispatch(request, *args, **kwargs)
        except (InvalidToken, AuthenticationFailed):
            pass
        
        # If we reach here, authentication failed or user is not staff
        login_url = reverse('frontend-login')
        next_url = request.path
        return redirect(f"{login_url}?next={next_url}")

# Frontend Template Views
class LoginView(TemplateView):
    template_name = 'login.html'
    
    def dispatch(self, request, *args, **kwargs):
        jwt_auth = JWTAuthentication()
        try:
            auth_result = jwt_auth.authenticate(request)
            if auth_result is not None:
                user, _ = auth_result
                if user.is_staff or user.is_superuser:
                    # Already authenticated, redirect to dashboard
                    return redirect('frontend-dashboard')
        except (InvalidToken, AuthenticationFailed):
            pass
        return super().dispatch(request, *args, **kwargs)

class ForgotPasswordView(TemplateView):
    template_name = 'forgot_password.html'

class VerifyCodeView(TemplateView):
    template_name = 'verify_code.html'

class ResetPasswordView(TemplateView):
    template_name = 'reset_password.html'

class DashboardView(JWTRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

class ProductListView(JWTRequiredMixin, TemplateView):
    template_name = 'products/list.html'

class ProductCreateView(JWTRequiredMixin, TemplateView):
    template_name = 'products/form.html'

class ProductEditView(JWTRequiredMixin, TemplateView):
    template_name = 'products/form.html'

class ProductDetailView(JWTRequiredMixin, TemplateView):
    template_name = 'products/detail.html'

class CollectionListView(JWTRequiredMixin, TemplateView):
    template_name = 'collections/list.html'

class CollectionCreateView(JWTRequiredMixin, TemplateView):
    template_name = 'collections/form.html'

class CollectionEditView(JWTRequiredMixin, TemplateView):
    template_name = 'collections/form.html'

class ProductTypeListView(JWTRequiredMixin, TemplateView):
    template_name = 'product_types/list.html'

class ProductTypeCreateView(JWTRequiredMixin, TemplateView):
    template_name = 'product_types/form.html'

class ProductTypeEditView(JWTRequiredMixin, TemplateView):
    template_name = 'product_types/form.html'

class ProductChoiceListView(JWTRequiredMixin, TemplateView):
    template_name = 'product_choices/list.html'

class OrderListView(JWTRequiredMixin, TemplateView):
    template_name = 'orders/list.html'

class OrderCreateView(JWTRequiredMixin, TemplateView):
    template_name = 'orders/form.html'

class OrderEditView(JWTRequiredMixin, TemplateView):
    template_name = 'orders/edit.html'

class OrderDetailView(JWTRequiredMixin, TemplateView):
    template_name = 'orders/detail.html'

class InventoryListView(JWTRequiredMixin, TemplateView):
    template_name = 'inventory/list.html'
