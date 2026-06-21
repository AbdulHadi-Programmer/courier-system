from django.contrib.auth.models import AbstractUser
from django.db import models


def generate_account_number():
    """Generate sequential account number like ACC-00001."""
    last = User.objects.exclude(account_number__isnull=True).order_by('-account_number').first()
    if last and last.account_number and last.account_number.startswith('ACC-'):
        try:
            last_num = int(last.account_number.split('-')[1])
            return f"ACC-{str(last_num + 1).zfill(5)}"
        except (ValueError, IndexError):
            pass
    return 'ACC-00001'


class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    account_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = generate_account_number()
        super().save(*args, **kwargs)

    @property
    def is_staff_role(self):
        return self.role == 'staff'

    @property
    def is_admin_role(self):
        return self.role == 'admin'
