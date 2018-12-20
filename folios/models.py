import os
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.utils.timezone import now as timezone_now

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
	caf = models.FileField(
					_('CAF'), 
					upload_to=upload_file_to, 
					blank=True, null=True, 
					validators=[FileExtensionValidator(allowed_extensions=['xml'])]
				)
	rut = models.CharField(null=False, max_length=255)
	tipo_de_documento = models.CharField(null=False, max_length=255)
	rango_desde = models.IntegerField(null=False)
	rango_hasta = models.IntegerField(null=False)
	folios_disponibles = models.IntegerField(null=False)
	fecha_de_autorizacion = models.DateTimeField(null=False)
	pk_modulo = models.CharField(null=False, max_length=255)
	pk_exponente = models.CharField(null=False, max_length=255)


	class Meta:

	    verbose_name = 'Folio'
	    verbose_name_plural = 'Folios'

	def get_tipo_de_documento(self):

		if int(self.tipo_de_documento) == 61:

			return "Nota de credito cod({})".format(self.tipo_de_documento)

		elif int(self.tipo_de_documento) == 39:

			return "Boleta de venta cod({})".format(self.tipo_de_documento)

		elif int(self.tipo_de_documento) == 33:

			return "Factura de venta cod({})".format(self.tipo_de_documento)
		else:
			return "Código desconocido cod({})".format(self.tipo_de_documento)


