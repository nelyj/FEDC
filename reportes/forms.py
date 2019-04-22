import datetime 
from django import forms 
from django.contrib.admin.widgets import AdminDateWidget

from .models import Reporte
from conectores.models import Compania


class ReporteCreateForm(forms.ModelForm):

    """
    Clase para el formulario de Reportes
    @author Alberto Rincones (alberto at timg.cl)
    @copyright TIMG
    @date 28-03-19 (dd-mm-YY)
    @version 1.0
    """

    class Meta:
        model = Reporte
        fields = [
            'tipo_de_operacion',
            'tipo_de_envio',
            'tipo_de_libro',
            'fecha_de_inicio', 
            'fecha_de_culminacion',
            'folio_notificacion',
            'periodo_tributario'
        ]

    def __init__(self, *args, **kwargs):

        self.request = kwargs.pop('request', None) 
        super().__init__(*args, **kwargs)

        self.fields['tipo_de_operacion'].widget.attrs.update({'class': 'form-control'})
        self.fields['tipo_de_envio'].widget.attrs.update({'class': 'form-control'})
        self.fields['tipo_de_libro'].widget.attrs.update({'class': 'form-control'}) 
        self.fields['folio_notificacion'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_de_inicio'].widget.attrs.update({'autocomplete':'off','class': 'form-control datepicker', 'data-provide': 'datepicker','placeholder':'DD/MM/YYYY'})
        self.fields['fecha_de_inicio'].required = False
        self.fields['fecha_de_culminacion'].widget.attrs.update({'autocomplete':'off','class': 'form-control datepicker', 'data-provide': 'datepicker','placeholder':'DD/MM/YYYY'})
        self.fields['fecha_de_culminacion'].required = False
        self.fields['periodo_tributario'].widget.attrs.update({'autocomplete':'off','class': 'form-control','placeholder':'YYYY-MM'})
        self.fields['periodo_tributario'].required = False

    def clean(self):        

        cleaned_data = super(ReporteCreateForm, self).clean()
        today = datetime.date.today()
        fecha_de_inicio = cleaned_data.get('fecha_de_inicio')
        fecha_de_culminacion = cleaned_data.get('fecha_de_culminacion')
        periodo_tributario = cleaned_data.get('periodo_tributario')
        tipo_de_envio = cleaned_data.get('tipo_de_envio')

        if(tipo_de_envio=='TOTAL' and periodo_tributario==''):
            raise forms.ValidationError('El periodo tributario es obligatorio',code='required')

        else:
            if(tipo_de_envio!='TOTAL' and fecha_de_inicio is None):
                raise forms.ValidationError('La fecha inicio es requerida',code='required')
            elif(tipo_de_envio!='TOTAL' and fecha_de_culminacion is None):
                raise forms.ValidationError('La fecha culminación es requerida',code='required')
            elif(tipo_de_envio!='TOTAL'):
                if fecha_de_culminacion < fecha_de_inicio: 

                    raise forms.ValidationError('Fecha de inicio no debe ser mayor a fecha de culminacion',code='invalid_date')

                if fecha_de_inicio > today:

                    raise forms.ValidationError('Fecha de inicio no puede ser mayor a la fecha actual',code='inicio_mayor_actual')

                if fecha_de_culminacion > today:

                    raise forms.ValidationError('Fecha de culminacion no puede ser mayor a la fecha actual',code='inicio_mayor_actual')

        return cleaned_data 