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

class SendInvoice(TemplateView):
    template_name = 'modal_XML.html'

    def get(self, request, **kwargs):
        xml = render_to_string('invoice.xml', {'query_set': kwargs['slug']})
        return HttpResponse(xml)
