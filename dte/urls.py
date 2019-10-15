from django.urls import path
from .views import *

app_name = 'dte'
urlpatterns = [
    path('lista-dte/empresa', 
        StartDte.as_view(), name="seleccionar_empresa"),
    path('lista-dte/<int:pk>',
       DteSistemaView.as_view(), name="lista_dte"),
    path('lista-dte/<int:pk>/crear',
       DteCreateView.as_view(), name="crear_dte"),
]