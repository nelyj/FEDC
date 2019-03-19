"""
Facturador TIMG
@package utils.SIISdk

Sdk para comunicarse con el SII(Servicio de Impuestos Internos)
@copyright TIMG
@version 1.0
"""
import requests
import xmlsec
import xml.etree.ElementTree as ET
from django.conf import settings
from django.template.loader import render_to_string

from lxml import etree


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
        soap = '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
        soap += '<SOAP-ENV:Body><m:getSeed xmlns:m="https://maullin.sii.cl/DTEWS/CrSeed.jws"/>' 
        soap += '</SOAP-ENV:Body></SOAP-ENV:Envelope>'
        headers = {'content-type': 'text/xml', 'SOAPAction':''}
        response = requests.post('https://maullin.sii.cl/DTEWS/CrSeed.jws?WSDL',data=soap,headers=headers)
        body = self._get_soap_body(response.content)
        response = body.find('{https://maullin.sii.cl/DTEWS/CrSeed.jws}getSeedResponse').find('{https://maullin.sii.cl/DTEWS/CrSeed.jws}getSeedReturn').text
        xml_response = ET.fromstring(response)
        return xml_response.find('{http://www.sii.cl/XMLSchema}RESP_BODY').find('SEMILLA').text

    def getAuthToken(self,seed_sign):
        """!
        Método para enviar la semilla firmada al sii
        @return xml con la semilla
        """
        soap = '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">' 
        soap += '<SOAP-ENV:Body><m:getToken xmlns:m="https://maullin.sii.cl/DTEWS/GetTokenFromSeed.jws">'
        soap += '<pszXml xsi:type="xsd:string"><![CDATA['+seed_sign+']]></pszXml>'
        soap += '</m:getToken></SOAP-ENV:Body></SOAP-ENV:Envelope>'
        headers = {'content-type': 'text/xml', 'SOAPAction':''}
        response = requests.post('https://maullin.sii.cl/DTEWS/GetTokenFromSeed.jws?WSDL',data=soap,headers=headers)
        body = self._get_soap_body(response.content)
        response = body.find('{https://maullin.sii.cl/DTEWS/GetTokenFromSeed.jws}getTokenResponse').find('{https://maullin.sii.cl/DTEWS/GetTokenFromSeed.jws}getTokenReturn').text
        xml_response = ET.fromstring(response)
        estado = xml_response.find('{http://www.sii.cl/XMLSchema}RESP_HDR').find('ESTADO').text
        if(estado=='00'):
            return xml_response.find('{http://www.sii.cl/XMLSchema}RESP_BODY').find('TOKEN').text
        else:
            return False

    def signXml(self, seed, compania, pass_certificado):
        """
        Método para crear la firma
        @param compania recibe el objeto compañia
        @return xml con la fima 
        """
    
        signature = etree.parse('facturas/templates/snippets/signature_sii.xml').getroot()
        signature = etree.tostring(signature)
        authentication = render_to_string('snippets/authentication.xml', {'seed':seed,'signature':signature.decode()})
        return self.generalSign(compania,authentication, pass_certificado)

    def generalSign(self,compania,xml_string, pass_certificado):
        """
        Método para firmar cualquier xml
        @param compania recibe el objeto compañia
        @param compania recibe el string a firmar
        @return xml con la fima 
        """
        template = etree.fromstring(xml_string)
        signature_node = xmlsec.tree.find_node(template, xmlsec.constants.NodeSignature)
        ctx = xmlsec.SignatureContext()
        ruta_pfx = settings.MEDIA_ROOT + str(compania.certificado)
        key = xmlsec.Key.from_file(ruta_pfx, xmlsec.constants.KeyDataFormatPkcs12, pass_certificado)
        ctx.key = key
        ctx.sign(signature_node)
        tree= etree.XML(str(etree.tostring(template).decode()))
        rem = tree.findall(".//{http://www.w3.org/2000/09/xmldsig#}X509Certificate")
        if(len(rem)>1):
            for element in rem[:-1]:
                element.getparent().remove(element)
            return etree.tostring(tree).decode()
        else:
            return etree.tostring(template).decode()

    def multipleSign(self,compania,xml_string, pass_certificado, index):
        """
        Método para firmar cualquier xml
        @param compania recibe el objeto compañia
        @param compania recibe el string a firmar
        @return xml con la fima 
        """
        tree = etree.fromstring(xml_string)
        sig = tree.findall(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
        s = sig[index]
        ctx = xmlsec.SignatureContext()
        ruta_pfx = settings.MEDIA_ROOT + str(compania.certificado)
        key = xmlsec.Key.from_file(ruta_pfx, xmlsec.constants.KeyDataFormatPkcs12, pass_certificado)
        ctx.key = key
        ctx.sign(s)
        tree= etree.XML(etree.tostring(tree).decode())
        sig = tree.findall(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
        s = sig[index]
        rem = s.findall(".//{http://www.w3.org/2000/09/xmldsig#}X509Certificate")
        if(len(rem)>1):
            for element in rem[:-1]:
                element.getparent().remove(element)
        return etree.tostring(tree).decode()


    def sendInvoice(self,token,invoice,rut_sender,rut_company):
        """
        Método para enviar la factura
        @param token recibe el token
        @param invoice recibe la factura
        @param rut_sender recibe el rut de quien envia
        @param rut_company recibe el rut de la compañia
        @return xml con los datos 
        """
        headers = {'User-Agent': 'Mozilla/4.0 (compatible; PROG 1.0; LibreDTE)',
        'Cookie':'TOKEN='+token}
        rut_s,dv_s = rut_sender.split('-')
        rut_c,dv_c = rut_company.split('-')
        files = {'archivo': invoice}
        values = {'rutSender': rut_s, 'dvSender': dv_s, 'rutCompany': rut_c,'dvCompany':dv_c}
        response = request.post('https://maullin.sii.cl/sii.cl/cgi_dte/UPL/DTEUpload',files=files,data=values)
        print(response)
        xml_response = ET.fromstring(response)