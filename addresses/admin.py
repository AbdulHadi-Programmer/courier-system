from django.contrib import admin
from .models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'address_type', 'city', 'phone', 'label', 'user', 'created_at')
    list_filter = ('address_type', 'city')
    search_fields = ('full_name', 'city', 'phone', 'user__username')
