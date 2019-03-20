import codecs, dicttoxml, json, os, requests
from requests import Request, Session
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.http import FileResponse
from django.views.generic.edit import FormView
from django.shortcuts import render
from django.views.generic.base import TemplateView, View
from django.views.generic import ListView
from django.template.loader import render_to_string
from conectores.models import *
from conectores.forms import FormCompania
from conectores.models import *
from folios.models import Folio
from folios.exceptions import ElCafNoTieneMasTimbres, ElCAFSenEncuentraVencido
from utils.SIISdk import SII_SDK
from .forms import *
from .models import Factura

class SeleccionarEmpresaView(TemplateView):
    template_name = 'seleccionar_empresa.html'

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
                return HttpResponseRedirect(reverse_lazy('facturas:lista-enviadas', kwargs={'pk':empresa}))
            else:
                return HttpResponseRedirect(reverse_lazy('facturas:lista_facturas', kwargs={'pk':empresa}))
        else:
            return HttpResponseRedirect('/')

class ListaFacturasViews(TemplateView):
    template_name = 'lista_facturas.html'

    def dispatch(self, *args, **kwargs):

        compania = self.kwargs.get('pk')

        usuario = Conector.objects.filter(t_documento='33',empresa=compania).first()

        if not usuario:

            messages.info(self.request, "No posee conectores asociados a esta empresa")
            return HttpResponseRedirect(reverse_lazy('facturas:seleccionar-empresa'))

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
        lista = session.get(usuario.url_erp+'/api/resource/Sales%20Invoice/')
        erp_data = json.loads(lista.text)

        # Todas las facturas y boletas sin discriminacion 
        data = erp_data['data']

        # Consulta en la base de datos todos los numeros de facturas
        # cargadas por la empresa correspondiente para hacer una comparacion
        # con el ERP y eliminar las que ya se encuentran cargadas
        enviadas = [factura.numero_factura for factura in Factura.objects.filter(compania=compania).only('numero_factura')]
        
        # print(enviadas)

        # Elimina todas las boletas de la lista
        # y crea una nueva lista con todas las facturas 
        solo_facturas  = []
        for i , item in enumerate(data):

            if item['name'].startswith('Nº'):

                solo_facturas.append(item['name'])

        # Verifica si la factura que vienen del ERP 
        # ya se encuentran cargadas en el sistema
        # y en ese caso las elimina de la lista
        solo_nuevas = []
        for i , item in enumerate(solo_facturas):

            if not item in enviadas:

                solo_nuevas.append(item)

        # print(solo_nuevas)


        url=usuario.url_erp+'/api/resource/Sales%20Invoice/'
        context['detail']=[]
        for tmp in solo_nuevas:
            aux1=url+str(tmp)
            aux=session.get(aux1)
            context['detail'].append(json.loads(aux.text))
        session.close()
        return context

class DeatailInvoice(TemplateView):
    template_name = 'detail_invoice.html'

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

class SendInvoice(FormView):
    template_name = 'envio_sii.html'
    form_class =FormFactura

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

        return reverse_lazy('facturas:send-invoice', kwargs={'pk':id_,'slug':self.kwargs['slug']})

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
            return super().form_invalid(form)
        assert compania, "compania no existe"
        data['productos']=eval(data['productos'])

        # rut = self.request.POST.get('rut', None)
        # assert rut, "rut no existe"
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
            messages.info(self.request, str('Queda ')+str(disponibles)+str('folio disponible'))
        elif disponibles < 50:
            messages.info(self.request, str('Quedan ')+str(disponibles)+str('folios disponibles'))
        form.compania = compania
        
        form.save()
        response_dd = Factura._firmar_dd(data, folio, form)
        documento_firmado = Factura.firmar_documento(response_dd,data,folio, compania, form)
        documento_final_firmado = Factura.firmar_etiqueta_set_dte(compania, folio, documento_firmado)
        caratula_firmada = Factura.generar_documento_final(documento_final_firmado)

        form.dte_xml = caratula_firmada
        form.save()


        # print(form.created)
        # print(type(form.created))

        try:
            os.makedirs(settings.MEDIA_ROOT +'facturas'+'/'+self.kwargs['slug'])
            file = open(settings.MEDIA_ROOT+'facturas'+'/'+self.kwargs['slug']+'/'+self.kwargs['slug']+'.xml','w')
            file.write(caratula_firmada)
        except Exception as e:
            messages.error(self.request, 'Ocurrio el siguiente Error: '+str(e))
            return super().form_invalid(form)


        # print(response_dd)


        msg = "Se guardo en Base de Datos la factura con éxito"
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

    def send_invoice_sii(self):
        try:
            sii_sdk = SII_SDK()
            seed = sii_sdk.getSeed()
            print(seed)
            return True
        except Exception as e:
            print(e)
            return False

class FacturasEnviadasView(ListView):
    template_name = 'facturas_enviadas.html'


    def get_queryset(self):

        compania = self.kwargs.get('pk')

        return Factura.objects.filter(compania=compania).order_by('-created')
