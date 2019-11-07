from django import forms

from django.forms import (
    modelformset_factory, formset_factory
)

from .models import *

class FormLibro(forms.ModelForm):
    """
    """
    class Meta:
        model = Libro
        fields = ('current_date', 'details')
        labels = {
            "details": "Posee detalles?",
            "current_date": "Fecha"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['current_date'].widget.attrs.update({
                                    'class': 'form-control',
                                    'placeholder': 'DD/MM/YYYY',
                                    'readonly': 'readonly'}
                                    )
        self.fields['details'].widget.attrs.update({'class': 'form-control'})


class CrearLibroCompraForm(forms.ModelForm):
    """
    """
    class Meta:
        model = DetailLibroCompra
        fields = ('tipo_dte', 'n_folio',
                  'observaciones', 'monto_exento',
                  'monto_afecto')

    def __ini__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['tipo_dte'].widget = forms.Select(attrs={'class':'form-control'})
                               
        self.fields['n_folio'].widget.attrs.update({'class': 'form-control'})
        self.fields['observaciones'].widget.attrs.update(
                                    {
                                        'class': 'form-control'
                                    }
                                )
        self.fields['monto_exento'].widget.attrs.update(
                                    {
                                        'class': 'form-control'
                                    }
                                )
        self.fields['monto_afecto'].widget.attrs.update(
                                    {
                                        'class': 'form-control'
                                    }
                                )


CrearLibroCompraFormFormSet = modelformset_factory(
                            DetailLibroCompra,
                            form=CrearLibroCompraForm,
                            min_num=1,
                            extra=0, validate_min=True,
                        )

formsetFac = formset_factory(CrearLibroCompraFormFormSet)
