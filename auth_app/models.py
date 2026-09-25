from django.db import models
from django.contrib.auth.models import AbstractUser,Permission,GroupManager,UserManager,AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.timezone import now
from datetime import timedelta
import uuid


from django.contrib.auth.hashers import (
    make_password,
)

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, unique=False, null=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Others', 'Others')])
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        # Automatically hash the password if not already hashed
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.full_name
    
class BlockJWT(models.Model):
    access = models.TextField(unique=True)
    refresh = models.TextField()
    expired = models.DateTimeField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.access
    
    
class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    code = models.CharField(max_length=6)  # 6-digit numeric code
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # Unique token
    code_confirmed=models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField()

    def is_expired(self):
        """Check if the token is expired."""
        return now() > self.expired_at

    def save(self, *args, **kwargs):
        """Automatically set the expiration time on save."""
        if not self.expired_at:
            self.expired_at = now() + timedelta(minutes=5)  # Token expires in 5 minutes
        super().save(*args, **kwargs)

    
class EmailVerificationToken(models.Model):
    email = models.EmailField(unique=False)
    password = models.CharField(max_length=255)
    code = models.CharField(max_length=6)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField()
    code_verified= models.BooleanField(default=False)
    
    def is_expired(self):
        return now() > self.expired_at
    
    def save(self, *args, **kwargs):
        if not self.expired_at:
            self.expired_at = now() + timedelta(minutes=5)
        super().save(*args, **kwargs)
    
