"""
Facturador TIMG
@package factura.viewset

Router del api de Rest Framework
@copyright TIMG
@version 1.0
"""
import re
import os

from django.conf import settings
from rest_framework import viewsets
from rest_framework.response import Response

from conectores.models import *
from folios.models import Folio
from folios.exceptions import ElCafNoTieneMasTimbres, ElCAFSenEncuentraVencido

from .models import DTE
from .views import SaveDteErp


class DteViewSet(viewsets.ViewSet):
    """
    Clase para la vista en rest de la factura
    @author Rodrigo Boet (rodrigoale.b at timg.cl)
    @copyright TIMG
    @date 07-01-2020 (dd-mm-YY)
    @version 1.0
    """
    save_dte = SaveDteErp()

    def create(self, request, rut, slug):
        value = True
        dte_obj = DTE()
        dte = dict(zip(request.data['data'].keys(), request.data['data'].values()))
        dte['total_taxes_and_charges'] = round(abs(float(dte['total_taxes_and_charges'])))
        dte['productos'] = dte['items']
        dte['neto'] = dte['net_total']
        dte['numero_factura'] = slug
        valor = re.sub('[^a-zA-Z0-9 \n\.]', '', dte['numero_factura'])
        valor = valor.replace(' ', '')
        dte_obj.numero_factura = valor
        tipo_dte = self.save_dte.type_dte(dte.get('tipo_de_documento', None))
        dte_obj.tipo_dte = tipo_dte
        try:
            dte_obj.status = dte['status_sii']
        except Exception as e:
            dte_obj.status = ""
        try:
            dte_obj.senores = dte['customer_name']
        except Exception as e:
            dte_obj.senores = ""
        try:
            dte_obj.direccion = dte['customer_address']
        except Exception as e:
            dte_obj.direccion = ""
        try:
            dte_obj.comuna = dte['comuna']
        except Exception as e:
            dte_obj.comuna = ""
        try:
            dte_obj.ciudad_receptora = dte['ciudad_receptora']
        except Exception as e:
            dte_obj.ciudad_receptora = ""
        '''
        try:
            dte_obj.transporte = dte['transporte']
        except Exception as e:
            dte_obj.transporte = ""
        try:
            dte_obj.despachar = dte['despachar_a']
        except Exception as e:
            dte_obj.despachar = ""
        try:
            dte_obj.observaciones = dte['observaciones']
        except Exception as e:
            dte_obj.observaciones = ""
        '''
        try:
            dte_obj.giro = dte['giro']
        except Exception as e:
            dte_obj.giro = ""
        '''
        try:
            dte['sales_team'] = dte['sales_team'][0]['sales_person']
            dte_obj.vendedor = dte['sales_team']
        except Exception as e:
            dte_obj.vendedor = ""
        '''
        try:
            dte_obj.rut = dte['rut']
        except Exception as e:
            dte_obj.rut = ""
        try:
            dte_obj.fecha = dte['posting_date']
        except Exception as e:
            dte_obj.fecha = ""
        '''
        try:
            dte_obj.orden_compra = dte['po_no']
        except Exception as e:
            dte_obj.orden_compra = ""
        try:
            dte_obj.nota_venta = dte['orden_de_venta']
        except Exception as e:
            dte_obj.nota_venta = ""
        '''
        try:
            dte_obj.productos = dte['productos']
        except Exception as e:
            dte_obj.productos = ""
        '''
        try:
            dte_obj.monto_palabra = dte['in_words']
        except Exception as e:
            dte_obj.monto_palabra = ""
        '''
        try:
            dte_obj.neto = dte['neto']
        except Exception as e:
            dte_obj.neto = ""
        try:
            dte_obj.iva = dte['total_taxes_and_charges']
        except Exception as e:
            dte_obj.iva = ""
        try:
            dte_obj.total = dte['rounded_total']
        except Exception as e:
            dte_obj.total = ""
        try:
            compania = Compania.objects.get(rut=rut)
        except Exception as e:
            print(e)
            value = False
            return Response({"response":value,"message":"Ocurrió un error con los conectores"})
        try:
            folio = Folio.objects.filter(empresa=compania.pk,is_active=True,vencido=False,tipo_de_documento=tipo_dte).order_by('fecha_de_autorizacion').first()
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
            response_dd = DTE._firmar_dd(dte, folio, dte_obj)
            documento_firmado = DTE.firmar_documento(response_dd,dte,folio, compania, fact_obj, compania.pass_certificado)
            documento_final_firmado = DTE.firmar_etiqueta_set_dte(compania, folio, documento_firmado,fact_obj)
            caratula_firmada = DTE.generar_documento_final(compania,documento_final_firmado,compania.pass_certificado)
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
        return Response({"response":value,"message":"Se creo el DTE con éxito"})
