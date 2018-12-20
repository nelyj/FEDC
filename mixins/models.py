from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

class CreationModificationDateMixin(models.Model):
	"""
	Abstract base class with a creation and modification date and time	

	"""
	created = models.DateTimeField(
		_("Tiempo y fecha de creación"),
		editable=False,
		auto_now_add=True,
		null=True,

	)
	modified = models.DateTimeField(
		_("Tiempo y fecha de modificación"),
		null=True,
		# editable=True,
		auto_now=True,
	)

	def save(self, *args, **kwargs):

		if not self.id:
			self.created = timezone.now()
		self.modified = timezone.now()
		return super(CreationModificationDateMixin, self).save(*args, **kwargs)


	class Meta:

		abstract = True