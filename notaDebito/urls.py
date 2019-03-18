from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic.base import TemplateView
from .views import *

app_name = 'notaDebito'
urlpatterns = [
    re_path(r'lista-nota-debito/(?P<pk>\d+)', ListaNotaDebitoViews.as_view(), name='lista_nota_debito'),
    re_path(r'^lista-nota-debito/empresa/$', SeleccionarEmpresaView.as_view(),name='seleccionar-empresa'),
    re_path(r'^invoice/(?P<slug>[a-zA-Z0-9º-]+)/$', DeatailInvoice.as_view(),name='detail-invoice'),
    re_path(r'^ND/(?P<pk>\d+)/enviadas/$', NotaDebitoEnviadasView.as_view(),name='lista-enviadas'),
    path('enviar-nota-debito/<int:pk>/<str:slug>/', SendInvoice.as_view(),name='send-invoice'),
]



