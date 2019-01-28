from django import forms
from django.forms import ModelForm
from django.forms.widgets import PasswordInput

from .models import *


class FormConector(ModelForm):

    class Meta:
        model = Conector
        fields = ['url_erp','url_sii','usuario',
                  'password','time_cron', 'certificado', 'empresa','t_documento']

    def __init__(self, *args, **kwargs):

        self.request = kwargs.pop('request', None)

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
        self.fields['certificado'].widget.attrs.update({'class': 'form-control'})
        self.fields['t_documento'].widget.attrs.update({'class': 'form-control'})
        self.fields['empresa'].widget.attrs.update({'class': 'form-control'})
        if self.request:
            
            self.fields['empresa'].queryset = Compania.objects.filter(owner=self.request.user)

    def clean(self):
        cleaned_data = super(FormConector, self).clean()
        password = cleaned_data.get("password")
        space = password.count(' ')
        if space > 0:
            msg = "Error en password: no puede contener espacios en blanco" 
            self.add_error('password', msg)


class FormCompania(ModelForm):

    class Meta:
        model = Compania
        fields = ['rut','razon_social','actividad_principal', 'giro',
                'direccion','comuna','logo','fecha_resolucion','numero_resolucion',
                'correo_sii','pass_correo_sii','correo_intercambio','pass_correo_intercambio']

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['rut'].widget.attrs.update({'class': 'form-control','placeholder': 'RUT de la compañia'})
        self.fields['rut'].required = True
        self.fields['razon_social'].widget.attrs.update({'class': 'form-control','placeholder': 'Razón Social de la Compañia'})
        self.fields['razon_social'].required = True
        self.fields['actividad_principal'].widget.attrs.update({'class': 'form-control','placeholder': 'Actividad Principal'})
        self.fields['actividad_principal'].required = True
        self.fields['giro'].widget.attrs.update({'class': 'form-control','placeholder': 'Número de Giro'})
        self.fields['giro'].required = True
        self.fields['direccion'].widget.attrs.update({'class': 'form-control','placeholder': 'Dirección de la Compañia Facturadora'})
        self.fields['direccion'].required = True
        self.fields['comuna'].widget.attrs.update({'class': 'form-control','placeholder': 'Comuna donde se localiza la Comuna'})
        self.fields['comuna'].required = True
        self.fields['fecha_resolucion'].widget.attrs.update({'class': 'form-control datepicker', 'data-provide': 'datepicker','placeholder':'DD/MM/YYYY'})
        self.fields['fecha_resolucion'].required=True
        self.fields['numero_resolucion'].widget.attrs.update({'class': 'form-control'})
        self.fields['numero_resolucion'].required = True
        self.fields['pass_correo_sii'].widget = PasswordInput()
        self.fields['pass_correo_sii'].widget.attrs.update({'class': 'form-control'})
        self.fields['pass_correo_sii'].required = True
        self.fields['correo_sii'].widget.attrs.update({'class': 'form-control'})
        self.fields['correo_sii'].required = True
        self.fields['pass_correo_intercambio'].widget = PasswordInput()
        self.fields['pass_correo_intercambio'].widget.attrs.update({'class': 'form-control'})
        self.fields['pass_correo_intercambio'].required = True
        self.fields['correo_intercambio'].widget.attrs.update({'class': 'form-control'})
        self.fields['correo_intercambio'].required = True
        self.fields['logo'].widget.attrs.update({'class': 'form-control'})