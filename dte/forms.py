from django import forms
from django.forms import ModelForm
from conectores.constantes import COMUNAS
from utils.constantes import FORMA_DE_PAGO, TIPO_DOCUMENTO, VALOR_DESCUENTO
from .models import *

class FormCreateDte(ModelForm):
    """!
    Formulario para gestionar los dte

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 15-10-2019
    @version 1.0.0
    """
    
    class Meta:
        model = DTE
        fields = ['numero_factura','senores', 'giro',
                    'rut','fecha','tipo_dte', 'forma_pago',
                    'productos','ciudad_receptora','comuna', 'region', 
                    'descuento_global', 'glosa_descuento', 'tipo_descuento']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['numero_factura'].widget.attrs.update({'class': 'form-control'})
        self.fields['numero_factura'].label = "Número"
        self.fields['senores'].widget.attrs.update({'class': 'form-control'})
        self.fields['senores'].label = "Señor(es)"
        self.fields['giro'].widget.attrs.update({'class': 'form-control'})
        self.fields['rut'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha'].widget.attrs.update({'class': 'form-control datepicker', 'readonly':'readonly'})
        self.fields['productos'].widget.attrs.update({'class': 'form-control', 'style':'display:none'})
        self.fields['productos'].required = False
        self.fields['ciudad_receptora'].widget.attrs.update({'class': 'form-control'})
        self.fields['comuna'].widget = forms.Select(attrs={'class':'form-control'})
        self.fields['comuna'].choices = COMUNAS
        self.fields['region'].widget.attrs.update({'class': 'form-control'})
        self.fields['region'].label = "Dirección"
        self.fields['forma_pago'].widget = forms.Select(attrs={'class':'form-control'})
        self.fields['forma_pago'].choices = FORMA_DE_PAGO
        self.fields['tipo_dte'].widget = forms.Select(attrs={'class':'form-control'})
        self.fields['tipo_dte'].choices = TIPO_DOCUMENTO
        self.fields['descuento_global'].widget.attrs.update({'class': 'form-control'})
        self.fields['glosa_descuento'].widget.attrs.update({'class': 'form-control'})
        self.fields['region'].label = "Glosa de Descuento"
        self.fields['tipo_descuento'].widget = forms.Select(attrs={'class':'form-control'})
        self.fields['region'].label = "Tipo de Descuento"
        self.fields['tipo_descuento'].choices = VALOR_DESCUENTO

    def clean(self):
        cleaned_data = super(FormCreateDte, self).clean()
        descuento_global = cleaned_data['descuento_global']
        glosa_descuento = cleaned_data['glosa_descuento']
        tipo_descuento = cleaned_data['tipo_descuento']
        if(descuento_global and glosa_descuento is None):
            self.add_error('glosa_descuento', 'Glosa del descuento es requerido')
        if(descuento_global and not tipo_descuento):
            self.add_error('tipo_descuento', 'Tipo de descuento es requerido')