from django.urls import path
from .views import *

app_name = 'conectores'
urlpatterns = [
    path('registrar-conector/', ConectorViews.as_view(), name='registrar_conector'),
    path('registrar-compania/', CompaniaViews.as_view(), name='registrar_compania'),
]