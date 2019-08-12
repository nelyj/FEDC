from django.db import models
from conectores.models import Compania    

class Libro(models.Model):
    """
    Model que contiene el registro de los libros que se emiten para un periodo
    """
    fk_compania = models.ForeignKey(Compania, on_delete=models.CASCADE)
    current_date = models.DateField()
    details = models.BooleanField(default=False)
    libro_xml = models.TextField()
    enviada = models.BooleanField(default=False)
    
    class Meta:
        ordering = ('-current_date',)
        verbose_name = 'Libro'
        verbose_name_plural = 'Libros'

    def __str__(self):
        return self.start_date.strftime("%d-%m-%Y")
