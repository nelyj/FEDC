# -*- coding: utf-8 -*-
from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^inicio/$', StartView.as_view(), name='inicio'),
    url(r'^pais-autocomplete/$', PaisAutocomplete.as_view(),
    name='pais_autocomplete',
    ),
    url(r'^estado-autocomplete/$', EstadoAutocomplete.as_view(),
    name='estado_autocomplete',
    ),
    url(r'^municipio-autocomplete/$', MunicipioAutocomplete.as_view(),
    name='municipio_autocomplete',
    ),
    url(r'^parroquia-autocomplete/$', ParroquiaAutocomplete.as_view(),
    name='parroquia_autocomplete',
    ),
]
