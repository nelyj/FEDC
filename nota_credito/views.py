import OpenSSL.crypto
import codecs, dicttoxml, json, os, requests
from collections import OrderedDict
from requests import Request, Session
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.http import FileResponse
from django.views.generic.edit import FormView
from django.shortcuts import (
    render, redirect
    )
from django.views.generic.base import TemplateView, View
from django.views.generic import ListView, CreateView
from django.template.loader import render_to_string
from django_weasyprint import WeasyTemplateResponseMixin

from base.constants import NOMB_DOC, LIST_DOC

from conectores.models import *
from conectores.forms import FormCompania
from conectores.models import *
from conectores.models import Compania

from folios.models import Folio
from folios.exceptions import ElCafNoTieneMasTimbres, ElCAFSenEncuentraVencido

from utils.SIISdk import SII_SDK
from utils.utils import validarModelPorDoc
from utils.CustomMixin import SeleccionarEmpresaView

from .models import notaCredito
from .forms import *


class StartNotaCredito(SeleccionarEmpresaView):
    """
    Selecciona la empresa

    @author Rodrigo A. Boet (rodrigo.b at timgla.com)
    @date 12-08-2019
    @version 1.0.0
    """

    def post(self, request):
        enviadas = self.request.GET.get('enviadas', None)
        sistema = self.request.GET.get('sistema', None)
        empresa = int(request.POST.get('empresa'))
        if not empresa:
            return HttpResponseRedirect('/')
        empresa_obj = Compania.objects.get(pk=empresa)
        if empresa_obj and self.request.user == empresa_obj.owner:
            if sistema:
                return HttpResponseRedirect(reverse_lazy('notaCredito:nota_sistema_listado', kwargs={'pk':empresa}))
            else:
                if enviadas == "1":
                    return HttpResponseRedirect(reverse_lazy('notaCredito:lista-enviadas', kwargs={'pk':empresa}))
                else:
                    return HttpResponseRedirect(reverse_lazy('notaCredito:lista_nota_credito', kwargs={'pk':empresa}))
        else:
            return HttpResponseRedirect('/')


class ListaNotaCreditoViews(LoginRequiredMixin, TemplateView):
    template_name = 'lista_NC.html'

    def dispatch(self, *args, **kwargs):

        compania = self.kwargs.get('pk')

        usuario = Conector.objects.filter(t_documento='33',empresa=compania).first()

        if not usuario:

            messages.info(self.request, "No posee conectores asociados a esta empresa")
            return HttpResponseRedirect(reverse_lazy('notaCredito:seleccionar-empresa'))

        return super().dispatch(*args, **kwargs)
            

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = requests.Session()
        compania = self.kwargs.get('pk')
        context['id_empresa'] = compania
        try:
            usuario = Conector.objects.filter(t_documento='33',empresa=compania).first()
        except Exception as e:

            print(e)

        payload = "{\"usr\":\"%s\",\"pwd\":\"%s\"\n}" % (usuario.usuario, usuario.password)

        headers = {'content-type': "application/json"}
        response = session.get(usuario.url_erp+'/api/method/login',data=payload,headers=headers)
        lista = session.get(usuario.url_erp+'/api/resource/Sales%20Invoice/?limit_page_length')
        erp_data = json.loads(lista.text)

        # Todas las facturas y boletas sin discriminacion 
        data = erp_data['data']

        # Consulta en la base de datos todos los numeros de facturas
        # cargadas por la empresa correspondiente para hacer una comparacion
        # con el ERP y eliminar las que ya se encuentran cargadas
        enviadas = [factura.numero_factura for factura in notaCredito.objects.filter(compania=compania).only('numero_factura')]
        # Elimina todas las boletas de la lista
        # y crea una nueva lista con todas las facturas 
        solo_facturas  = []
        for i , item in enumerate(data):

            if item['name'].startswith('NC'):

                solo_facturas.append(item['name'])
        # Verifica si la factura que vienen del ERP 
        # ya se encuentran cargadas en el sistema
        # y en ese caso las elimina de la lista
        solo_nuevas = []
        for i , item in enumerate(solo_facturas):
            if not item in enviadas:
                solo_nuevas.append(item)
        url=usuario.url_erp+'/api/resource/Sales%20Invoice/'
        context['detail']=[]
        for tmp in solo_nuevas:
            aux1=url+str(tmp)
            aux=session.get(aux1)
            context['detail'].append(json.loads(aux.text))
        session.close()
        return context

