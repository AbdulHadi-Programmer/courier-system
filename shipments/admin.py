from django.contrib import admin

from .models import Shipment, StatusUpdate
from .services import STATUS_LOCATIONS, STATUS_NOTES


class StatusUpdateInline(admin.TabularInline):
    model = StatusUpdate
    extra = 1
    readonly_fields = ('timestamp',)


def mark_picked_up(modeladmin, request, queryset):
    for s in queryset.filter(status='pending'):
        s.status = 'picked_up'
        s.save()
        StatusUpdate.objects.create(shipment=s, status='picked_up',
            location=STATUS_LOCATIONS['picked_up'], notes=STATUS_NOTES['picked_up'])
mark_picked_up.short_description = "Mark as Picked Up"


def mark_in_transit(modeladmin, request, queryset):
    for s in queryset.filter(status='picked_up'):
        s.status = 'in_transit'
        s.save()
        StatusUpdate.objects.create(shipment=s, status='in_transit',
            location=STATUS_LOCATIONS['in_transit'], notes=STATUS_NOTES['in_transit'])
mark_in_transit.short_description = "Mark as In Transit"


def mark_out_for_delivery(modeladmin, request, queryset):
    for s in queryset.filter(status='in_transit'):
        s.status = 'out_for_delivery'
        s.save()
        StatusUpdate.objects.create(shipment=s, status='out_for_delivery',
            location=STATUS_LOCATIONS['out_for_delivery'], notes=STATUS_NOTES['out_for_delivery'])
mark_out_for_delivery.short_description = "Mark as Out for Delivery"


def mark_delivered(modeladmin, request, queryset):
    for s in queryset.filter(status='out_for_delivery'):
        s.status = 'delivered'
        s.save()
        StatusUpdate.objects.create(shipment=s, status='delivered',
            location=STATUS_LOCATIONS['delivered'], notes=STATUS_NOTES['delivered'])
mark_delivered.short_description = "Mark as Delivered"


def mark_cancelled(modeladmin, request, queryset):
    for s in queryset.exclude(status__in=['delivered', 'cancelled', 'returned']):
        s.status = 'cancelled'
        s.save()
        StatusUpdate.objects.create(shipment=s, status='cancelled',
            location='-', notes=STATUS_NOTES['cancelled'])
mark_cancelled.short_description = "Mark as Cancelled"


def mark_returned(modeladmin, request, queryset):
    for s in queryset.filter(status='delivered'):
        s.status = 'returned'
        s.save()
        StatusUpdate.objects.create(shipment=s, status='returned',
            location=STATUS_LOCATIONS['returned'], notes=STATUS_NOTES['returned'])
mark_returned.short_description = "Mark as Returned"


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'sender', 'sender_city', 'receiver_name', 'receiver_city',
                    'service_type', 'quantity', 'status', 'price', 'estimated_delivery', 'created_at')
    list_filter = ('status', 'service_type', 'package_type', 'created_at')
    search_fields = ('tracking_number', 'sender_name', 'receiver_name', 'sender_city', 'receiver_city', 'description')
    readonly_fields = ('tracking_number', 'price', 'estimated_delivery', 'created_at', 'updated_at')
    list_editable = ('status',)
    date_hierarchy = 'created_at'
    inlines = [StatusUpdateInline]
    actions = [mark_picked_up, mark_in_transit, mark_out_for_delivery, mark_delivered, mark_cancelled, mark_returned]


@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'status', 'location', 'notes', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('shipment__tracking_number', 'location', 'notes')
    readonly_fields = ('timestamp',)
