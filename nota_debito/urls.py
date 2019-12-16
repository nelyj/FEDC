from django.contrib import admin
from django.urls import (
    path, include, 
    re_path, reverse_lazy
)
from django.views.generic.base import TemplateView

from base.views import (
    UpdateDTEView, DeleteDTEView
)

from nota_credito.views import NotaCreditoCreateView

from .forms import FormCreateNotaDebito
from .models import notaDebito
from .views import *

app_name = 'nota_debito'
urlpatterns = [
    re_path(r'lista-nota-debito/(?P<pk>\d+)', ListaNotaDebitoViews.as_view(), name='lista_nota_debito'),
    re_path(r'^lista-nota-debito/empresa/$', StartNotaCredito.as_view(),name='seleccionar-empresa'),
    re_path(r'^nota-debito/(?P<slug>[a-zA-Z0-9º-]+)/$', DeatailInvoice.as_view(),name='detail-invoice'),
    re_path(r'^ND-enviadas/(?P<pk>\d+)/$', NotaDebitoEnviadasView.as_view(),name='lista-enviadas'),
    path('enviar-nota-debito/<int:pk>/<str:slug>/', SendInvoice.as_view(),name='send-invoice'),
    path('estado-nd/<int:pk>/<str:slug>/',VerEstadoND.as_view(),name="ver_estado_nd"),
    path('sistema-nd/<int:pk>', NotaDebitoSistemaView.as_view(),name="nota_sistema_listado"),
    path('crear-nd/<int:pk>',
         NotaCreditoCreateView.as_view(
          form_class=FormCreateNotaDebito, model=notaDebito,
          template_name='nd_crear.html',
          success_url = 'nota_debito:nota_sistema_crear'
          ), name="nota_sistema_crear"),
    path('actualizar-dte-nd/<int:pk>/<int:comp>/',
         UpdateDTEView.as_view(
          form_class=FormCreateNotaDebito, model=notaDebito,
          template_name='nd_crear.html',
          success_url ='nota_debito:actualizar'), name="actualizar"),
    path('eliminar-dte-nd/<int:pk>',
         DeleteDTEView.as_view(model=notaDebito,
         success_url=reverse_lazy('notaDebito:seleccionar-empresa')), name="eliminar_dte"),
]
