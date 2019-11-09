import datetime

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.template.loader import render_to_string

from conectores.models import Compania

from utils.constantes import TIPO_DOCUMENTO
from utils.SIISdk import SII_SDK
from utils.utils import validate_string_number

from .constants import CHOICE_LIBRO


class Libro(models.Model):
    """
    Model que contiene el registro de los libros que se emiten para un periodo
    """
    error_messages = {
        'invalid': 'Ingresa un año y mes con un formato valido (YYYY-mm).',
    }
    fk_compania = models.ForeignKey(Compania, on_delete=models.CASCADE)
    current_date = models.DateField()
    details = models.BooleanField(default=False)
    libro_xml = models.TextField()
    enviada = models.BooleanField(default=False)
    track_id = models.CharField(max_length=32, blank=True, null=True)
    tipo_libro = models.PositiveSmallIntegerField(
                    choices=CHOICE_LIBRO, default=1
                )
    periodo = models.CharField(max_length=12)

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

    def save(self, *args, **kwargs):
        """ This step is just formatting: add the dash if missing """
        if isinstance(self.periodo, datetime.datetime):
            self.periodo = format(self.periodo, '%Y-%m')
        else:
            raise ValidationError(self.error_messages['invalid'])
        super(Libro, self).save(*args, **kwargs)


class DetailLibroCompra(models.Model):
    """
    Model que contiene el registro del detalle de los libro de compra
    """
    fk_libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    tipo_dte = models.PositiveSmallIntegerField(choices=TIPO_DOCUMENTO)
    n_folio = models.IntegerField(default=0)
    observaciones = models.TextField(null=True, blank=True)
    monto_exento = models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[MinValueValidator(Decimal('0.00'))]
                    )
    monto_afecto = models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[MinValueValidator(Decimal('0.00'))]
                    )

    def __str__(self):
        return self.numero_factura
