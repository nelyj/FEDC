from django.db import models
from django.contrib.auth.models import User

class Conector(models.Model):
    """
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.CharField(max_length=255)
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
