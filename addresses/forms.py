from django import forms
from .models import Address


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('address_type', 'full_name', 'phone', 'city', 'address', 'label')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'address_type':
                field.widget = forms.Select(attrs={'class': 'form-select'}, choices=Address.TYPE_CHOICES)
            elif name == 'address':
                field.widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
            else:
                field.widget.attrs.update({'class': 'form-control'})
        self.fields['label'].widget.attrs['placeholder'] = 'e.g. Home, Office'
