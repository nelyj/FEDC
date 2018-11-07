from django.contrib import admin
from .models import *

admin.site.register(Pais)
admin.site.register(Estado)
admin.site.register(Municipio)
admin.site.register(Parroquia)
admin.site.register(TipoDocumento)

