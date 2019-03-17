from django.urls import path
from .views import IntercambiosListView

app_name = 'intercambios'
urlpatterns = [
    # re_path(r'^invoice/(?P<pk>\d+)/enviadas/$', FacturasEnviadasView.as_view(),name='lista-enviadas'),
    path('intercambio/', IntercambiosListView.as_view(),name='lista'),
]



