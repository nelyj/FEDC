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
    path('eliminar-dte/<int:pk>/<int:comp>/',
         DeleteDTEView.as_view(), name="eliminar_dte"),
    path('imprimir-dte/<int:pk>/<str:slug>/',
         ImprimirFactura.as_view(), name="imprimir_dte"),
    path('listar-dte/<int:pk>/',
         AjaxGenericListDTETable.as_view(), name="ajax_list_dte"),
    path('send_sii/<int:pk>/',
         SendToSiiView.as_view(), name="send_sii"),
    path('get-dte-data/<int:pk>/',
         GetDteDataView.as_view(), name="get_dte_data"),
    path('estado/<int:pk>/<str:slug>/',
         VerEstado.as_view(), name="ver_estado"),
    path('listar-dte-erp/<int:pk>/',
         ListarDteDesdeERP.as_view(), name="lista_dte_erp"),
    path('guardar-dte-erp/<int:pk>/<str:slug>/',
         SaveDteErp.as_view(), name='save_dte_erp'),
]
