"""
Facturador TIMG
@package factura.viewset

Router del api de Rest Framework
@copyright TIMG
@version 1.0
"""
import os
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

  def create(self, request, rut, slug):
    value = True
    fact_obj = Factura()
    factura = dict(zip(request.data['data'].keys(), request.data['data'].values()))
    factura['sales_team'] = factura['sales_team'][0]['sales_person']
    factura['total_taxes_and_charges'] = round(abs(float(factura['total_taxes_and_charges'])))
    factura['productos'] = factura['items']
    factura['neto'] = factura['net_total']
    factura['numero_factura'] = slug
    fact_obj.numero_factura = slug
    try:
        fact_obj.status = factura['status_sii']
    except Exception as e:
        fact_obj.status = ""
    try:
        fact_obj.senores = factura['customer_name']
    except Exception as e:
        fact_obj.senores = ""
    try:
        fact_obj.direccion = factura['customer_address']
    except Exception as e:
        fact_obj.direccion = ""
    try:
        fact_obj.comuna = factura['comuna']
    except Exception as e:
        fact_obj.comuna = ""
    try:
        fact_obj.ciudad_receptora = factura['ciudad_receptora']
    except Exception as e:
        fact_obj.ciudad_receptora = ""
    try:
        fact_obj.transporte = factura['transporte']
    except Exception as e:
        fact_obj.transporte = ""
    try:
        fact_obj.despachar = factura['despachar_a']
    except Exception as e:
        fact_obj.despachar = ""
    try:
        fact_obj.observaciones = factura['observaciones']
    except Exception as e:
        fact_obj.observaciones = ""
    try:
        fact_obj.giro = factura['giro']
    except Exception as e:
        fact_obj.giro = ""
    try:
        fact_obj.vendedor = factura['sales_team']
    except Exception as e:
        fact_obj.vendedor = ""
    try:
        fact_obj.rut = factura['rut']
    except Exception as e:
        fact_obj.rut = ""
    try:
        fact_obj.fecha = factura['posting_date']
    except Exception as e:
        fact_obj.fecha = ""
    try:
        fact_obj.orden_compra = factura['po_no']
    except Exception as e:
        fact_obj.orden_compra = ""
    try:
        fact_obj.nota_venta = factura['orden_de_venta']
    except Exception as e:
        fact_obj.nota_venta = ""
    try:
        fact_obj.productos = factura['productos']
    except Exception as e:
        fact_obj.productos = ""
    try:
        fact_obj.monto_palabra = factura['in_words']
    except Exception as e:
        fact_obj.monto_palabra = ""
    try:
        fact_obj.neto = factura['neto']
    except Exception as e:
        fact_obj.neto = ""
    try:
        fact_obj.iva = factura['total_taxes_and_charges']
    except Exception as e:
        fact_obj.iva = ""
    try:
        fact_obj.total = factura['rounded_total']
    except Exception as e:
        fact_obj.total = ""

    try:
      compania = Compania.objects.get(razon_social=rut)
    except Exception as e:
      print(e)
      value = False
      return Response({"response":value,"message":"Ocurrió un error con los conectores"})

    try:
      folio = Folio.objects.filter(empresa=compania.pk,is_active=True,vencido=False,tipo_de_documento=33).order_by('fecha_de_autorizacion').first()

      if not folio:
        raise Folio.DoesNotExist

    except Folio.DoesNotExist:  
      value = False
      return Response({"response":value,"message":"No posee folios para asignacion de timbre"})
    try:
      folio.verificar_vencimiento()
    except ElCAFSenEncuentraVencido:
      value = False
      return Response({"response":value,"message":"El CAF se encuentra vencido"})

    try:
      response_dd = Factura._firmar_dd(factura, folio, fact_obj)
      documento_firmado = Factura.firmar_documento(response_dd,factura,folio, compania, fact_obj, compania.pass_certificado)
      documento_final_firmado = Factura.firmar_etiqueta_set_dte(compania, folio, documento_firmado,fact_obj)
      caratula_firmada = Factura.generar_documento_final(compania,documento_final_firmado,compania.pass_certificado)
      fact_obj.dte_xml = caratula_firmada
    except Exception as e:
      print(e)
      value = False
      return Response({"response":value,"message":"Ocurrió un error al generar el xml"})

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
      return Response({"response":value,"message":"Ocurrió un error al crear el xml"})
    fact_obj.save()

    return Response({"response":value,"message":"Se creo la factura con éxito"})