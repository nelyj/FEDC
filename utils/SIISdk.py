"""
Facturador TIMG
@package utils.SIISdk

Sdk para comunicarse con el SII(Servicio de Impuestos Internos)
@copyright TIMG
@version 1.0
"""
import requests
import xml.etree.ElementTree as ET

class SII_SDK():
	"""
	Clase principal del sdk
	@author Rodrigo Boet (rodrigoale.b at timg.cl)
	@copyright TIMG
	@date 27-02-19 (dd-mm-YY)
	@version 1.0
	"""
	def _get_soap_body(self,soap_string):
		"""!
		Método para obtener el cuerpo de una petición
		SOAP
		@param soap_string recibe el string de una petición SOAP
		@return body
		"""
		body = ET.fromstring(soap_string)
		return body.find('{http://schemas.xmlsoap.org/soap/envelope/}Body')

	def getSeed(self):
		"""!
		Método para solicitar la semilla al SII
		@return xml con la semilla
		"""
		html = '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
		html += '<SOAP-ENV:Body><m:getSeed xmlns:m="https://palena.sii.cl/DTEWS/CrSeed.jws"/>' 
		html += '</SOAP-ENV:Body></SOAP-ENV:Envelope>'
		headers = {'content-type': 'text/xml', 'SOAPAction':''}
		response = requests.post('https://palena.sii.cl/DTEWS/CrSeed.jws?WSDL',data=html,headers=headers)
		body = self._get_soap_body(response.content)
		response = body.find('{https://palena.sii.cl/DTEWS/CrSeed.jws}getSeedResponse').find('{https://palena.sii.cl/DTEWS/CrSeed.jws}getSeedReturn').text
		xml_response = ET.fromstring(response)
		return xml_response.find('{http://www.sii.cl/XMLSchema}RESP_BODY').find('SEMILLA').text
