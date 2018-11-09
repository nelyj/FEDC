from django.contrib import messages
from django.views.generic.edit import FormView
from django.shortcuts import render
from django.views.generic.base import TemplateView
import mysql.connector
import requests
from requests import Request, Session
import json

class ListaFacturasViews(TemplateView):
    """!
    Show the start of the platform

    @author Ing. Leonel P. Hernandez M. (lhernandez at analiticom.com)
    @author Ing. Luis Barrios (lbarrios at analiticom.com)
    @author Ing. Octavio Torres (otorres at analiticom.com)
    @copyright ANALITICOM
    @date 12-04-2018
    @version 1.0.0
    """
    template_name = 'lista_facturas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = requests.Session()
        payload = "{\"usr\":\"luis.be@timg.cl\",\"pwd\":\"Yayu115.\"\n}"
        headers = {'content-type': "application/json"}
        response = session.get('http://erp.timg.cl/api/method/login',data=payload,headers=headers)
        lista = session.get('http://erp.timg.cl/api/resource/Sales%20Invoice/')
        context['invoices'] = json.loads(lista.text)
        url='http://erp.timg.cl/api/resource/Sales%20Invoice/'
        #print(type(context['invoices']))
        #print(context['invoices']['data'])
        context['detail']=[]
        for tmp in  context['invoices']['data']:
            aux1=url+str(tmp['name'])
            #print(aux1)
            aux=session.get(aux1)
            #print(aux.text,'')
            context['detail'].append(json.loads(aux.text))

    	# try:
    	# 	mydb = mysql.connector.connect(user='root', password='haydelis26',
    	# 		host='127.0.0.1',database='_1bd3e0294da19198')
    	# 	mycursor = mydb.cursor()
    	# 	mycursor.execute("SELECT * FROM `tabSales Invoice` ")
    	# 	myresult = mycursor.fetchall()
    	# 	print(myresult)
    	# 	for x in myresult:
    	# 		print(x)
    	# 	mydb.close()
    	# except Exception as e:
    	# 	print(e)
    	# 
        return context

class DeatailInvoice(TemplateView):
    """!
    Show the start of the platform

    @author Ing. Leonel P. Hernandez M. (lhernandez at analiticom.com)
    @author Ing. Luis Barrios (lbarrios at analiticom.com)
    @author Ing. Octavio Torres (otorres at analiticom.com)
    @copyright ANALITICOM
    @date 12-04-2018
    @version 1.0.0
    """
    template_name = 'detail_invoice.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = requests.Session()
        payload = "{\"usr\":\"luis.be@timg.cl\",\"pwd\":\"Yayu115.\"\n}"
        headers = {'content-type': "application/json"}
        response = session.get('http://erp.timg.cl/api/method/login',data=payload,headers=headers)
        url='http://erp.timg.cl/api/resource/Sales%20Invoice/'+str(kwargs['slug'])
        aux=session.get(url)
        aux=json.loads(aux.text)
        context['keys'] = list(aux['data'].keys())
        context['values'] = list(aux['data'].values())
        return context
