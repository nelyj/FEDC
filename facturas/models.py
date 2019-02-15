import datetime
from base64 import b64decode,b64encode

from django.db import models
from django.contrib.auth.models import User
from django.template.loader import render_to_string

from conectores.constantes import (COMUNAS, ACTIVIDADES)
from conectores.models import Compania
from folios.models import Folio
from folios.exceptions import ElCafNoTieneMasTimbres
from mixins.models import CreationModificationDateMixin

from bs4 import BeautifulSoup
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA
from Crypto.Signature import PKCS1_v1_5


class Factura(CreationModificationDateMixin):
	"""!
	Modelo Producto
	"""
	status = models.CharField(max_length=128,blank=True, null=True)
	compania = models.ForeignKey(Compania, on_delete=models.CASCADE, blank=True, null=True)
	numero_factura = models.CharField(max_length=128, blank=True, null=True, db_index=True)
	senores = models.CharField(max_length=128, blank=True, null=True)
	direccion = models.CharField(max_length=128, blank=True, null=True)
	transporte = models.CharField(max_length=128, blank=True, null=True)
	despachar = models.CharField(max_length=128, blank=True, null=True)
	observaciones = models.CharField(max_length=255, blank=True, null=True)
	giro = models.CharField(max_length=128, blank=True, null=True)
	condicion_venta = models.CharField(max_length=128, blank=True, null=True)
	vencimiento = models.DateField(blank=True, null=True)
	vendedor = models.CharField(max_length=128, blank=True, null=True)
	rut = models.CharField(max_length=128, blank=True, null=True)
	fecha = models.DateField(blank=True, null=True)
	guia = models.CharField(max_length=128, blank=True, null=True)
	orden_compra = models.CharField(max_length=128, blank=True, null=True)
	nota_venta = models.CharField(max_length=128, blank=True, null=True)
	productos = models.TextField(blank=True, null=True)
	monto_palabra = models.CharField(max_length=128, blank=True, null=True)
	neto = models.CharField(max_length=128, blank=True, null=True)
	excento = models.CharField(max_length=128, blank=True, null=True)
	iva = models.CharField(max_length=128, blank=True, null=True)
	total = models.CharField(max_length=128, blank=True, null=True)
	n_folio = models.IntegerField(null=True, default=0)

	
	class Meta:
		ordering = ('numero_factura',)
		verbose_name = 'Factura'
		verbose_name_plural = 'Facturas'

		def __str__(self):
			return self.numero_factura

	def recibir_folio(self, folio):

		if isinstance(folio, Folio):

			try:
				n_folio = folio.asignar_folio()
			except (ElCafNoTieneMasTimbres, ValueError):

				raise ElCafNoTieneMasTimbres
			# except ValueError: 
			assert type(n_folio) == int, "folio no es entero"

			self.n_folio = n_folio 

			print(f'{self.n_folio} asignado con exito')

		else: 

			return 


	def _firmar_dd(data, folio, instance): 

		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S").split()

		timestamp = f"{now[0]}T{now[1]}"

		print(timestamp)

		sin_aplanar = render_to_string('snippets/DD_tag.xml', {'data':data,'folio':folio, 'instance':instance, 'timestamp':timestamp})
		digest_string = sin_aplanar.replace('\n','').replace('\t','').replace('\r','')

		RSAprivatekey = RSA.importKey(folio.pem_private)
		private_signer = PKCS1_v1_5.new(RSAprivatekey)


		digest = SHA.new()
		digest.update(digest_string.encode('iso8859-1'))
		sign = private_signer.sign(digest)

		firma = f'<FRMT algoritmo="SHA1withRSA">{b64encode(sign).decode()}</FRMT>'

		# print(firma)

		sin_aplanar += firma

		print(sin_aplanar)

		return sin_aplanar

	def firmar_documento(etiqueta_DD, datos, folio):

		return 

		


# 		"""
# <FRMT algoritmo="SHA1withRSA">IC5N6cxClFn7HkKrnFpW0XcldExD72EhLX/zoI3Dt4YbpMtvROUuGhVZiqKqY2rteXDtPawZAzmIXDpQeCX4aQ==</FRMT>"""

# 		return 

	# # @class_method
	# def firmar_factura(dte_string):

	# 	soup = BeautifulSoup(dte_string, 'xml')

	# 	documento = soup.EnvioDTE.Documento.text

	# 	SetDTE =  soup.EnvioDTE.SetDTE.text


	# 	return 



