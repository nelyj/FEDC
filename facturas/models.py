from django.db import models
from django.contrib.auth.models import User
from conectores.constantes import (COMUNAS, ACTIVIDADES)
from conectores.models import Compania


class Factura(models.Model):
	"""!
	Modelo Producto
	"""
	compania = models.ForeignKey(Compania, on_delete=models.CASCADE, blank=True, null=True)
	numero_factura = models.CharField(max_length=128)
	senores = models.CharField(max_length=128)
	direccion = models.CharField(max_length=128)
	transporte = models.CharField(max_length=128)
	despachar = models.CharField(max_length=128)
	observaciones = models.CharField(max_length=255)
	giro = models.CharField(max_length=128)
	condicion_venta = models.CharField(max_length=128)
	vencimiento = models.DateField()
	vendedor = models.CharField(max_length=128)
	rut = models.CharField(max_length=128)
	fecha = models.DateField()
	guia = models.CharField(max_length=128)
	orden_compra = models.CharField(max_length=128)
	nota_venta = models.CharField(max_length=128)
	productos = models.TextField()
	monto_palabra = models.CharField(max_length=128)
	neto = models.CharField(max_length=128)
	excento = models.CharField(max_length=128)
	iva = models.CharField(max_length=128)
	total = models.CharField(max_length=128)

	class Meta:
		ordering = ('numero_factura',)
		verbose_name = 'Factura'
		verbose_name_plural = 'Facturas'

		def __str__(self):
			return self.numero_factura