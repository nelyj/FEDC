from django.urls import path

from .views import *

app_name = 'libro'

urlpatterns = [
    path('libro/', StartLibro.as_view(),name='libro'),
    path('libro/crear/<int:pk>', CreateLibro.as_view(),name='crear_libro'),
    path('libro/listar/<int:pk>', ListarLibrosViews.as_view(),name='listar_libro'),
    path('libro/listar-ajax/<int:pk>', AjaxListTable.as_view(),name='listar_libro_ajax'),
    path('libro/detalle/<int:pk>', LibroDetailView.as_view(),name='detalle_libro'),
    path('libro/enviar/<int:pk>', LibroSendView.as_view(),name='enviar_libro'),
]