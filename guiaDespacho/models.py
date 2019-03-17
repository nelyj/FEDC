from django.db import models
from conectores.models import Compania
from mixins.models import CreationModificationDateMixin

class guiaDespacho(CreationModificationDateMixin):
	"""!
	Modelo Guia de Despacho
	"""
	status = models.CharField(max_length=128,blank=True, null=True)
	compania = models.ForeignKey(Compania, on_delete=models.CASCADE, blank=True, null=True)
	numero_factura = models.CharField(max_length=128, blank=True, null=True)
	class Meta:
		# ordering = ('numero_factura',)
		verbose_name = 'Guia de Despacho'
		verbose_name_plural = 'Guias de Despacho'

		def __str__(self):
			return self.numero_factura
