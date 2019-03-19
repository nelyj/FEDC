from enum import Enum

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now as timezone_now
from django.utils import timezone
from django.core.validators import FileExtensionValidator

from Crypto.Hash import SHA
from dateutil.relativedelta import relativedelta

from mixins.models import CreationModificationDateMixin
from conectores.models import Compania

def upload_file_to(instance, filename):
	now = timezone_now()
	filename_base, filename_ext = os.path.splitext(filename)
	return "media/reportes/%s/%s%s" % (
		instance.compania.razon_social,
		filename_base,
		filename_ext.lower(),
	)


class Reporte(CreationModificationDateMixin):

	class TIPO_DE_REPORTE(Enum):

		boletas			= ("39", _('Libro de Boletas'))
		ventas			= ("33", _('Libro de Ventas'))


		@classmethod
		def get_value(cls, member):
			return cls[member].value[0]



	compania = models.ForeignKey(Compania, on_delete=models.CASCADE, blank=False, null=False)
	tipo_de_reporte = models.CharField(_('Tipo de reporte'),max_length=50,choices=[x.value for x in TIPO_DE_REPORTE],null=False,blank=False)
	fecha_de_inicio = models.DateField(_('Fecha de inicio'),null=False)
	fecha_de_culminacion = models.DateField(_('Fecha de culminación'),null=False)
	version_xml	= models.FileField(upload_to=upload_file_to, blank=True, null=True, validators=[FileExtensionValidator(['xml'])])
	enviado = models.BooleanField(default=False)


	def __str__(self):

		reporte = self.get_tipo_de_reporte()

		return "{} {}/{} {}".format(self.compania, self.fecha_de_inicio, self.fecha_de_culminacion, reporte)


	def get_tipo_de_reporte(self):

		if self.tipo_de_reporte == '33':

			return 'Libro de Ventas'

		elif self.tipo_de_reporte == '39': 

			return 'Libro de Boletas'

	@staticmethod
	def check_reporte_len(queryset):

		if len(queryset) == 0: 

			raise ValueError("No hay facturas para agregar al reporte")

		return 


