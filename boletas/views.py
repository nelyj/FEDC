import requests, dicttoxml, json, codecs, os
from requests import Request, Session
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView
from conectores.models import *
from conectores.forms import FormCompania
from conectores.models import *
from folios.models import Folio
from folios.exceptions import ElCafNoTieneMasTimbres, ElCAFSenEncuentraVencido

from .models import *
from .forms import *
from .tasks import massshippingBoletas


class SeleccionarEmpresaView(LoginRequiredMixin, TemplateView):
    template_name = 'seleccionar_empresa_boleta.html'

    def get_context_data(self, *args, **kwargs): 

        context = super().get_context_data(*args, **kwargs)
        context['empresas'] = Compania.objects.filter(owner=self.request.user)
        if Compania.objects.filter(owner=self.request.user).exists():
            context['tiene_empresa'] = True
        else:
            messages.info(self.request, "Registre una empresa para continuar")
            context['tiene_empresa'] = False
        return context

    def post(self, request):

        enviadas = self.request.POST.get('enviadas', None)

        # print(enviadas)
        # enviadas = int(enviadas)

        empresa = int(request.POST.get('empresa'))
        if not empresa:
            return HttpResponseRedirect('/')
        empresa_obj = Compania.objects.get(pk=empresa)
        if empresa_obj and self.request.user == empresa_obj.owner:
            if enviadas == "1":
                return HttpResponseRedirect(reverse_lazy('boletas:lista-enviadas', kwargs={'pk':empresa}))
            else:
                return HttpResponseRedirect(reverse_lazy('boletas:lista_boletas', kwargs={'pk':empresa}))
        else:
            return HttpResponseRedirect('/')



class ListaBoletasViews(LoginRequiredMixin, TemplateView):
    template_name = 'lista_boletas.html'

    def dispatch(self, *args, **kwargs):

        compania = self.kwargs.get('pk')

        usuario = Conector.objects.filter(t_documento='39',empresa=compania).first()

        if not usuario:

            messages.info(self.request, "No posee conectores asociados a esta empresa")
            return HttpResponseRedirect(reverse_lazy('boletas:seleccionar-empresa'))

        return super().dispatch(*args, **kwargs)
            

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = requests.Session()
        compania = self.kwargs.get('pk')
        context['id_empresa'] = compania

        try:
            usuario = Conector.objects.filter(t_documento='39',empresa=compania).first()
        except Exception as e:
            messages.info(self.request, "No posee conectores asociados a esta empresa")
            return HttpResponseRedirect(reverse_lazy('boletas:seleccionar-empresa'))

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
        enviadas = [factura.numero_factura for factura in Boleta.objects.filter(compania=compania).only('numero_factura')]
        

        # Elimina todas las boletas de la lista
        # y crea una nueva lista con todas las facturas 
        solo_facturas  = []
        for i , item in enumerate(data):

            if item['name'].startswith('BOL'):

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
    template_name = 'detail_boleta.html'

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
        url=usuario.url_erp+'/api/resourfce/Sales%20Invoice/'+str(kwargs['slug'])
        aux=session.get(url)
        session.close()
        aux=json.loads(aux.text)
        xml = dicttoxml.dicttoxml(aux)
        context['keys'] = list(aux['data'].keys())
        context['values'] = list(aux['data'].values())
        return context

class BoletasEnviadasView(LoginRequiredMixin, ListView):
    template_name = 'boletas_enviadas.html'


    def get_queryset(self):

        compania = self.kwargs.get('pk')
        return Boleta.objects.filter(compania=compania).order_by('-created')

