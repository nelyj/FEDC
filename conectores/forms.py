from django import forms
from django.forms import ModelForm
from django.forms.widgets import PasswordInput

from .models import Conector


class FormConector(ModelForm):

    class Meta:
        model = Conector
        fields = ['url_erp','url_sii','usuario', 'password','time_cron']

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['usuario'].widget.attrs.update({'class': 'form-control'})
        self.fields['usuario'].required = True
        self.fields['usuario'].empty_label = 'Seleccione Usuario'
        self.fields['url_erp'].widget.attrs.update({'class': 'form-control','placeholder': 'Configurar Url del ERP'})
        self.fields['url_erp'].required = True
        self.fields['url_sii'].widget.attrs.update({'class': 'form-control','placeholder': 'Configurar Url del SII'})
        self.fields['url_sii'].required = True
        self.fields['password'].widget = PasswordInput()
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password'].required = True
        self.fields['time_cron'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Tiempo para enviar facturas al SII'})
        self.fields['time_cron'].required = True