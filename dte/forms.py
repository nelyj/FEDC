from django import forms
from django.forms import ModelForm
from utils.constantes import FORMA_DE_PAGO, TIPO_DOCUMENTO
from .models import *

class FormCreateDte(ModelForm):
    """!
    Formulario para gestionar los dte

    @author Rodrigo Boet (rudmanmrrod at gmail.com)
    @date 15-10-2019
    @version 1.0.0
    """
    
    class Meta:
        model = DTE
        fields = ['numero_factura','senores','observaciones',
                    'giro','rut','fecha','tipo_dte', 'forma_pago',
                    'productos','ciudad_receptora','comuna', 'region','exento']

    forma_pago = forms.ChoiceField(
        widget=forms.Select(attrs={'class':'form-control'}),
        choices=FORMA_DE_PAGO)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['numero_factura'].widget.attrs.update({'class': 'form-control'})
        self.fields['numero_factura'].required = True
        self.fields['numero_factura'].label = "Número"
        self.fields['senores'].widget.attrs.update({'class': 'form-control'})
        self.fields['senores'].required = True
        self.fields['senores'].label = "Cliente"
        self.fields['observaciones'].widget = forms.Textarea()
        self.fields['observaciones'].widget.attrs.update({'class': 'form-control'})
        self.fields['observaciones'].required = False
        self.fields['giro'].widget.attrs.update({'class': 'form-control'})
        self.fields['giro'].required = True
        self.fields['rut'].widget.attrs.update({'class': 'form-control'})
        self.fields['rut'].required = True
        self.fields['fecha'].widget.attrs.update({'class': 'form-control datepicker', 'readonly':'readonly'})
        self.fields['fecha'].required = True
        self.fields['productos'].widget.attrs.update({'class': 'form-control', 'style':'display:none'})
        self.fields['productos'].required = False
        self.fields['ciudad_receptora'].widget.attrs.update({'class': 'form-control'})
        self.fields['ciudad_receptora'].required = True
        self.fields['comuna'].widget.attrs.update({'class': 'form-control'})
        self.fields['comuna'].required = True
        self.fields['region'].widget.attrs.update({'class': 'form-control'})
        self.fields['region'].required = True
        self.fields['region'].label = "Dirección"
        self.fields['forma_pago'].widget = forms.Select(attrs={'class':'form-control'})
        self.fields['forma_pago'].choices = FORMA_DE_PAGO
        self.fields['tipo_dte'].widget = forms.Select(attrs={'class':'form-control'})
        self.fields['tipo_dte'].choices = TIPO_DOCUMENTO
        self.fields['exento'].widget.attrs.update({'class': 'form-control'})