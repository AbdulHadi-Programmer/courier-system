from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from shipments.models import Shipment
from accounts.models import User
from .services import get_dashboard_stats


@login_required
def dashboard_index(request):
    # Admin users go to admin dashboard
    if request.user.role == 'admin':
        return redirect('administration:dashboard')

    stats = get_dashboard_stats(user=request.user)

    if request.user.role == 'staff':
        recent_shipments = Shipment.objects.all()[:10]
        pending_shipments = Shipment.objects.filter(status='pending')[:5]
        active_shipments = Shipment.objects.exclude(
            status__in=['delivered', 'cancelled', 'returned']
        )[:10]
        total_customers = User.objects.filter(role='customer').count()
        return render(request, 'dashboard/staff_dashboard.html', {
            'stats': stats,
            'recent_shipments': recent_shipments,
            'pending_shipments': pending_shipments,
            'active_shipments': active_shipments,
            'total_customers': total_customers,
        })
    else:
        recent_shipments = Shipment.objects.filter(sender=request.user)[:10]
        active_shipments = Shipment.objects.filter(
            sender=request.user
        ).exclude(status__in=['delivered', 'cancelled', 'returned'])[:5]
        return render(request, 'dashboard/index.html', {
            'stats': stats,
            'recent_shipments': recent_shipments,
            'active_shipments': active_shipments,
        })
