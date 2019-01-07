import os
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.utils.timezone import now as timezone_now

from Crypto.Hash import SHA

# Create your models here.
from mixins.models import CreationModificationDateMixin
from conectores.models import Compania


def upload_file_to(instance, filename):
	now = timezone_now()
	filename_base, filename_ext = os.path.splitext(filename)
	return "cafs/%s%s" % (
		now.strftime("%Y/%m/%Y%m%d%H%M%S"),
		filename_ext.lower(),
	)


class Folio(CreationModificationDateMixin):

	empresa = models.ForeignKey(Compania, on_delete=models.CASCADE, blank=True, null=True)
	unique_hash = models.CharField(null=False, max_length=255, unique=True, db_index=True)
	caf = models.FileField(
					_('CAF'), 
					upload_to=upload_file_to, 
					blank=True, null=True, 
					validators=[FileExtensionValidator(allowed_extensions=['xml'])]
				)
	rut = models.CharField(null=False, max_length=255)
	tipo_de_documento = models.IntegerField(null=False)
	rango_desde = models.IntegerField(null=False)
	rango_hasta = models.IntegerField(null=False)
	folio_actual = models.IntegerField(null=False)
	folios_disponibles = models.IntegerField(null=False)
	fecha_de_autorizacion = models.DateTimeField(null=False)
	pk_modulo = models.CharField(null=False, max_length=255)
	pk_exponente = models.CharField(null=False, max_length=255)
	pem_public = models.TextField(null=True, default='')
	pem_private = models.TextField(null=True, default='')
	is_active = models.BooleanField(default=True)


	class Meta:

	    verbose_name = 'Folio'
	    verbose_name_plural = 'Folios'

	def hacer_hash(self):
		"""
		Crea un hash del rango con el tipo de documento para obtener un identificador unico del CAF
		"""
		assert type(self.rango_desde) == int, "rango desde no es un entero"
		assert type(self.rango_hasta) == int, "rango hasta no es un entero"
		# assert type(tipo) == int, "tipo de documento no es un entero"

		digest = SHA.new()
		digest.update(bytes(self.rango_desde))
		digest.update(bytes(self.rango_hasta))
		digest.update(bytes(int(self.tipo_de_documento)))

		return digest.hexdigest()



	def get_folio_actual(self):
		"""
		Retorna el ultimo folio que no ha sido asignado
		"""
		
		return self.folio_actual

	def asignar_folio(self, request):
		"""
		Asigna un nuevo folio, recalcula folios disponibles y el ultimo folio disponible (folio_actual)
		"""

		if self.folio_actual > self.rango_hasta:

			raise ValueError

		else:

			nuevo_folio = self.folio_actual
			self.folio_actual  += 1
			self.folios_disponibles -= 1

		return nuevo_folio
 

	def get_tipo_de_documento(self):

		if self.tipo_de_documento == 61:

			return "Nota de credito cod({})".format(self.tipo_de_documento)

		elif self.tipo_de_documento == 39:

			return "Boleta de venta cod({})".format(self.tipo_de_documento)

		elif self.tipo_de_documento == 33:

			return "Factura de venta cod({})".format(self.tipo_de_documento)
		else:
			return "Código desconocido cod({})".format(self.tipo_de_documento)

