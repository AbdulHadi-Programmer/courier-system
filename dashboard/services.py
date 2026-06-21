from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from shipments.models import Shipment


def get_dashboard_stats(user=None):
    qs = Shipment.objects.all()
    if user and user.role == 'customer':
        qs = qs.filter(sender=user)

    total = qs.count()
    delivered = qs.filter(status='delivered').count()
    in_transit = qs.filter(status='in_transit').count()
    pending = qs.filter(status='pending').count()
    cancelled = qs.filter(status='cancelled').count()
    returned = qs.filter(status='returned').count()
    picked_up = qs.filter(status='picked_up').count()
    out_for_delivery = qs.filter(status='out_for_delivery').count()
    active = qs.exclude(status__in=['delivered', 'cancelled', 'returned']).count()

    revenue = qs.filter(status='delivered').aggregate(total=Sum('price'))['total'] or Decimal('0.00')
    delivery_rate = round((delivered / total * 100), 1) if total > 0 else 0

    today = timezone.now().date()
    today_shipments = qs.filter(created_at__date=today).count()

    return {
        'total_shipments': total,
        'delivered': delivered,
        'in_transit': in_transit,
        'pending': pending,
        'cancelled': cancelled,
        'returned': returned,
        'picked_up': picked_up,
        'out_for_delivery': out_for_delivery,
        'active': active,
        'revenue': revenue,
        'delivery_rate': delivery_rate,
        'today_shipments': today_shipments,
    }
