from django.template.loader import render_to_string
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.mixins import  RetrieveModelMixin, UpdateModelMixin, ListModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from auth_app.models import BlockJWT
from .models import User,PasswordResetToken,EmailVerificationToken
import random
from . import serializers
from . import models
from rest_framework.response import Response
from django.conf import settings

class UserProfileViewSet(
                   RetrieveModelMixin,
                   UpdateModelMixin,
                   ListModelMixin,
                   GenericViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    # Retrieve the current user's details
    def list(self, request):
        user = request.user
        serializer = self.get_serializer(user)  # Refactor to use the serializer class
        return Response(serializer.data)

    # Update the current user's details
    def partial_update(self, request, pk=None):
        user = request.user  # Get the logged-in user
        serializer = self.get_serializer(user, data=request.data, partial=True)  # Updated to use the serializer class
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Logout(APIView):
    serializer_class = serializers.LogoutSerializer
    def post(self,request,*args, **kwargs):
        access = request.data.get("access", None)
        refresh = request.data.get("refresh", None)
        if not access:
            return Response({"detail":"Please send access"},status=400)
        if not refresh:
            return Response({"detail":"Please send refresh"},status=400)
        b=BlockJWT()
        b.access=access
        b.refresh=refresh
        b.save()
        return Response({"detail":"Successfully Log out"})
    

class SendCodeView(APIView):
    permission_classes=[AllowAny]
    serializer_class=serializers.EmailSerializer
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User with this email does not exist."}, status=404)

        code = f"{random.randint(100000, 999999)}"  # Generate 6-digit code
        prt=PasswordResetToken.objects.create(user=user, code=code)

        html_message = render_to_string('reset_password_code.html', {
        'user': user,
        'code': code,
        'expire_time': 5,
    })
        # Send code via email
        send_mail(
            subject="Password Reset Code",
            message=f"Your password reset code is: {code}",
            html_message=html_message,
            from_email="no-reply@example.com",
            recipient_list=[email],
        )
        print(code)
        return Response({"detail": "Password reset code sent to your email.","token":prt.token,"email":prt.user.email})
    
class VerifyCodeView(APIView):
    permission_classes=[AllowAny]
    serializer_class=serializers.CodeVerificationSerializer
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        token = request.data.get('token')

        try:
            user = User.objects.get(email=email)
            reset_token = PasswordResetToken.objects.get(user=user, token=token, code=code)

            if reset_token.is_expired():
                return Response({"detail": "The reset Code has expired."}, status=status.HTTP_400_BAD_REQUEST)
            reset_token.code_confirmed=True
            reset_token.save()
            return Response({"detail": "Code verified."})

        except PasswordResetToken.DoesNotExist:
            return Response({"detail": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)
        

class ResetPasswordView(APIView):
    permission_classes=[AllowAny]
    serializer_class=serializers.PasswordResetSerializer
    def post(self, request):
        serializer =serializers. PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            # Save new password and delete the reset token
            serializer.save()
            return Response({"detail": "Password reset successfully."}, status=status.HTTP_200_OK)
        for key,value in serializer.errors.items():
            return Response({"detail":f"{key} : {value[0]}"},status=400)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class RegistrationStep1View(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.RegistrationStep1Serializer
    
    def post(self, request):
        serializer = serializers.RegistrationStep1Serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            # Generate verification code
            code = str(random.randint(100000, 999999))
            evt = EmailVerificationToken()
            evt.email = email
            evt.password = password
            evt.code = code
            evt.save()

            html_message = render_to_string('email_verification_code.html', {
                'code': code,
                'expire_time': 5,
            })

            # Send verification email
            send_mail(
                subject="Email Verification Code",
                message=f"Your Verification code is: {code}",
                html_message=html_message,
                from_email="no-reply@example.com",
                recipient_list=[email],
            )
            return Response({"detail": "Verification code sent to email.", "token": evt.token}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.VerifyEmailSerializer

    def post(self, request):
        serializer = serializers.VerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']
            token = serializer.validated_data['token']

            try:
                verification_token = EmailVerificationToken.objects.get(token=token)
                if verification_token.is_expired():
                    return Response({"detail": "Token has expired."}, status=status.HTTP_400_BAD_REQUEST)
                if verification_token.code != code:
                    return Response({"detail": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)

                # Step 2: Finalizing the registration after email verification
                verification_token.code_verified = True
                verification_token.save()

                # Create the user object
                user = User.objects.create_user(
                    email=verification_token.email,
                )
                user.set_password(verification_token.password)
                user.save()

                # Delete the token after successful registration
                verification_token.delete()

                return Response({"detail": "Registration complete."}, status=status.HTTP_201_CREATED)
            except EmailVerificationToken.DoesNotExist:
                return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
