from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic.base import TemplateView
from .views import *

app_name = 'notaCredito'
urlpatterns = [
    re_path(r'lista-nota-credito/(?P<pk>\d+)', ListaNotaCreditoViews.as_view(), name='lista_nota_credito'),
    re_path(r'^lista-nota-credito/empresa/$', SeleccionarEmpresaView.as_view(),name='seleccionar-empresa'),
    re_path(r'^invoice/(?P<slug>[a-zA-Z0-9º-]+)/$', DeatailInvoice.as_view(),name='detail-invoice'),
    re_path(r'^NC/(?P<pk>\d+)/enviadas/$', NotaCreditoEnviadasView.as_view(),name='lista-enviadas'),
    path('enviar-nota-credito/<int:pk>/<str:slug>/', SendInvoice.as_view(),name='send-invoice'),
]



