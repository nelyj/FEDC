"""
Facturador TIMG
@package config.router

Router del api de Rest Framework
@copyright TIMG
@version 1.0
"""
from rest_framework import routers
from dte.viewset import *
#from nota_credito.viewset import NotaCreditoViewSet

router = routers.DefaultRouter()
router.register(r'facturas/(?P<rut>[-\w\s]+)/(?P<slug>[-\w]+)', DteViewSet, basename='facturas')
#router.register(r'nota-credito', NotaCreditoViewSet, basename='nota-credito')
