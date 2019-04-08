from django.urls import path
from .views import (
	IntercambiosListView, 
	RefrescarBandejaRedirectView,
)

app_name = 'intercambios'
urlpatterns = [
    # re_path(r'^invoice/(?P<pk>\d+)/enviadas/$', FacturasEnviadasView.as_view(),name='lista-enviadas'),
    path('intercambio/', IntercambiosListView.as_view(),name='lista'),
    path('intercambio/actualizar', RefrescarBandejaRedirectView.as_view(),name='actualizar'),
]



