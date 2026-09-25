from django.urls import path, include
from rest_framework_nested import routers
from . import views 

router = routers.DefaultRouter()
router.register("user-profile", views.UserProfileViewSet,basename="user-profile")


urlpatterns = [
    path('', include('djoser.urls.jwt')),
    path("jwt/logout/",views. Logout.as_view(), name='custom_logout'),
    path('password-reset/send-code/',views.SendCodeView.as_view(), name='send-code'),
    path('password-reset/verify-code/',views. VerifyCodeView.as_view(), name='verify-code'),
    path('password-reset/reset/',views. ResetPasswordView.as_view(), name='reset-password'),
    path('register/step1/', views. RegistrationStep1View.as_view(), name='register-step1'),
    path('register/verify-email/',views. VerifyEmailView.as_view(), name='verify-email'),
]

urlpatterns += router.urls + urlpatterns

