from django.urls import path
from .views import *

app_name = 'utils'
urlpatterns = [
  path('inicio/', StartView.as_view(), name='inicio'),
  path('registrar-parametros/', RegistrarParametroView.as_view(), name='registrar_parametro'),
  #path('send_sii/<int:pk>/<str:dte>', SendToSiiView.as_view(),name="send_sii"),
]
