from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Shipment, StatusUpdate
from .forms import ShipmentForm
from .services import calculate_price, generate_tracking_number, calculate_eta, STATUS_LOCATIONS, STATUS_NOTES
from addresses.models import Address


def _is_privileged(user):
    """Check if user is staff or admin."""
    return user.role in ('staff', 'admin')


@login_required
def shipment_create(request):
    if request.user.role == 'admin':
        messages.error(request, 'This feature is only for customers.')
        return redirect('administration:dashboard')
    if request.user.role == 'staff':
        messages.error(request, 'This feature is only for customers.')
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = ShipmentForm(request.POST)
        if form.is_valid():
            shipment = form.save(commit=False)
            shipment.sender = request.user
            shipment.tracking_number = generate_tracking_number()
            shipment.price = calculate_price(
                shipment.weight, shipment.quantity,
                shipment.package_type, shipment.service_type
            )
            shipment.estimated_delivery = calculate_eta(shipment.service_type)
            shipment.save()
            StatusUpdate.objects.create(
                shipment=shipment,
                status='pending',
                location=shipment.sender_city,
                notes='Shipment created and is awaiting pickup.'
            )
            messages.success(
                request,
                f'Shipment created! Tracking Number: {shipment.tracking_number} | '
                f'Price: Rs. {shipment.price} | ETA: {shipment.estimated_delivery}'
            )
            return redirect('shipments:detail', pk=shipment.pk)
    else:
        form = ShipmentForm()

    from_addresses = Address.objects.filter(user=request.user, address_type='from')
    to_addresses = Address.objects.filter(user=request.user, address_type='to')
    return render(request, 'shipments/create.html', {
        'form': form,
        'from_addresses': from_addresses,
        'to_addresses': to_addresses,
        'no_from_addresses': not from_addresses.exists(),
        'no_to_addresses': not to_addresses.exists(),
    })


@login_required
def shipment_list(request):
    if _is_privileged(request.user):
        shipments = Shipment.objects.all()
    else:
        shipments = Shipment.objects.filter(sender=request.user)

    status_filter = request.GET.get('status')
    if status_filter:
        shipments = shipments.filter(status=status_filter)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        from django.db.models import Q
        shipments = shipments.filter(
            Q(tracking_number__icontains=search_query) |
            Q(receiver_name__icontains=search_query) |
            Q(sender_name__icontains=search_query) |
            Q(receiver_city__icontains=search_query) |
            Q(sender_city__icontains=search_query) |
            Q(receiver_phone__icontains=search_query)
        )

    return render(request, 'shipments/list.html', {
        'shipments': shipments,
        'current_filter': status_filter,
        'search_query': search_query,
        'status_choices': Shipment.STATUS_CHOICES,
    })


@login_required
def shipment_detail(request, pk):
    shipment = get_object_or_404(Shipment, pk=pk)
    if not _is_privileged(request.user) and shipment.sender != request.user:
        messages.error(request, 'You do not have permission to view this shipment.')
        return redirect('shipments:list')
    updates = shipment.status_updates.all()
    next_status_label = ''
    if shipment.next_status:
        next_status_label = dict(Shipment.STATUS_CHOICES).get(shipment.next_status, '')
    return render(request, 'shipments/detail.html', {
        'shipment': shipment,
        'updates': updates,
        'status_choices': Shipment.STATUS_CHOICES,
        'next_status_label': next_status_label,
    })


@login_required
def shipment_cancel(request, pk):
    shipment = get_object_or_404(Shipment, pk=pk)
    if shipment.sender != request.user and not _is_privileged(request.user):
        messages.error(request, 'Permission denied.')
        return redirect('shipments:list')
    # Customers can only cancel pending orders
    if not _is_privileged(request.user) and shipment.status != 'pending':
        messages.warning(request, 'You can only cancel orders that are still pending.')
        return redirect('shipments:detail', pk=pk)
    if shipment.status in ('delivered', 'cancelled', 'returned'):
        messages.warning(request, 'This shipment cannot be cancelled.')
        return redirect('shipments:detail', pk=pk)
    shipment.status = 'cancelled'
    shipment.save()
    StatusUpdate.objects.create(
        shipment=shipment, status='cancelled',
        location='-', notes='Shipment has been cancelled.'
    )
    messages.info(request, f'Shipment {shipment.tracking_number} has been cancelled.')
    return redirect('shipments:detail', pk=pk)


@login_required
def shipment_update_status(request, pk):
    """Staff/Admin: manually update shipment status."""
    if not _is_privileged(request.user):
        messages.error(request, 'Permission denied.')
        return redirect('shipments:list')

    shipment = get_object_or_404(Shipment, pk=pk)
    if not shipment.is_active:
        messages.warning(request, 'This shipment is no longer active and cannot be updated.')
        return redirect('shipments:detail', pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        note = request.POST.get('notes', '')
        allowed = [shipment.next_status, 'cancelled']
        if new_status in allowed and new_status != shipment.status:
            shipment.status = new_status
            shipment.save()
            StatusUpdate.objects.create(
                shipment=shipment,
                status=new_status,
                location=STATUS_LOCATIONS.get(new_status, ''),
                notes=note or STATUS_NOTES.get(new_status, ''),
            )
            messages.success(request, f'Status updated to: {shipment.get_status_display()}')
        else:
            messages.warning(request, 'Invalid status or no change.')
    return redirect('shipments:detail', pk=pk)


@login_required
def shipment_return(request, pk):
    """Mark a shipment as returned."""
    shipment = get_object_or_404(Shipment, pk=pk)
    if not _is_privileged(request.user) and shipment.sender != request.user:
        messages.error(request, 'Permission denied.')
        return redirect('shipments:list')
    if shipment.status in ('cancelled', 'returned', 'pending'):
        messages.warning(request, 'This shipment cannot be returned.')
        return redirect('shipments:detail', pk=pk)
    shipment.status = 'returned'
    shipment.save()
    StatusUpdate.objects.create(
        shipment=shipment, status='returned',
        location='Return Processing Center',
        notes='Package is being returned to sender.'
    )
    messages.info(request, f'Shipment {shipment.tracking_number} marked as returned.')
    return redirect('shipments:detail', pk=pk)
