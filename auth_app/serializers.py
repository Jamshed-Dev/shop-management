from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.serializers import TokenRefreshSerializer as BaseRefreshSerializer
from rest_framework import serializers
from auth_app.models import BlockJWT
from typing import Any, Dict
from .models import User,PasswordResetToken,EmailVerificationToken
from rest_framework_simplejwt .settings import api_settings



class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "phone_number", "gender", "is_staff"]
        read_only_fields = ["id", "email", "is_staff"]

class TokenRefreshSerializer (BaseRefreshSerializer):
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        refresh_token=attrs["refresh"]
        print(refresh_token)
        if BlockJWT.objects.filter(refresh=refresh_token).exists():
            return {}
        refresh = self.token_class(attrs["refresh"])

        data = {"access": str(refresh.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass

            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()

            data["refresh"] = str(refresh)

        return data


class LogoutSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    

class CodeVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    token = serializers.UUIDField()

    def validate(self, data):
        email = data.get('email')
        code = data.get('code')
        token = data.get('token')

        # Check if token exists and is valid
        try:
            user = User.objects.get(email=email)
            reset_token = PasswordResetToken.objects.get(user=user, token=token, code=code)

            if reset_token.is_expired():
                raise serializers.ValidationError("The reset token has expired.")

        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token or code.")

        return data
    

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    token = serializers.UUIDField()

    def validate(self, data):
        email = data.get('email')
        code = data.get('code')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        token = data.get('token')

        if new_password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")
        try:

        # Check if token exists and is valid
            user = User.objects.get(email=email)
            reset_token = PasswordResetToken.objects.get(user=user, token=token, code=code)

            if not reset_token.code_confirmed:
                raise serializers.ValidationError("The code has not verified.")

        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid code.")

        return data

    def save(self):
        email = self.validated_data['email']
        code = self.validated_data['code']
        new_password = self.validated_data['new_password']
        token = self.validated_data['token']

        try:
            user = User.objects.get(email=email)
            reset_token = PasswordResetToken.objects.get(user=user, token=token, code=code)
            user.set_password(new_password)
            user.save()

            # Delete the token to prevent reuse
            reset_token.delete()

        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid code.")
        
        
class RegistrationStep1Serializer(serializers.Serializer):
    full_name = serializers.CharField(write_only = True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    terms_a_policy = serializers.BooleanField(default = False)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        return data

class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    token = serializers.UUIDField()

    def validate(self, data):
        code = data.get('code')
        token = data.get('token')

        try:
            verification_token = EmailVerificationToken.objects.get(token=token)
            if verification_token.is_expired():
                raise serializers.ValidationError("Token has expired.")
            if verification_token.code != code:
                raise serializers.ValidationError("Invalid code.")
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token.")
        
        return data
