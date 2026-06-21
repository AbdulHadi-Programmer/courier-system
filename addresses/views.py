from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .models import Address
from .forms import AddressForm


@login_required
def address_list(request):
    """Show from and to addresses in tabs with inline add form."""
    tab = request.GET.get('tab', 'from')
    show_form = False

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            addr = form.save(commit=False)
            addr.user = request.user
            addr.save()
            messages.success(request, f'{addr.get_address_type_display()} saved successfully.')
            return redirect(f'/addresses/?tab={addr.address_type}')
        else:
            show_form = True
            tab = request.POST.get('address_type', tab)
    else:
        form = AddressForm()

    from_addresses = Address.objects.filter(user=request.user, address_type='from')
    to_addresses = Address.objects.filter(user=request.user, address_type='to')

    return render(request, 'addresses/address_list.html', {
        'from_addresses': from_addresses,
        'to_addresses': to_addresses,
        'form': form,
        'tab': tab,
        'show_form': show_form,
    })


@login_required
def address_delete(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    addr_type = addr.address_type
    addr.delete()
    messages.success(request, 'Address deleted.')
    return redirect(f'/addresses/?tab={addr_type}')


@login_required
def address_api(request):
    """Return user's addresses as JSON for shipment form dropdowns."""
    addr_type = request.GET.get('type', 'from')
    addrs = Address.objects.filter(user=request.user, address_type=addr_type).values(
        'id', 'full_name', 'phone', 'city', 'address', 'label'
    )
    return JsonResponse(list(addrs), safe=False)
