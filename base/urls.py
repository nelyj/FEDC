from django.urls import path
from .views import *

app_name = 'base'
urlpatterns = [
  path('send_sii/<int:pk>/<str:dte>',
       SendToSiiView.as_view(), name="send_sii"),
  path('imprimir-factura/<int:pk>/<str:slug>/<str:doc>/',
       ImprimirFactura.as_view(), name="imprimir_factura"),
  path('listar-dte/<int:pk>/<str:dte>',
       AjaxGenericListDTETable.as_view(), name="ajax_list_dte"),
]
