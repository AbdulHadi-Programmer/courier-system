from django.db import models
from django.conf import settings


class Address(models.Model):
    TYPE_CHOICES = [
        ('from', 'From Address (Sender)'),
        ('to', 'To Address (Receiver)'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=4, choices=TYPE_CHOICES)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    address = models.TextField()
    label = models.CharField(max_length=50, blank=True, help_text="e.g. Home, Office, Warehouse")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'addresses'

    def __str__(self):
        lbl = f" ({self.label})" if self.label else ""
        return f"{self.full_name} - {self.city}{lbl}"
