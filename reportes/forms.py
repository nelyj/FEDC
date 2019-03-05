from django import forms 
from django.contrib.admin.widgets import AdminDateWidget

from .models import Reporte
from conectores.models import Compania


class ReporteCreateForm(forms.ModelForm):

    class Meta:
        model = Reporte
        fields = [

            'compania',
            'tipo_de_reporte', 
            'fecha_de_inicio', 
            'fecha_de_culminacion'

        ]

    def __init__(self, *args, **kwargs):

        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        self.fields['compania'].widget.attrs.update({'class': 'form-control'})
        self.fields['tipo_de_reporte'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_de_inicio'].widget.attrs.update({'class': 'form-control datepicker', 'data-provide': 'datepicker','placeholder':'DD/MM/YYYY'})
        self.fields['fecha_de_culminacion'].widget.attrs.update({'class': 'form-control datepicker', 'data-provide': 'datepicker','placeholder':'DD/MM/YYYY'})
        self.fields['compania'].queryset = Compania.objects.filter(owner=self.request.user)




# self.fields['b2b_reviewer'].queryset = Affiliates.objects.filter(owner=self.request.user,verified=True,activated=True)