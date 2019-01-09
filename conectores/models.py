from django.db import models
from django.contrib.auth.models import User
from .constantes import (COMUNAS, ACTIVIDADES)

class Conector(models.Model):
    """
    """
    def get_upload_to(self, filename):
        return "certificados/%s/%s" % (self.usuario, filename)

    usuario = models.CharField(max_length=128, blank=True, null=True)
    url_erp = models.URLField(max_length=255, blank=True, null=True)
    url_sii = models.URLField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    certificado = models.FileField(upload_to=get_upload_to, blank=True, null=True)
    time_cron = models.IntegerField(default=10, blank=True, null=True)

    class Meta:
        """!
        Clase que construye los meta datos del modelo
        """
        ordering = ('usuario',)
        verbose_name = 'Conector'
        verbose_name_plural = 'Conectores'

    def __str__(self):
        return self.url_erp

class Compania(models.Model):
    """
    """
    def get_upload_to(self, filename):
        return "logos/%s/%s" % (self.rut, filename)
        
    rut = models.CharField(max_length=128, blank=True, null=True)
    razon_social = models.CharField(max_length=128, blank=True, null=True)
    actividad_principal = models.CharField(max_length=128,choices=ACTIVIDADES, blank=True, null=True)
    giro = models.CharField(max_length=128,choices=ACTIVIDADES, blank=True, null=True)
    direccion = models.CharField(max_length=128, blank=True, null=True)
    comuna = models.CharField(max_length=128, choices=COMUNAS, blank=True, null=True)
    logo = models.FileField(upload_to=get_upload_to, blank=True, null=True)
    fecha_resolucion = models.DateField(blank=True, null=True)
    numero_resolucion = models.IntegerField(blank=True, null=True)
    correo_sii = models.EmailField(blank=True, null=True)
    pass_correo_sii = models.CharField(max_length=128, blank=True, null=True)
    correo_intercambio = models.EmailField(blank=True, null=True)
    pass_correo_intercambio = models.CharField(max_length=128, blank=True, null=True)


    class Meta:
        """!
        Clase que construye los meta datos del modelo
        """
        ordering = ('rut',)
        verbose_name = 'Compania'
        verbose_name_plural = 'Companias'

    def __str__(self):
        return self.rut
