from django.urls import path, re_path

from base.views import DeleteDTEView

from .views import *

app_name = 'facturas'
urlpatterns = [
    re_path(r'lista-facturas/(?P<pk>\d+)',
            ListaFacturasViews.as_view(), name='lista_facturas'),
    re_path(r'^lista-facturas/empresa/$',
            SeleccionarEmpresaView.as_view(), name='seleccionar-empresa'),
    re_path(r'^factura/(?P<slug>[a-zA-Z0-9º-]+)/$',
            DeatailInvoice.as_view(), name='detail-invoice'),
    re_path(r'^facturas-enviadas/(?P<pk>\d+)/$',
            FacturasEnviadasView.as_view(), name='lista-enviadas'),
    path('enviar-factura/<int:pk>/<str:slug>/',
         SendInvoice.as_view(), name='send-invoice'),
    path('estado-factura/<int:pk>/<str:slug>/',
         VerEstadoFactura.as_view(), name="ver_estado"),
    path('eliminar-dte/<int:pk>',
       DeleteDTEView.as_view(), name="eliminar_dte"),
]
