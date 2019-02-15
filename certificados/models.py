from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

from mixins.models import CreationModificationDateMixin
from conectores.models import Compania

# Create your models here.


def upload_certificate_to(instance, filename):
	now = timezone_now()
	filename_base, filename_ext = os.path.splitext(filename)
	return "certificados/%s%s" % (
		now.strftime("%Y/%m/%Y%m%d%H%M%S"),
		filename_ext.lower(),
	)


class Certificado(CreationModificationDateMixin):

	empresa = models.ForeignKey(Compania, on_delete=models.CASCADE, blank=True, null=True)
	owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
	certificado = models.FileField(
					_('Certificado digital'), 
					upload_to=upload_certificate_to, 
					blank=True, null=True, 
					validators=[FileExtensionValidator(allowed_extensions=['xml'])]
				)
	



	class Meta:

	    verbose_name = 'Certificado'
	    verbose_name_plural = 'Certificados'


	def upload_file_to(instance, filename):
		now = timezone_now()
		filename_base, filename_ext = os.path.splitext(filename)
		return "certificados/%s%s" % (
			now.strftime("%Y/%m/%Y%m%d%H%M%S"),
			filename_ext.lower(),
		)