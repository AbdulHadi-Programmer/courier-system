from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'account_number', 'email', 'first_name', 'last_name', 'role', 'city', 'is_active')
    list_filter = ('role', 'is_active', 'city')
    search_fields = ('username', 'account_number', 'email', 'first_name', 'last_name', 'phone')
    list_editable = ('role', 'is_active')
    readonly_fields = ('account_number', 'date_joined', 'last_login')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile', {'fields': ('role', 'account_number', 'phone', 'address', 'city')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Profile', {'fields': ('role', 'first_name', 'last_name', 'email', 'phone', 'city')}),
    )
