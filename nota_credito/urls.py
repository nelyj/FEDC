from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic.base import TemplateView

from base.views import (
    UpdateDTEView, DeleteDTEView
)

from .forms import *
from .models import *
from .views import *

app_name = 'nota_credito'
urlpatterns = [
    re_path(r'lista-nota-credito/(?P<pk>\d+)', ListaNotaCreditoViews.as_view(), name='lista_nota_credito'),
    re_path(r'^lista-nota-credito/empresa/$', StartNotaCredito.as_view(),name='seleccionar-empresa'),
    re_path(r'^nota-credito/(?P<slug>[a-zA-Z0-9º-]+)/$', DeatailInvoice.as_view(),name='detail-invoice'),
    re_path(r'^NC-enviadas/(?P<pk>\d+)/$', NotaCreditoEnviadasView.as_view(),name='lista-enviadas'),
    path('enviar-nota-credito/<int:pk>/<str:slug>/', SendInvoice.as_view(),name='send-invoice'),
    path('estado-nc/<int:pk>/<str:slug>/',VerEstadoNC.as_view(),name="ver_estado_nc"),
    path('sistema-nc/<int:pk>', NotaCreditoSistemaView.as_view(),name="nota_sistema_listado"),
    path('crear-nc/<int:pk>', NotaCreditoCreateView.as_view(),name="nota_sistema_crear"),
    path('actualizar-dte-nc/<int:pk>/<int:comp>/',
         UpdateDTEView.as_view(
          form_class=FormCreateNotaCredito, model=notaCredito,
          template_name='nc_crear.html',
          success_url ='nota_credito:actualizar'
          ), name="actualizar",),
    path('eliminar-dte-nc/<int:pk>',
         DeleteDTEView.as_view(model=notaCredito,
         success_url=reverse_lazy('notaCredito:seleccionar-empresa')), name="eliminar_dte"),
]
