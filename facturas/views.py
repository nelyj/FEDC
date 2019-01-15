from django.contrib import messages
from django.views.generic.edit import FormView
from django.shortcuts import render
from django.views.generic.base import TemplateView
import mysql.connector
import requests
from requests import Request, Session
import dicttoxml
import json
from django.template.loader import render_to_string
from django.http import HttpResponse
from conectores.models import *
import codecs
from conectores.forms import FormCompania
from conectores.models import *
from django.http import HttpResponse
from .forms import *
from django.urls import reverse_lazy
from multi_form_view import MultiModelFormView
from folios.models import Folio
from folios.exceptions import ElCafNoTieneMasTimbres

class ListaFacturasViews(TemplateView):
    template_name = 'lista_facturas.html'

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
        lista = session.get(usuario.url_erp+'/api/resource/Sales%20Invoice/')
        context['invoices'] = json.loads(lista.text)
        url=usuario.url_erp+'/api/resource/Sales%20Invoice/'
        context['detail']=[]
        for tmp in  context['invoices']['data']:
            aux1=url+str(tmp['name'])
            aux=session.get(aux1)
            context['detail'].append(json.loads(aux.text))
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
        aux=json.loads(aux.text)
        xml = dicttoxml.dicttoxml(aux)
        context['keys'] = list(aux['data'].keys())
        context['values'] = list(aux['data'].values())
        return context

# class SendInvoice(FormView):
#     # template_name = 'modal_XML.html'

#     # def get(self, request, **kwargs):
#     #     xml = render_to_string('invoice.xml', {'query_set': kwargs['slug']})
#     #     return HttpResponse(xml)
#     form_class = FormFactura
#     template_name = 'envio_sii.html'
#     model = Factura

#     def get_success_url(self):
#         return reverse_lazy('facturas:send-invoice', kwargs={'slug': self.request.get_full_path().split('/')[2].replace('%C2%BA','º')})

#     def get_context_data(self, **kwargs):
#         url=self.request.get_full_path().split('/')[2]
#         context = super().get_context_data(**kwargs)
#         session = requests.Session()
#         try:
#             usuario = Conector.objects.filter(pk=1).first()
#         except Exception as e:
#             print(e)
#         payload = "{\"usr\":\"%s\",\"pwd\":\"%s\"\n}" % (usuario.usuario, usuario.password)
#         headers = {'content-type': "application/json"}
#         response = session.get(usuario.url_erp+'/api/method/login',data=payload,headers=headers)
#         url=usuario.url_erp+'/api/resource/Sales%20Invoice/'+url
#         aux=session.get(url)
#         aux=json.loads(aux.text)
#         context['factura'] = dict(zip(aux['data'].keys(), aux['data'].values()))
#         context['factura']['sales_team'] = context['factura']['sales_team'][0]['sales_person']
#         context['factura']['total_taxes_and_charges'] = round(abs(float(context['factura']['total_taxes_and_charges'])))
#         # regiones=json.load(codecs.open('static/fixtures/comunas.json', 'r', 'utf-8-sig'))
#         try:
#             record = Compania.objects.filter(pk=1).first()
#             if record:
#                 # datetime.strftime(record.fecha_resolucion,"%d/%m/%Y")
#                 # record.fecha_resolucion.strftime("%Y/%m/%d")
#                 # datetime.strptime(record.fecha_resolucion, "%d/%m/%Y")
#                 form = FormCompania(instance=record)
#             else:
#                 form = FormCompania()
#             context['compania'] = form
#         except Exception as e:
#             raise e        
#         return context

#     def form_valid(self,form):
#         print(self.request.POST)
#         return super().form_valid(form)
#     def form_invalid(self, form):
#         return super().form_invalid(form)

