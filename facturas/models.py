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
from certificados.models import Certificado
from .utils import extraer_modulo_y_exponente, generar_firma_con_certificado

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

			# print(str(self.n_folio)+ str('asignado con exito'))

		else: 

			return 


	def _firmar_dd(data, folio, instance): 

		"""
		Llena los campos de que se encuentran dentro de la etiqueta
		<DD> del DTE y anade la firma correspondiente en la etiqueta
		<FMRT>. Retorna la etiqueta <DD> con su contenido, firmada y
		sin aplanar.

		"""

		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S").split()

		timestamp = "{}T{}".format(now[0],now[1])

		# print(timestamp)

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

		# print(sin_aplanar)

		return sin_aplanar


	def firmar_documento(etiqueta_DD, datos, folio, compania):

		"""
		Llena los campos de la etiqueta <Documento>, y la firma usando la 
		plantilla signature.xml. Retorna la etiquta <Documento> con sus datos y 
		la correspondiente firma con la clave privada cargada por el usuario en
		el certificado.
		"""

		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S").split()

		timestamp = "{}T{}".format(now[0],now[1])

		documento_sin_aplanar = render_to_string(
			'snippets/Documento_tag.xml', {
				'datos':datos,
				'folio':folio, 
				'compania':compania, 
				'timestamp':timestamp,
				'DD':etiqueta_DD 
			})

		digest_string = documento_sin_aplanar.replace('\n','').replace('\t','').replace('\r','')


		firma_electronica = generar_firma_con_certificado(compania, digest_string)

		signature_tag = render_to_string('snippets/signature.xml', {'signature':firma_electronica})

		documento_sin_aplanar += "\n{}".format(signature_tag)

	
		return documento_sin_aplanar


	def firmar_etiqueta_set_dte(compania, folio, etiqueta_Documento):


		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S").split()

		timestamp_firma = "{}T{}".format(now[0],now[1])

		set_dte_sin_aplanar = render_to_string(
			'snippets/set_DTE_tag.xml', {
				'compania':compania, 
				'folio':folio, 
				'timestamp_firma':timestamp_firma,
				'documento': etiqueta_Documento
			}
		)

		digest_string = set_dte_sin_aplanar.replace('\n','').replace('\t','').replace('\r','')

		firma_electronica = generar_firma_con_certificado(compania, digest_string)

		signature_tag = render_to_string('snippets/signature.xml', {'signature':firma_electronica})


		set_dte_sin_aplanar += "\n{}".format(signature_tag)

		# print(set_dte_sin_aplanar)


		return set_dte_sin_aplanar


	def generar_documento_final(etiqueta_SetDte):

		documento_final = render_to_string('invoice.xml', {'set_DTE':etiqueta_SetDte})

		documento_final_sin_tabs = documento_final.replace('\t','').replace('\r','')

		print(documento_final_sin_tabs)

		return documento_final_sin_tabs




	
