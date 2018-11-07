# -*- coding: utf-8 -*-
from django.conf.urls import url
from .views import *

app_name = 'utils'
urlpatterns = [
    url(r'^inicio/$', StartView.as_view(), name='inicio'),
]