class DeatailInvoice(LoginRequiredMixin, TemplateView):
    template_name = 'detail_NC.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = requests.Session()
        try:
            usuario = Conector.objects.filter(pk=1).first()
        except Exception as e:
            print(e)
        payload = "{\"usr\":\"%s\",\"pwd\":\"%s\"\n}" % (usuario.usuario, usuario.password)
        headers = {'content-type': "application/json"}
        response = session.get(usuario.url_erp+'/api/method/login',data=payload,headers=headers)
        url=usuario.url_erp+'/api/resource/Sales%20Invoice/'+str(kwargs['slug'])
        aux=session.get(url)
        session.close()
        aux=json.loads(aux.text)
        xml = dicttoxml.dicttoxml(aux)
        context['keys'] = list(aux['data'].keys())
        context['values'] = list(aux['data'].values())
        return context

class SendInvoice(LoginRequiredMixin, FormView):
    template_name = 'envio_sii_NC.html'
    form_class =FormNotaCredito

    def get_initial(self):
        initial = super().get_initial()
        session = requests.Session()
        url = self.kwargs['slug']
        compania = self.kwargs['pk']

        try:
            usuario = Conector.objects.filter(t_documento='33',empresa=compania).first()
        except Exception as e:
            print(e)
        payload = "{\"usr\":\"%s\",\"pwd\":\"%s\"\n}" % (usuario.usuario, usuario.password)
        headers = {'content-type': "application/json"}
        try:
            response = session.get(usuario.url_erp+'/api/method/login',data=payload,headers=headers)
        except Exception as e:
            messages.warning(self.request, "No se pudo establecer conexion con el ERP Next, se genera el siguiente error: "+str(e))
        url=usuario.url_erp+'/api/resource/Sales%20Invoice/'+url
        try:
            aux=session.get(url)
            session.close()
            aux=json.loads(aux.text)
            context={}
            context['factura'] = dict(zip(aux['data'].keys(), aux['data'].values()))
            context['factura']['sales_team'] = context['factura']['sales_team'][0]['sales_person']
            context['factura']['total_taxes_and_charges'] = round(abs(float(context['factura']['total_taxes_and_charges'])))
        except Exception as e:
            messages.warning(self.request, "No se pudo establecer conexion con el ERP Next, se genera el siguiente error: "+str(e))
        try:
            initial['status']= context['factura']['status_sii']
        except Exception as e:
            initial['status'] =""
        initial['numero_factura']=self.kwargs['slug']
        try:
            initial['senores']=context['factura']['customer_name']
        except Exception as e:
            initial['senores']=""
        try:
            initial['direccion']=context['factura']['customer_address']
        except Exception as e:
            initial['direccion']=""
        try:
            initial['transporte']=context['factura']['transporte']
        except Exception as e:
            initial['transporte']=""
        try:
            initial['despachar']=context['factura']['despachar_a']
        except Exception as e:
            initial['despachar']=""
        try:
            initial['observaciones']=context['factura']['observaciones']
        except Exception as e:
            initial['observaciones']=""
        try:
            initial['giro']=context['factura']['giro']
        except Exception as e:
            self.form_class.base_fields['giro'].initial=""
        # self.form_class.base_fields['condicion_venta'].initial=context['factura']['']
        # self.form_class.base_fields['vencimiento'].initial=context['factura']['']
        try:
            initial['vendedor']=context['factura']['sales_team']
        except Exception as e:
            initial['vendedor']=""
        try:
            initial['rut']=context['factura']['rut']
        except Exception as e:
            initial['rut']=""
        try:
            initial['fecha']=context['factura']['posting_date']
        except Exception as e:
            initial['fecha']=""
        # self.form_class.base_fields['guia'].initial=context['factura']['']
        # self.form_class.base_fields['orden_compra'].initial=context['factura']['']
        try:
            initial['nota_venta']=context['factura']['orden_de_venta']
        except Exception as e:
            initial['nota_venta']=""
        try:
            initial['productos']=context['factura']['items']
        except Exception as e:
            initial['productos']=""
        try:
            initial['monto_palabra']=context['factura']['in_words']
        except Exception as e:
            initial['monto_palabra']=""
        try:
            initial['neto']=context['factura']['net_total']
        except Exception as e:
            initial['neto']=""
        # self.form_class.base_fields['excento'].initial=context['factura']['']
        try:
            initial['iva']=context['factura']['total_taxes_and_charges']
        except Exception as e:
            initial['iva']=""
        try:
            initial['total']=context['factura']['rounded_total']
        except Exception as e:
            initial['total']=""
        return initial
    
    def get_success_url(self):

        id_ = self.kwargs.get('pk')

        return reverse_lazy('notaCredito:send-invoice', kwargs={'pk':id_,'slug':self.kwargs['slug']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = requests.Session()
        url = self.kwargs['slug']
        compania = self.kwargs['pk']

        try:
            usuario = Conector.objects.filter(pk=1).first()
        except Exception as e:
            print(e)
        payload = "{\"usr\":\"%s\",\"pwd\":\"%s\"\n}" % (usuario.usuario, usuario.password)
        headers = {'content-type': "application/json"}
        try:
            response = session.get(usuario.url_erp+'/api/method/login',data=payload,headers=headers)
        except Exception as e:
            messages.warning(self.request, "No se pudo establecer conexion con el ERP Next, se genera el siguiente error: "+str(e))
        url=usuario.url_erp+'/api/resource/Sales%20Invoice/'+url
        try:
            aux=session.get(url)
            session.close()
            aux=json.loads(aux.text)
            context['factura'] = dict(zip(aux['data'].keys(), aux['data'].values()))
        except Exception as e:
            messages.warning(self.request, "No se pudo establecer conexion con el ERP Next, se genera el siguiente error: "+str(e))
        try:
            record = Compania.objects.filter(pk=1).first()
            if record:
                form = FormCompania(instance=record)
            else:
                form = FormCompania()
            context['compania'] = form
        except Exception as e:
            raise e        
        return context

    def form_valid(self, form, **kwargs):
        compania_id = self.kwargs['pk']
        # pass_certificado = form.cleaned_data['pass_certificado']
        # if form.cleaned_data['status'] == 'En proceso':
        data = form.clean()
        print(data)
        try:
            compania = Compania.objects.get(pk=compania_id)
        except Compania.DoesNotExist:
            messages.error(self.request, "No ha seleccionado la compania")
            return super().form_invalid(form)
        assert compania, "compania no existe"
        pass_certificado = compania.pass_certificado
        data['productos']=eval(data['productos'])

        form = form.save(commit=False)
        try:
            folio = Folio.objects.filter(empresa=compania_id,is_active=True,vencido=False,tipo_de_documento=33).order_by('fecha_de_autorizacion').first()

            if not folio:
                raise Folio.DoesNotExist

        except Folio.DoesNotExist:  
            messages.error(self.request, "No posee folios para asignacion de timbre")
            return super().form_invalid(form)
        try:
            
            folio.verificar_vencimiento()
        except ElCAFSenEncuentraVencido:
            messages.error(self.request, "El CAF se encuentra vencido")
            return super().form_invalid(form)
        form.status = 'Aprobado'
        try:
            form.recibir_folio(folio)
        except (ElCafNoTieneMasTimbres, ValueError):
            messages.error(self.request, "Ya ha consumido todos sus timbres")
            return super().form_invalid(form)
        # Trae la cantidad de folios disponibles y genera una notificacion cuando quedan menos de 5
        # Si queda uno, cambia la estructura de la oracion a singular. 
        disponibles = folio.get_folios_disponibles()

        if disponibles == 1:
            messages.success(self.request, "Nota de crédito enviada exitosamente")
            messages.info(self.request, str('Queda ')+str(disponibles)+str('folio disponible'))
        elif disponibles < 50:
            messages.success(self.request, "Nota de crédito enviada exitosamente")
            messages.info(self.request, str('Quedan ')+str(disponibles)+str('folios disponibles'))
        else:
            messages.success(self.request, "Nota de crédito enviada exitosamente")
        form.compania = compania
        #form.save()

        try:
            response_dd = notaCredito._firmar_dd(data, folio, form)
            documento_firmado = notaCredito.firmar_documento(response_dd,data,folio, compania, form, pass_certificado)
            documento_final_firmado = notaCredito.firmar_etiqueta_set_dte(compania, folio, documento_firmado)
            caratula_firmada = notaCredito.generar_documento_final(compania,documento_final_firmado,pass_certificado)
            form.dte_xml = caratula_firmada
        except Exception as e:
            print(e)
            messages.error(self.request, "Ocurrió un error al firmar el documento")
            return super().form_valid(form)

        try:
            xml_dir = settings.MEDIA_ROOT +'notas_de_credito'+'/'+self.kwargs['slug']
            if(not os.path.isdir(xml_dir)):
                os.makedirs(xml_dir)
            f = open(xml_dir+'/'+self.kwargs['slug']+'.xml','w')
            f.write(caratula_firmada)
            f.close()
        except Exception as e:
            messages.error(self.request, 'Ocurrio el siguiente Error: '+str(e))
            return super().form_valid(form)

        send_sii = self.send_invoice_sii(compania,caratula_firmada,pass_certificado)
        if(not send_sii['estado']):
            messages.error(self.request, send_sii['msg'])
            return super().form_valid(form)
        else:
            form.track_id = send_sii['track_id']
            form.save()

        session = requests.Session()
        try:
            usuario = Conector.objects.filter(pk=1).first()
        except Exception as e:
            print(e)
        payload = "{\"usr\":\"%s\",\"pwd\":\"%s\"\n}" % (usuario.usuario, usuario.password)
        headers = {'content-type': "application/json"}
        response = session.get(usuario.url_erp+'/api/method/login',data=payload,headers=headers)
        url=usuario.url_erp+'/api/resource/Sales%20Invoice/'+self.kwargs['slug']
        aux=session.put(url,json={'status_sii':'Aprobado'})
        session.close()
        # else:
        #     msg = "La factura %s ya se encuentra almacenada en la base de datos del Faturador" % (self.kwargs['slug'])
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, form.errors)
        return super().form_invalid(form)

    def send_invoice_sii(self,compania,invoice, pass_certificado):
        """
        Método para enviar la factura al sii
        @param compania recibe el objeto compañia
        @param invoice recibe el xml de la factura
        @param pass_certificado recibe la contraseña del certificado
        @return dict con la respuesta
        """
        try:
            sii_sdk = SII_SDK(settings.SII_PRODUCTION)
            seed = sii_sdk.getSeed()
            try:
                sign = sii_sdk.signXml(seed, compania, pass_certificado)
                token = sii_sdk.getAuthToken(sign)
                if(token):
                    print(token)
                    try:
                        invoice_reponse = sii_sdk.sendInvoice(token,invoice,compania.rut,'60803000-K')
                        return {'estado':invoice_reponse['success'],'msg':invoice_reponse['message'],
                        'track_id':invoice_reponse['track_id']}
                    except Exception as e:
                        print(e)
                        return {'estado':False,'msg':'No se pudo enviar la factura'}    
                else:
                    return {'estado':False,'msg':'No se pudo obtener el token del sii'}
            except Exception as e:
                print(e)
                return {'estado':False,'msg':'Ocurrió un error al firmar el documento'}
            return {'estado':True}
        except Exception as e:
            print(e)
            return {'estado':False,'msg':'Ocurrió un error al comunicarse con el sii'}

class NotaCreditoEnviadasView(LoginRequiredMixin, TemplateView):
    template_name = 'NC_enviadas.html'


    def get_context_data(self, *args, **kwargs): 
        """
        Método para colocar contexto en la vista
        """
        context = super().get_context_data(*args, **kwargs)
        context['compania'] = self.kwargs.get('pk')
        return context


class VerEstadoNC(LoginRequiredMixin, TemplateView):
    """!
    Clase para ver el estado de envio de una factura

    @author Rodrigo Boet (rudmanmrrod at gmail.com)
    @date 04-04-2019
    @version 1.0.0
    """
    template_name = "estado_factura.html"
    model = notaCredito

    def get_context_data(self, *args, **kwargs):
        """!
        Method to handle data on get

        @date 04-04-2019
        @return Returns dict with data
        """
        context = super().get_context_data(*args, **kwargs)
        num_factura = self.kwargs['slug']
        compania = self.kwargs['pk']

        factura = self.model.objects.get(numero_factura=num_factura, compania=compania)
        context['factura'] = factura
        
        estado = self.get_invoice_status(factura,factura.compania,)

        if(not estado['estado']):
            messages.error(self.request, estado['msg'])
        else:
            context['estado'] = estado['status']
            context['glosa'] = estado['glosa']

        return context

    def get_invoice_status(self,factura,compania):
        """
        Método para enviar la factura al sii
        @param factura recibe el objeto de la factura
        @param compania recibe el objeto compañia
        @return dict con la respuesta
        """
        try:
            sii_sdk = SII_SDK(settings.SII_PRODUCTION)
            seed = sii_sdk.getSeed()
            try:
                sign = sii_sdk.signXml(seed, compania, compania.pass_certificado)
                token = sii_sdk.getAuthToken(sign)
                if(token):
                    print(token)
                    estado = sii_sdk.checkDTEstatus(compania.rut,factura.track_id,token)
                    return {'estado':True,'status':estado['estado'],'glosa':estado['glosa']} 
                else:
                    return {'estado':False,'msg':'No se pudo obtener el token del sii'}
            except Exception as e:
                print(e)
                return {'estado':False,'msg':'Ocurrió un error al firmar el documento'}
            return {'estado':True}
        except Exception as e:
            print(e)
            return {'estado':False,'msg':'Ocurrió un error al comunicarse con el sii'}

class NotaCreditoSistemaView(LoginRequiredMixin, TemplateView):
    """!
    Clase para ver el listado de notas del sistema

    @author Rodrigo Boet (rudmanmrrod at gmail.com)
    @date 13-09-2019
    @version 1.0.0
    """
    template_name = 'NC_enviadas.html'

    def get_context_data(self, *args, **kwargs): 
        """
        Método para colocar contexto en la vista
        """
        context = super().get_context_data(*args, **kwargs)
        context['sistema'] = True
        context['compania'] = self.kwargs.get('pk')
        return context

class NotaCreditoCreateView(LoginRequiredMixin, CreateView):
    """!
    Clase para generar una nota de crédito por el sistema

    @author Rodrigo Boet (rudmanmrrod at gmail.com)
    @date 13-09-2019
    @version 1.0.0
    """
    template_name = "nc_crear.html"
    model = notaCredito
    form_class = FormCreateNotaCredito
    success_url = 'nota_credito:nota_sistema_crear'

    def get_context_data(self, *args, **kwargs): 
        """
        Método para colocar contexto en la vista
        """
        context = super().get_context_data(*args, **kwargs)
        context['compania'] = self.kwargs.get('pk')
        context['impuesto'] = Compania.objects.get(pk=self.kwargs.get('pk')).tasa_de_iva
        if(self.request.method == 'POST'):
            dict_post = dict(self.request.POST.lists())
            productos = self.transform_product(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'])
            context['productos'] = productos
        return context

    def get_success_url(self):
        """
        Método para retornar la url de éxito
        """
        return reverse_lazy(self.success_url, kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form, **kwargs):
        """
        Método si el formulario es válido
        """

        dict_post = dict(self.request.POST.lists())
        datetime_object = datetime.datetime.now()
        fecha = datetime.datetime.strptime(dict_post['fecha'][0], '%d/%m/%Y')
        if 'codigo' not in self.request.POST or 'nombre' not in self.request.POST\
            or 'cantidad' not in self.request.POST or 'precio' not in self.request.POST:
            messages.error(self.request, "Debe cargar al menos un producto")
            return super().form_invalid(form)
        if(len(dict_post['codigo']) == 0 or len(dict_post['nombre']) == 0\
            or len(dict_post['cantidad']) == 0 or len(dict_post['precio']) == 0):
            messages.error(self.request, "Debe cargar al menos un producto")
            return super().form_invalid(form)
        if(len(dict_post['codigo']) != len(dict_post['nombre']) or\
            len(dict_post['cantidad']) != len(dict_post['precio']) or\
            len(dict_post['codigo']) != len(dict_post['cantidad']) or\
            len(dict_post['cantidad']) != len(dict_post['nombre'])):
            messages.error(self.request, "Faltan valores por llenar en la tabla")
            return super().form_invalid(form)

        if fecha > datetime_object:
            messages.error(self.request, "La fecha no puede ser mayor a la fecha actual, por favor verifica nuevamente la fecha")
            return super().form_invalid(form)
        valid_r = self.validateProduct(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'])
        if(not valid_r['valid']):
            messages.error(self.request, valid_r['msg'])
            return super().form_invalid(form)
        productos = self.transform_product(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'])
        compania = Compania.objects.get(pk=self.kwargs.get('pk'))
        pass_certificado = compania.pass_certificado
        diccionario_general = self.load_product(productos,compania)
        self.object = form.save(commit=False)
        diccionario_general['rut'] = self.object.rut
        diccionario_general['numero_factura'] = self.object.numero_factura
        diccionario_general['senores'] = self.object.senores
        diccionario_general['giro'] = self.object.giro
        diccionario_general['direccion'] = self.object.region
        diccionario_general['comuna'] = self.object.comuna
        try:
            diccionario_general['ciudad_receptora'] = self.object.ciudad_receptora
        except:
            pass
        diccionario_general['forma_pago'] = form.cleaned_data['forma_pago']
        # Se verifica el folio
        try:
            folio = Folio.objects.filter(empresa=self.kwargs.get('pk'),is_active=True,vencido=False,tipo_de_documento=33).order_by('fecha_de_autorizacion').first()
            if not folio:
                raise Folio.DoesNotExist
        except Folio.DoesNotExist:  
            messages.error(self.request, "No posee folios para asignacion de timbre")
            return super().form_invalid(form)
        try:
            folio.verificar_vencimiento()
        except ElCAFSenEncuentraVencido:
            messages.error(self.request, "El CAF se encuentra vencido")
            return super().form_invalid(form)
        try:
            self.object.recibir_folio(folio)
        except (ElCafNoTieneMasTimbres, ValueError):
            messages.error(self.request, "Ya ha consumido todos sus timbres")
            return super().form_invalid(form)
        self.object.productos = json.dumps(diccionario_general['productos'])
        # Se generan los XML
        response_dd = self.model._firmar_dd(diccionario_general, folio, self.object)
        documento_firmado = self.model.firmar_documento(response_dd,diccionario_general,folio, compania, self.object, pass_certificado)
        documento_final_firmado = self.model.firmar_etiqueta_set_dte(compania, folio, documento_firmado)
        caratula_firmada = self.model.generar_documento_final(compania,documento_final_firmado,pass_certificado)
        self.object.dte_xml = caratula_firmada
        self.object.neto = diccionario_general['neto']
        self.object.total = diccionario_general['total']
        self.object.iva = compania.tasa_de_iva
        self.object.compania = compania
        self.object.save()
        # Se crea el arhivo del xml
        try:
            xml_dir = settings.MEDIA_ROOT +'notas_de_credito'+'/'+self.object.numero_factura
            if(not os.path.isdir(xml_dir)):
                os.makedirs(xml_dir)
            f = open(xml_dir+'/'+self.object.numero_factura+'.xml','w')
            f.write(caratula_firmada)
            f.close()
        except Exception as e:
            messages.error(self.request, 'Ocurrio el siguiente Error: '+str(e))
            return super().form_valid(form)
        messages.success(self.request, "Se creó el documento con éxito")
        return super().form_valid(form)

    def form_invalid(self, form, **kwargs):
        """
        Método si el formulario es válido
        """
        return super().form_invalid(form)

    def transform_product(self, code, name, qty, price):
        """
        Método para transformar los productos en listas de diccionarios
        @param code Recibe la lista con los códigos
        @param name Recibe la lista con los nombres
        @param qty Recibe la lista con las cantidades
        @param price Recibe la lista con los precios
        @return retorna los productos como lista de diccionarios
        """
        products = []
        for i in range(len(code)):
            new_prod = {}
            new_prod['nombre'] = name[i]
            new_prod['codigo'] = code[i]
            new_prod['cantidad'] = int(qty[i])
            new_prod['precio'] = float(price[i])
            products.append(new_prod)
        return products

    def load_product(self, prod_dict, compania):
        """
        Método para armar el json de producto
        @param prod_dict Recibe el diccionarios de productos
        @param compania Recibe el objecto de la compañia
        @return retorna la data en un diccionario
        """
        total = 0
        products = []
        for producto in prod_dict:
            new_prod = OrderedDict()
            new_prod['item_name'] = producto['nombre']
            new_prod['description'] = producto['nombre']
            new_prod['item_code'] = producto['codigo']
            new_prod['qty'] = producto['cantidad']
            new_prod['base_net_rate'] = producto['precio']
            new_prod['amount'] = new_prod['qty'] * new_prod['base_net_rate']
            products.append(new_prod)
            total += new_prod['amount']
        neto = total - (total*(compania.tasa_de_iva/100))
        data = OrderedDict()
        data['productos'] = products
        data['neto'] = neto
        data['total'] = total
        return data

    def validateProduct(self, code, name, qty, price):
        """
        Método para validar el producto
        @param code Recibe la lista con los códigos
        @param name Recibe la lista con los nombres
        @param qty Recibe la lista con las cantidades
        @param price Recibe la lista con los precios
        @return retorna los productos como lista de diccionarios
        """
        for i in range(len(code)):
            for j in range(i+1,len(code)):
                if(code[i]==code[j]):
                    return {'valid':False,'msg':'No pueden existir códigos dúplicados'}
        for q in qty:
            try:
                int(q)
            except Exception as e:
                return {'valid':False,'msg':'Las cantidades deben ser enteras'}
        for p in price:
            try:
                float(p)
            except Exception as e:
                return {'valid':False,'msg':'El precio debe ser un número'}
        return {'valid':True}