class SendInvoice(LoginRequiredMixin, FormView):
    template_name = 'envio_sii.html'
    form_class = FormBoleta

    def get_form_kwargs(self):
        kwargs = super(SendInvoice, self).get_form_kwargs()
        kwargs.update({'compania': self.kwargs['pk']})
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        session = requests.Session()
        url = self.kwargs['slug']
        compania = self.kwargs['pk']

        try:
            usuario = Conector.objects.filter(t_documento='39',empresa=compania).first()
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
            initial['comuna']=context['factura']['comuna']
        except Exception as e:
            initial['comuna']=""
        try:
            initial['ciudad_receptora']=context['factura']['ciudad_receptora']
        except Exception as e:
            initial['ciudad_receptora']=""
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
        try:
            initial['orden_compra']=context['factura']['po_no']
        except Exception as e:
            initial['orden_compra']=""
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

        return reverse_lazy('boletas:lista_boletas', kwargs={'pk':id_})

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

        # if form.cleaned_data['status'] == 'En proceso':
        data = form.clean()
        
        try:
            compania = Compania.objects.get(pk=compania_id)
        except Compania.DoesNotExist:
            messages.error(self.request, "No ha seleccionado la compania")
            return super().form_valid(form)
        assert compania, "compania no existe"

        pass_certificado = compania.pass_certificado
        
        data['productos']=eval(data['productos'])

        # rut = self.request.POST.get('rut', None)
        # assert rut, "rut no existe"
        form = form.save(commit=False)
        try:
            folio = Folio.objects.filter(empresa=compania_id,is_active=True,vencido=False,tipo_de_documento=39).order_by('fecha_de_autorizacion').first()

            if not folio:
                raise Folio.DoesNotExist

        except Folio.DoesNotExist:  
            messages.error(self.request, "No posee folios para asignacion de timbre")
            return super().form_valid(form)
        try:
            
            folio.verificar_vencimiento()
        except ElCAFSenEncuentraVencido:
            messages.error(self.request, "El CAF se encuentra vencido")
            return super().form_valid(form)
        form.status = 'TIMBRADO'
        try:
            form.recibir_folio(folio)
        except (ElCafNoTieneMasTimbres, ValueError):
            messages.error(self.request, "Ya ha consumido todos sus timbres")
            return super().form_valid(form)
        disponibles = folio.get_folios_disponibles()
        if disponibles == 1:
            messages.success(self.request, "Boleta generada exitosamente")
            messages.info(self.request, str('Queda ')+str(disponibles)+str('folio disponible'))
        elif disponibles < 50:
            messages.success(self.request, "Boleta generada exitosamente")
            messages.info(self.request, str('Quedan ')+str(disponibles)+str('folios disponibles'))
        else:
            messages.success(self.request, "Boleta generada exitosamente")
        form.compania = compania
       
        try:
            response_dd = Boleta._firmar_dd(data, folio, form)
            documento_firmado = Boleta.firmar_documento(response_dd,data,folio, compania, form, pass_certificado)
            form.dte_xml = documento_firmado
        except Exception as e:
            messages.error(self.request, "Ocurrió un error al firmar el documento")
            return super().form_valid(form)
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, form.errors)
        return super().form_invalid(form)

from django.core.serializers import serialize
class EnvioMasivo(LoginRequiredMixin, View):
    """!
    Class that allows to send massive document of Boletas

    @author Ing. Luis Barrios (nikeven at gmail.com)
    @author Rodrigo Boet (rudmanmrrod at gmail.com)
    @date 22-04-2019
    @version 1.0.0
    """

    def get(self, request, **kwargs):
        try:
            compania_id = self.request.GET.get('pk')
            object_states = Boleta.objects.filter(compania_id=compania_id).exclude(status='ENVIADA')
            if(not object_states.exists()):
                messages.warning(self.request, "No posee boletas para enviar")
                return JsonResponse(False, safe=False)
            
            folio = Folio.objects.filter(empresa=compania_id,is_active=True,vencido=False,tipo_de_documento=39).order_by('fecha_de_autorizacion').first()
            if folio is None:
                messages.error(self.request, "No posee folios para asignacion de timbre")
                return JsonResponse(False, safe=False)

            else:
                massshippingBoletas.apply_async(args=[compania_id])
                messages.success(self.request, "Se activo el proceso de envio masivo de boletas")
                return JsonResponse(True, safe=False)
            
        except Exception as e:
            messages.error(self.request, 'Ocurrio el siguiente Error: '+str(e))
            return JsonResponse(False, safe=False)
