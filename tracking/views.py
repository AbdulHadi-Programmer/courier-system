from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from shipments.models import Shipment, StatusUpdate
from shipments.services import STATUS_FLOW, STATUS_LOCATIONS, STATUS_NOTES


def track_shipment(request):
    shipment = None
    error = None
    tracking_number = ''
    if request.method == 'POST' or request.GET.get('tn'):
        tracking_number = (request.POST.get('tracking_number') or request.GET.get('tn', '')).strip()
        try:
            shipment = Shipment.objects.get(tracking_number=tracking_number)
        except Shipment.DoesNotExist:
            error = 'No shipment found with that tracking number.'
    return render(request, 'tracking/track.html', {
        'shipment': shipment,
        'error': error,
        'updates': shipment.status_updates.all() if shipment else [],
        'tracking_number': tracking_number,
    })


@login_required
def auto_progress(request, pk):
    """Staff/Admin only: Advance shipment to next status."""
    shipment = get_object_or_404(Shipment, pk=pk)
    if request.user.role not in ('staff', 'admin'):
        messages.error(request, 'Only staff can update shipment status.')
        return redirect('shipments:detail', pk=pk)

    next_status = shipment.next_status
    if not next_status:
        messages.warning(request, 'Shipment has already reached its final status.')
        return redirect('shipments:detail', pk=pk)

    shipment.status = next_status
    shipment.save()
    StatusUpdate.objects.create(
        shipment=shipment,
        status=next_status,
        location=STATUS_LOCATIONS.get(next_status, ''),
        notes=STATUS_NOTES.get(next_status, ''),
    )
    messages.success(request, f'Status updated to: {shipment.get_status_display()}')
    return redirect('shipments:detail', pk=pk)


@login_required
def auto_complete(request, pk):
    """Staff/Admin only: Progress shipment through ALL remaining stages."""
    shipment = get_object_or_404(Shipment, pk=pk)
    if request.user.role not in ('staff', 'admin'):
        messages.error(request, 'Only staff can update shipment status.')
        return redirect('shipments:detail', pk=pk)

    if shipment.status in ('delivered', 'cancelled', 'returned'):
        messages.warning(request, 'Shipment is already completed or cancelled.')
        return redirect('shipments:detail', pk=pk)

    current_idx = STATUS_FLOW.index(shipment.status)
    for status in STATUS_FLOW[current_idx + 1:]:
        shipment.status = status
        shipment.save()
        StatusUpdate.objects.create(
            shipment=shipment,
            status=status,
            location=STATUS_LOCATIONS.get(status, ''),
            notes=STATUS_NOTES.get(status, ''),
        )

    messages.success(request, f'Shipment {shipment.tracking_number} has been fully delivered!')
    return redirect('shipments:detail', pk=pk)
