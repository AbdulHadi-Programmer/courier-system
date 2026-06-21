import logging
from decimal import Decimal
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.db.models import Sum, Count, Q
from django.utils import timezone

from accounts.models import User
from accounts.forms import AdminCreateUserForm
from shipments.models import Shipment, StatusUpdate

logger = logging.getLogger(__name__)


def admin_required(view_func):
    """Decorator: only allow admin role users."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'admin':
            messages.error(request, 'Access denied. Admin only.')
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_dashboard(request):
    """Main admin dashboard with full system overview."""
    total_users = User.objects.count()
    total_customers = User.objects.filter(role='customer').count()
    total_staff = User.objects.filter(role='staff').count()
    total_admins = User.objects.filter(role='admin').count()

    total_shipments = Shipment.objects.count()
    active_shipments = Shipment.objects.exclude(
        status__in=['delivered', 'cancelled', 'returned']
    ).count()
    delivered = Shipment.objects.filter(status='delivered').count()
    cancelled = Shipment.objects.filter(status='cancelled').count()
    returned = Shipment.objects.filter(status='returned').count()
    pending = Shipment.objects.filter(status='pending').count()

    revenue = Shipment.objects.filter(status='delivered').aggregate(
        total=Sum('price')
    )['total'] or Decimal('0.00')

    today = timezone.now().date()
    today_shipments = Shipment.objects.filter(created_at__date=today).count()
    today_revenue = Shipment.objects.filter(
        status='delivered', updated_at__date=today
    ).aggregate(total=Sum('price'))['total'] or Decimal('0.00')

    delivery_rate = round((delivered / total_shipments * 100), 1) if total_shipments > 0 else 0

    recent_shipments = Shipment.objects.all()[:8]
    recent_users = User.objects.order_by('-date_joined')[:5]

    # Status counts for breakdown
    status_counts = {}
    for val, label in Shipment.STATUS_CHOICES:
        status_counts[val] = Shipment.objects.filter(status=val).count()

    return render(request, 'administration/dashboard.html', {
        'total_users': total_users,
        'total_customers': total_customers,
        'total_staff': total_staff,
        'total_admins': total_admins,
        'total_shipments': total_shipments,
        'active_shipments': active_shipments,
        'delivered': delivered,
        'cancelled': cancelled,
        'returned': returned,
        'pending': pending,
        'revenue': revenue,
        'today_shipments': today_shipments,
        'today_revenue': today_revenue,
        'delivery_rate': delivery_rate,
        'recent_shipments': recent_shipments,
        'recent_users': recent_users,
        'status_counts': status_counts,
    })


@admin_required
def user_list(request):
    """List all users with filtering + inline create form."""
    show_form = False
    if request.method == 'POST':
        form = AdminCreateUserForm(request.POST)
        if form.is_valid():
            raw_password = form.cleaned_data['password1']
            user = form.save()

            # Send welcome email
            if user.email:
                try:
                    login_url = request.build_absolute_uri('/accounts/login/')
                    html_message = render_to_string('administration/email_welcome.html', {
                        'user': user,
                        'raw_password': raw_password,
                        'login_url': login_url,
                    })
                    plain_message = strip_tags(html_message)
                    send_mail(
                        subject=f'Welcome to QuickShip — Your {user.get_role_display()} Account',
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    messages.success(request, f'{user.get_role_display()} account "{user.username}" created and welcome email sent to {user.email}.')
                except Exception as e:
                    logger.error(f'Failed to send welcome email to {user.email}: {e}')
                    messages.success(request, f'{user.get_role_display()} account "{user.username}" created. Email could not be sent.')
            else:
                messages.success(request, f'{user.get_role_display()} account "{user.username}" created (no email provided).')

            return redirect('administration:user_list')
        else:
            show_form = True
    else:
        form = AdminCreateUserForm()

    role_filter = request.GET.get('role', 'customer')
    users = User.objects.filter(role=role_filter).order_by('-date_joined')

    search = request.GET.get('q', '').strip()
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    return render(request, 'administration/user_list.html', {
        'users': users,
        'current_role': role_filter,
        'search_query': search,
        'form': form,
        'show_form': show_form,
    })


@admin_required
def user_create(request):
    """Admin creates a new user with role assignment."""
    if request.method == 'POST':
        form = AdminCreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'{user.get_role_display()} account "{user.username}" created successfully.')
            return redirect('administration:user_list')
    else:
        form = AdminCreateUserForm()
    return render(request, 'administration/user_create.html', {'form': form})


@admin_required
def user_edit(request, pk):
    """Edit user role and details."""
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        new_role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'
        if new_role in ['customer', 'staff', 'admin']:
            user_obj.role = new_role
        user_obj.is_active = is_active
        user_obj.save()
        messages.success(request, f'User {user_obj.username} updated successfully.')
        return redirect('administration:user_list')
    return render(request, 'administration/user_edit.html', {'user_obj': user_obj})


@admin_required
def user_delete(request, pk):
    """Delete a user (not self)."""
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, 'You cannot delete yourself.')
        return redirect('administration:user_list')
    username = user_obj.username
    user_obj.delete()
    messages.success(request, f'User {username} has been deleted.')
    return redirect('administration:user_list')


@admin_required
def shipment_management(request):
    """View and manage all shipments."""
    shipments = Shipment.objects.all()

    status_filter = request.GET.get('status')
    if status_filter:
        shipments = shipments.filter(status=status_filter)

    search = request.GET.get('q', '').strip()
    if search:
        shipments = shipments.filter(
            Q(tracking_number__icontains=search) |
            Q(sender_name__icontains=search) |
            Q(receiver_name__icontains=search)
        )

    return render(request, 'administration/shipment_management.html', {
        'shipments': shipments,
        'current_status': status_filter,
        'search_query': search,
        'status_choices': Shipment.STATUS_CHOICES,
    })


@admin_required
def admin_delete_shipment(request, pk):
    """Admin can delete a shipment entirely."""
    shipment = get_object_or_404(Shipment, pk=pk)
    tracking = shipment.tracking_number
    shipment.delete()
    messages.success(request, f'Shipment {tracking} has been deleted.')
    return redirect('administration:shipment_management')
