from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic.base import TemplateView
from .views import *

app_name = 'facturas'
urlpatterns = [
    path('lista-facturas/', ListaFacturasViews.as_view(), name='lista_facturas'),
    re_path(r'^invoice/(?P<slug>[a-zA-Z0-9º-]+)/$', DeatailInvoice.as_view(),name='detail-invoice'),
    re_path(r'^enviar-factura/(?P<slug>[a-zA-Z0-9º-]+)/$', SendInvoice.as_view(),name='send-invoice'),
]