from django import forms
from django.forms import ModelForm
from .models import *


class FormFactura(ModelForm):

    class Meta:
        model = Factura
        fields = ['compania','numero_factura','senores','direccion','transporte','despachar','observaciones',
                    'giro','condicion_venta','vencimiento','vendedor','rut','fecha','guia','orden_compra','nota_venta',
                    'productos','monto_palabra','neto','excento','iva','total']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['compania'].widget.attrs.update({'class': 'form-control'})
        self.fields['compania'].required = False
        self.fields['numero_factura'].widget.attrs.update({'class': 'form-control'})
        self.fields['numero_factura'].required = False
        self.fields['senores'].widget.attrs.update({'class': 'form-control'})
        self.fields['senores'].required = False
        self.fields['direccion'].widget.attrs.update({'class': 'form-control'})
        self.fields['direccion'].required = False
        self.fields['transporte'].widget.attrs.update({'class': 'form-control'})
        self.fields['transporte'].required = False
        self.fields['despachar'].widget.attrs.update({'class': 'form-control'})
        self.fields['despachar'].required = False
        self.fields['observaciones'].widget.attrs.update({'class': 'form-control'})
        self.fields['observaciones'].required = False
        self.fields['giro'].widget.attrs.update({'class': 'form-control'})
        self.fields['giro'].required = False
        self.fields['condicion_venta'].widget.attrs.update({'class': 'form-control'})
        self.fields['condicion_venta'].required = False
        self.fields['vencimiento'].widget.attrs.update({'class': 'form-control'})
        self.fields['vencimiento'].required = False
        self.fields['vendedor'].widget.attrs.update({'class': 'form-control'})
        self.fields['vendedor'].required = False
        self.fields['rut'].widget.attrs.update({'class': 'form-control'})
        self.fields['rut'].required = False
        self.fields['fecha'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha'].required = False
        self.fields['guia'].widget.attrs.update({'class': 'form-control'})
        self.fields['guia'].required = False
        self.fields['orden_compra'].widget.attrs.update({'class': 'form-control'})
        self.fields['orden_compra'].required = False
        self.fields['nota_venta'].widget.attrs.update({'class': 'form-control'})
        self.fields['nota_venta'].required = False
        self.fields['productos'].widget.attrs.update({'class': 'form-control'})
        self.fields['productos'].required = False
        self.fields['monto_palabra'].widget.attrs.update({'class': 'form-control'})
        self.fields['monto_palabra'].required = False
        self.fields['neto'].widget.attrs.update({'class': 'form-control'})
        self.fields['neto'].required = False
        self.fields['excento'].widget.attrs.update({'class': 'form-control'})
        self.fields['excento'].required = False
        self.fields['iva'].widget.attrs.update({'class': 'form-control'})
        self.fields['iva'].required = False
        self.fields['total'].widget.attrs.update({'class': 'form-control'})
        self.fields['total'].required = False
