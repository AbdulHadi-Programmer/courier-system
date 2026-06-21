from django import forms

from .models import Shipment


class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = [
            'sender_name', 'sender_phone', 'sender_address', 'sender_city',
            'receiver_name', 'receiver_phone', 'receiver_address', 'receiver_city',
            'weight', 'quantity', 'package_type', 'service_type', 'description',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Address fields are hidden — populated from saved addresses via JS
        address_fields = [
            'sender_name', 'sender_phone', 'sender_city', 'sender_address',
            'receiver_name', 'receiver_phone', 'receiver_city', 'receiver_address',
        ]
        for name in address_fields:
            self.fields[name].widget = forms.HiddenInput()

        # Visible fields
        for name in ('weight', 'quantity', 'description'):
            self.fields[name].widget.attrs.update({'class': 'form-control'})
        self.fields['package_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['service_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['description'].widget.attrs.update({'placeholder': 'e.g. Electronics, Clothing, Documents...'})
        self.fields['description'].required = False
