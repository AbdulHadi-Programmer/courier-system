from django.db import models
from django.conf import settings


class Shipment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    PACKAGE_CHOICES = [
        ('document', 'Document'),
        ('parcel', 'Parcel'),
        ('fragile', 'Fragile'),
        ('bulk', 'Bulk'),
    ]
    SERVICE_CHOICES = [
        ('express', 'Express (1-2 Days)'),
        ('standard', 'Standard (3-5 Days)'),
        ('economy', 'Economy (5-7 Days)'),
    ]

    tracking_number = models.CharField(max_length=20, unique=True, editable=False)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shipments')

    sender_name = models.CharField(max_length=100)
    sender_phone = models.CharField(max_length=20)
    sender_address = models.TextField()
    sender_city = models.CharField(max_length=100)

    receiver_name = models.CharField(max_length=100)
    receiver_phone = models.CharField(max_length=20)
    receiver_address = models.TextField()
    receiver_city = models.CharField(max_length=100)

    weight = models.DecimalField(max_digits=8, decimal_places=2, help_text="Weight in KG")
    quantity = models.PositiveIntegerField(default=1, help_text="Number of items")
    package_type = models.CharField(max_length=10, choices=PACKAGE_CHOICES)
    service_type = models.CharField(max_length=10, choices=SERVICE_CHOICES)
    description = models.CharField(max_length=200, blank=True, help_text="Brief item description")

    price = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)
    estimated_delivery = models.DateField(null=True, blank=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tracking_number} - {self.receiver_name}"

    @property
    def status_percentage(self):
        status_map = {
            'pending': 0,
            'picked_up': 25,
            'in_transit': 50,
            'out_for_delivery': 75,
            'delivered': 100,
            'cancelled': 0,
            'returned': 0,
        }
        return status_map.get(self.status, 0)

    @property
    def next_status(self):
        flow = ['pending', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered']
        if self.status in flow and self.status != 'delivered':
            return flow[flow.index(self.status) + 1]
        return None

    @property
    def is_active(self):
        return self.status not in ('delivered', 'cancelled', 'returned')


class StatusUpdate(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='status_updates')
    status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES)
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.shipment.tracking_number} → {self.get_status_display()}"
