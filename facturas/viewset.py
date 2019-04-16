"""
Facturador TIMG
@package factura.viewset

Router del api de Rest Framework
@copyright TIMG
@version 1.0
"""
from django.conf import settings
from rest_framework import viewsets
from rest_framework.response import Response

from conectores.models import *
from folios.models import Folio
from folios.exceptions import ElCafNoTieneMasTimbres, ElCAFSenEncuentraVencido
from .models import Factura

class FacturaViewSet(viewsets.ViewSet):
  """
  Clase para la vista en rest de la factura
  @author Rodrigo Boet (rodrigoale.b at timg.cl)
  @copyright TIMG
  @date 15-04-19 (dd-mm-YY)
  @version 1.0
  """

  def create(self, request, pk, slug):
    value = True
    factura = dict(zip(request.data['data'].keys(), request.data['data'].values()))
    try:
      usuario = Conector.objects.filter(t_documento='33',empresa=pk).first()
      compania = Compania.objects.filter(pk=pk).get()
    except Exception as e:
      print(e)
      value = False

    productos = eval(request.data['productos'])

    try:
      folio = Folio.objects.filter(empresa=compania_id,is_active=True,vencido=False,tipo_de_documento=33).order_by('fecha_de_autorizacion').first()

      if not folio:
        raise Folio.DoesNotExist

    except Folio.DoesNotExist:  
      messages.error(self.request, "No posee folios para asignacion de timbre")
      value = False
    try:
      folio.verificar_vencimiento()
    except ElCAFSenEncuentraVencido:
      messages.error(self.request, "El CAF se encuentra vencido")
      value = False

    try:
      response_dd = Factura._firmar_dd(data, folio, form)
      documento_firmado = Factura.firmar_documento(response_dd,data,folio, compania, form, pass_certificado)
      documento_final_firmado = Factura.firmar_etiqueta_set_dte(compania, folio, documento_firmado,form)
      caratula_firmada = Factura.generar_documento_final(compania,documento_final_firmado,pass_certificado)
      form.dte_xml = caratula_firmada
    except Exception as e:
      value = False

    etiqueta = slug.replace('º','')
    try:
      xml_dir = settings.MEDIA_ROOT +'facturas'+'/'+etiqueta
      if(not os.path.isdir(xml_dir)):
          os.makedirs(settings.MEDIA_ROOT +'facturas'+'/'+etiqueta)
      f = open(xml_dir+'/'+etiqueta+'.xml','w')
      f.write(caratula_firmada)
      f.close()
    except Exception as e:
      value = False

    return Response({"response":value})