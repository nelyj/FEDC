from django.db import models
from django.contrib.auth.models import User

class Conector(models.Model):
    """
    """
    usuario = models.CharField(max_length=128)
    url = models.URLField(max_length=255)
    password = models.CharField(max_length=128)

    class Meta:
        """!
        Clase que construye los meta datos del modelo
        """
        ordering = ('usuario',)
        verbose_name = 'Conector'
        verbose_name_plural = 'Conectores'

    def __str__(self):
        return self.url
