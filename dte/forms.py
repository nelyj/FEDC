from django import forms
from django.forms import ModelForm
from conectores.constantes import COMUNAS
from utils.constantes import (
    FORMA_DE_PAGO, TIPO_DOCUMENTO, 
    VALOR_DESCUENTO, CODIGO_REFERENCIA)
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
                    'descuento_global', 'glosa_descuento', 'tipo_descuento', 'ref_factura',
                    'cod_ref', 'razon_ref']

    def __init__(self, *args, **kwargs):
        compania = kwargs.pop('compania')
        super().__init__(*args, **kwargs)
        self.fields['ref_factura'].widget.attrs.update({'class': 'form-control',
            'onchange':'load_dte_info(this.value)'})
        self.fields['ref_factura'].queryset = DTE.objects.filter(compania_id=compania,track_id=None)
        self.fields['ref_factura'].empty_label = "Seleccione..."
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
        self.fields['tipo_dte'].widget = forms.Select(attrs={'class':'form-control',
            'onchange':'show_dte_fields(this)'})
        self.fields['tipo_dte'].choices = TIPO_DOCUMENTO
        self.fields['descuento_global'].widget.attrs.update({'class': 'form-control'})
        self.fields['glosa_descuento'].widget.attrs.update({'class': 'form-control'})
        self.fields['glosa_descuento'].label = "Glosa de Descuento"
        self.fields['tipo_descuento'].widget = forms.Select(attrs={'class':'form-control'})
        self.fields['tipo_descuento'].label = "Tipo de Descuento"
        self.fields['tipo_descuento'].choices = VALOR_DESCUENTO
        self.fields['cod_ref'].widget = forms.Select(attrs={'class':'form-control',
            'onchange':'enable_dte_fields(this.value)'})
        self.fields['cod_ref'].label = label="Código de Referencia"
        self.fields['cod_ref'].choices = (('','Seleccione...'),) +CODIGO_REFERENCIA
        self.fields['razon_ref'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super(FormCreateDte, self).clean()
        descuento_global = cleaned_data['descuento_global']
        glosa_descuento = cleaned_data['glosa_descuento']
        tipo_descuento = cleaned_data['tipo_descuento']
        tipo_dte = cleaned_data['tipo_dte']
        cod_ref = cleaned_data['cod_ref']
        razon_ref = cleaned_data['razon_ref']
        if(descuento_global and glosa_descuento is None):
            self.add_error('glosa_descuento', 'Glosa del descuento es requerido')
        if(descuento_global and not tipo_descuento):
            self.add_error('tipo_descuento', 'Tipo de descuento es requerido')
        if(tipo_dte==56 and cod_ref!='' or tipo_dte==63 and cod_ref!=''):
            self.add_error('cod_ref', 'Código de referencia es requerido')
        if(tipo_dte==56 and razon_ref!='' or tipo_dte==63 and razon_ref!=''):
            self.add_error('cod_ref', 'Razon de referencia es requerido')