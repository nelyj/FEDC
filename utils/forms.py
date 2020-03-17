from django.forms import ModelForm

from .models import Parametro

class FormularioParametro(ModelForm):
    class Meta:
        model = Parametro
        fields = ['envio_automatico', 'sii_produccion']

    def __init__(self, *args, **kwargs):

        super(FormularioParametro, self).__init__(*args, **kwargs)

        self.fields['envio_automatico'].label = '¿Se harán envios automaticos desde el ERPNext al SII?'
        self.fields['envio_automatico'].widget.attrs.update({'class': 'form-control','data-toggle': 'toggle','data-on': 'Si',
                                                   'data-off': 'No' })

        self.fields['sii_produccion'].label = '¿Configurar variables del SII en produccion?'
        self.fields['sii_produccion'].widget.attrs.update({'class': 'form-control','data-toggle': 'toggle','data-on': 'Si',
                                                   'data-off': 'No' })