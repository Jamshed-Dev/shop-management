from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import User, BlockJWT, PasswordResetToken, EmailVerificationToken


class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'full_name', 'phone_number', 'gender')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class CustomUserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label="Password",
        help_text="Raw passwords are not stored, so there is no way to see this user’s password."
    )

    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    ordering = ('email',)
    list_display = ('email', 'full_name', 'phone_number', 'gender', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'gender', 'date_joined')
    search_fields = ('email', 'full_name', 'phone_number')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone_number', 'gender')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'phone_number', 'gender', 'password'),
        }),
    )


@admin.register(BlockJWT)
class BlockJWTAdmin(admin.ModelAdmin):
    list_display = ('access_snippet', 'expired', 'created_at')
    search_fields = ('access', 'refresh')
    readonly_fields = ('access', 'refresh', 'expired', 'created_at')

    def access_snippet(self, obj):
        return obj.access[:30] + '...' if len(obj.access) > 30 else obj.access
    access_snippet.short_description = "Access Token"


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'token', 'code_confirmed', 'created_at', 'expired_at', 'is_expired_display')
    search_fields = ('user__email', 'user__full_name', 'code', 'token')
    list_filter = ('code_confirmed', 'created_at')
    readonly_fields = ('token', 'created_at', 'expired_at')

    def is_expired_display(self, obj):
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = "Expired?"


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'token', 'code_verified', 'created_at', 'expired_at', 'is_expired_display')
    search_fields = ('email', 'code', 'token')
    list_filter = ('code_verified', 'created_at')
    readonly_fields = ('token', 'created_at', 'expired_at')

    def is_expired_display(self, obj):
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = "Expired?"

