# -*- encoding: utf-8 -*-
"""!
Modelo que construye los modelos de datos de los usuarios

@author Ing. Leonel P. Hernandez M. (leonelphm at gmail.com)
@copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
@date 09-06-2017
@version 1.0.0
"""
from django.db import models


class Pais(models.Model):
    """!
    Clase que contiene el modelo de datos de los países

    @author Ing. Leonel Paolo Hernandez Macchiarulo  (leonelphm at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-06-2017
    @version 1.0.0
    """
    nombre = models.CharField(max_length=50)

    class Meta:
        ordering = ('nombre',)
        verbose_name = 'Pais'
        verbose_name_plural = 'Paises'

    def __str__(self):
        return self.nombre


class Estado(models.Model):
    """!
    Clase que contiene el modelo de datos de los Estados

    @author Ing. Leonel Paolo Hernandez Macchiarulo  (leonelphm at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-06-2017
    @version 1.0.0
    """
    nombre = models.CharField(max_length=50)
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE)

    class Meta:
        ordering = ('nombre',)
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'


    def __str__(self):
        return self.nombre


class Municipio(models.Model):
    """!
    Clase que contiene el modelo de datos de los Municipios

    @author Ing. Leonel Paolo Hernandez Macchiarulo  (leonelphm at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-06-2017
    @version 1.0.0
    """
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=50)

    class Meta:
        ordering = ('nombre',)
        verbose_name = 'Municipio'
        verbose_name_plural = 'Municipios'

    def __str__(self):
     return self.nombre


class Parroquia(models.Model):
    """!
    Clase que contiene el modelo de datos de  las Parroquias

    @author Ing. Leonel Paolo Hernandez Macchiarulo  (leonelphm at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-06-2017
    @version 1.0.0
    """
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=50)
    
    class Meta:
        ordering = ('nombre',)
        verbose_name = 'Parroquia'
        verbose_name_plural = 'Parroquias'

    def __str__(self):
        return self.nombre


class TipoDocumento(models.Model):
    """!
    Clase que contiene el modelo de datos del Tipo de  Documento

    @author Ing. Leonel Paolo Hernandez Macchiarulo  (leonelphm at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-06-2017
    @version 1.0.0
    """
    abreviatura = models.CharField(max_length=4, verbose_name='Acrónimo')
    descripcion = models.TextField()

    class Meta:
        ordering = ('abreviatura',)
        verbose_name = 'Tipo Documento'
        verbose_name_plural = 'Tipos Documentos'

    def __str__(self):
        return self.abreviatura