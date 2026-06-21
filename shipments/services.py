import random
import string
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone


# --- AUTO: Price Calculation ---
BASE_PRICE = Decimal('50.00')
WEIGHT_RATE = Decimal('20.00')      # per KG
QUANTITY_RATE = Decimal('10.00')    # per extra item

PACKAGE_MULTIPLIER = {
    'document': Decimal('1.0'),
    'parcel': Decimal('1.2'),
    'fragile': Decimal('1.5'),
    'bulk': Decimal('1.8'),
}
SERVICE_MULTIPLIER = {
    'express': Decimal('2.0'),
    'standard': Decimal('1.0'),
    'economy': Decimal('0.7'),
}


def calculate_price(weight, quantity, package_type, service_type):
    weight_cost = Decimal(str(weight)) * WEIGHT_RATE
    quantity_cost = Decimal(str(max(quantity - 1, 0))) * QUANTITY_RATE
    pkg_mult = PACKAGE_MULTIPLIER.get(package_type, Decimal('1.0'))
    svc_mult = SERVICE_MULTIPLIER.get(service_type, Decimal('1.0'))
    total = (BASE_PRICE + weight_cost + quantity_cost) * pkg_mult * svc_mult
    return total.quantize(Decimal('0.01'))


# --- AUTO: Tracking Number Generation ---
def generate_tracking_number():
    random_part = ''.join(random.choices(string.digits, k=12))
    return f"TRK{random_part}"


# --- AUTO: ETA Calculation ---
SERVICE_DAYS = {
    'express': (1, 2),
    'standard': (3, 5),
    'economy': (5, 7),
}


def calculate_eta(service_type):
    min_days, max_days = SERVICE_DAYS.get(service_type, (3, 5))
    avg_days = (min_days + max_days) // 2
    return timezone.now().date() + timedelta(days=avg_days)


# --- AUTO: Status Progression ---
STATUS_FLOW = ['pending', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered']

STATUS_LOCATIONS = {
    'picked_up': 'Local Collection Hub',
    'in_transit': 'Regional Sorting Facility',
    'out_for_delivery': 'Destination Distribution Center',
    'delivered': 'Delivered to Recipient',
    'cancelled': '-',
    'returned': 'Return Processing Center',
}

STATUS_NOTES = {
    'picked_up': 'Package has been picked up from sender.',
    'in_transit': 'Package is in transit to the destination city.',
    'out_for_delivery': 'Package is out for delivery to the recipient.',
    'delivered': 'Package has been successfully delivered.',
    'cancelled': 'Shipment has been cancelled.',
    'returned': 'Package is being returned to sender.',
}
