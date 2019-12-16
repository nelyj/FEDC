from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic.base import TemplateView
from .views import *

app_name = 'boletas'
urlpatterns = [
    re_path(r'lista-boletas/(?P<pk>\d+)', ListaBoletasViews.as_view(), name='lista_boletas'),
    re_path(r'^lista-boletas/empresa/$', SeleccionarEmpresaView.as_view(),name='seleccionar-empresa'),
    path('boleta/<str:slug>/',DeatailInvoice.as_view(),name='detail-boleta'),
    re_path(r'^boletas-enviadas/(?P<pk>\d+)/$', BoletasEnviadasView.as_view(),name='lista-enviadas'),
	path('enviar-boleta/<int:pk>/<str:slug>/', SendInvoice.as_view(),name='send-boleta'),
	path('envio-masivo/', EnvioMasivo.as_view(),name="envio_masivo"),
    # path('imprimir-factura/<int:pk>/<str:slug>/<str:doc>/', ImprimirFactura.as_view(),name="imprimir_factura"),
    # path('estado-factura/<int:pk>/<str:slug>/',VerEstadoFactura.as_view(),name="ver_estado"),
    # re_path(r'^enviar-boleta/(?P<pk>\d+)/(?P<slug>[a-zA-Z0-9º-]+)/$', SendInvoice.as_view(),name='send-invoice'),
]