class SendInvoice(FormView):
    template_name = 'envio_sii.html'
    form_class =FormFactura
    
    def get_success_url(self):
        return reverse_lazy('facturas:send-invoice', kwargs={'slug': self.request.get_full_path().split('/')[2].replace('%C2%BA','º')})

    def get_context_data(self, **kwargs):
        url=self.request.get_full_path().split('/')[2]
        context = super().get_context_data(**kwargs)
        session = requests.Session()
        try:
            usuario = Conector.objects.filter(pk=1).first()
        except Exception as e:
            print(e)
        payload = "{\"usr\":\"%s\",\"pwd\":\"%s\"\n}" % (usuario.usuario, usuario.password)
        headers = {'content-type': "application/json"}
        response = session.get(usuario.url_erp+'/api/method/login',data=payload,headers=headers)
        url=usuario.url_erp+'/api/resource/Sales%20Invoice/'+url
        aux=session.get(url)
        aux=json.loads(aux.text)
        context['factura'] = dict(zip(aux['data'].keys(), aux['data'].values()))
        context['factura']['sales_team'] = context['factura']['sales_team'][0]['sales_person']
        context['factura']['total_taxes_and_charges'] = round(abs(float(context['factura']['total_taxes_and_charges'])))
        # self.form_class.base_fields['compania'].initial=context['factura']['']
        try:
            self.form_class.base_fields['status'].initial = context['factura']['status_sii']
        except Exception as e:
            self.form_class.base_fields['status'].initial =""
        self.form_class.base_fields['numero_factura'].initial=self.kwargs['slug']
        try:
            self.form_class.base_fields['senores'].initial=context['factura']['customer_name']
        except Exception as e:
            self.form_class.base_fields['senores'].initial=""
        try:
            self.form_class.base_fields['direccion'].initial=context['factura']['customer_address']
        except Exception as e:
            self.form_class.base_fields['direccion'].initial=""
        try:
            self.form_class.base_fields['transporte'].initial=context['factura']['transporte']
        except Exception as e:
            self.form_class.base_fields['transporte'].initial=""
        try:
            self.form_class.base_fields['despachar'].initial=context['factura']['despachar_a']
        except Exception as e:
            self.form_class.base_fields['despachar'].initial=""
        try:
            self.form_class.base_fields['observaciones'].initial=context['factura']['observaciones']
        except Exception as e:
            self.form_class.base_fields['observaciones'].initial=""
        try:
            self.form_class.base_fields['giro'].initial=context['factura']['giro']
        except Exception as e:
            self.form_class.base_fields['giro'].initial=""
        # self.form_class.base_fields['condicion_venta'].initial=context['factura']['']
        # self.form_class.base_fields['vencimiento'].initial=context['factura']['']
        try:
            self.form_class.base_fields['vendedor'].initial=context['factura']['sales_team']
        except Exception as e:
            self.form_class.base_fields['vendedor'].initial=""
        try:
            self.form_class.base_fields['rut'].initial=context['factura']['rut']
        except Exception as e:
            self.form_class.base_fields['rut'].initial=""
        try:
            self.form_class.base_fields['fecha'].initial=context['factura']['posting_date']
        except Exception as e:
            self.form_class.base_fields['fecha'].initial=""
        # self.form_class.base_fields['guia'].initial=context['factura']['']
        # self.form_class.base_fields['orden_compra'].initial=context['factura']['']
        try:
            self.form_class.base_fields['nota_venta'].initial=context['factura']['orden_de_venta']
        except Exception as e:
            self.form_class.base_fields['nota_venta'].initial=""
        try:
            self.form_class.base_fields['productos'].initial=context['factura']['items']
        except Exception as e:
            self.form_class.base_fields['productos'].initial=""
        try:
            self.form_class.base_fields['monto_palabra'].initial=context['factura']['in_words']
        except Exception as e:
            self.form_class.base_fields['monto_palabra'].initial=""
        try:
            self.form_class.base_fields['neto'].initial=context['factura']['net_total']
        except Exception as e:
            self.form_class.base_fields['neto'].initial=""
        # self.form_class.base_fields['excento'].initial=context['factura']['']
        try:
            self.form_class.base_fields['iva'].initial=context['factura']['total_taxes_and_charges']
        except Exception as e:
            self.form_class.base_fields['iva'].initial=""
        try:
            self.form_class.base_fields['total'].initial=context['factura']['rounded_total']
        except Exception as e:
            self.form_class.base_fields['total'].initial=""
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
        rut = self.request.POST.get('rut', None)
        assert rut, "rut no existe"
        try:

            compania = Compania.objects.get(rut=rut)
        except Compania.DoesNotExist:

            messages.error(self.request, "No ha seleccionado la compania")
            return super().form_invalid(form)

        assert compania, "compania no existe"

        # if form.cleaned_data['status'] == 'En proceso':
        form = form.save(commit=False)
        try:
            folio = Folio.objects.get(empresa=compania,is_active=True,tipo_de_documento=33)
            print(folio)

        except Folio.DoesNotExist:  

            messages.error(self.request, "No posee folios para asignacion de timbre")
            return super().form_invalid(form)

        form.status = 'Aprobado'
        try:
            form.recibir_folio(folio)
        except (ElCafNoTieneMasTimbres, ValueError):

            messages.error(self.request, "Ya ha consumido todos sus timbres")
            return super().form_invalid(form)


        form.save()
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
        # else:
        #     msg = "La factura %s ya se encuentra almacenada en la base de datos del Faturador" % (self.kwargs['slug'])

        messages.info(self.request, msg)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, form.errors)
        return super().form_invalid(form)