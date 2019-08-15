import datetime
from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from conectores.models import Compania
from utils.SIISdk import SII_SDK 

class Libro(models.Model):
    """
    Model que contiene el registro de los libros que se emiten para un periodo
    """
    fk_compania = models.ForeignKey(Compania, on_delete=models.CASCADE)
    current_date = models.DateField()
    details = models.BooleanField(default=False)
    libro_xml = models.TextField()
    enviada = models.BooleanField(default=False)
    track_id = models.CharField(max_length=32, blank=True, null=True)
    
    class Meta:
        ordering = ('-current_date',)
        verbose_name = 'Libro'
        verbose_name_plural = 'Libros'

    def __str__(self):
        return self.current_date.strftime("%d-%m-%Y")

    def sign_base(self, tipo_operacion, tipo_libro, tipo_envio):
        """
        Firma el xml de libro de compra y venta
        @param tipo_operacion (COMPRA y VENTA)
        @param tipo_libro (MENSUAL o ESPECIAL)
        @param tipo_envio (TOTAL o PARCIAL)
        """
        compania = self.fk_compania
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        envio = render_to_string('xml_lcv/envio_libro.xml', {
            'libro_pk':self.pk,
            'compania':compania,
            'timestamp':timestamp,
            'tipo_operacion':tipo_operacion,
            'tipo_libro':tipo_libro,
            'tipo_envio':tipo_envio,
            'resumen_periodo':self.libro_xml
            })
        base = render_to_string('xml_lcv/lcv_base.xml', {
            'envio_libro':envio,
            })
        sii_sdk = SII_SDK(settings.SII_PRODUCTION)
        signed_xml = sii_sdk.generalSign(compania,base,compania.pass_certificado)
        return '<?xml version="1.0" encoding="ISO-8859-1"?>\n'+signed_xml
