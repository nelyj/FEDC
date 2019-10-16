from django.urls import path
from .views import *

app_name = 'dte'
urlpatterns = [
    path('lista-dte/empresa',
         StartDte.as_view(), name="seleccionar_empresa"),
    path('lista-dte/<int:pk>/',
         DteSistemaView.as_view(), name="lista_dte"),
    path('lista-dte/<int:pk>/crear',
         DteCreateView.as_view(), name="crear_dte"),
    path('actualizar-dte/<int:pk>/<int:comp>/',
         UpdateDTEView.as_view(), name="actualizar",),
    path('eliminar-dte/<int:pk>',
         DeleteDTEView.as_view(), name="eliminar_dte"),
    path('imprimir-dte/<int:pk>/<str:slug>/',
         ImprimirFactura.as_view(), name="imprimir_dte"),
    path('listar-dte/<int:pk>/',
         AjaxGenericListDTETable.as_view(), name="ajax_list_dte"),
]
