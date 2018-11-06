from django.contrib import admin
from .models import *
from .forms import (
    ParroquiaForm, EstadoForm, MunicipioForm
)


class EstadoAdmin(admin.ModelAdmin):
    form = EstadoForm


class MunicipioAdmin(admin.ModelAdmin):
    form = MunicipioForm


class ParroquiaAdmin(admin.ModelAdmin):
    form = ParroquiaForm


admin.site.register(Pais)
admin.site.register(Estado, EstadoAdmin)
admin.site.register(Municipio, MunicipioAdmin)
admin.site.register(Parroquia, ParroquiaAdmin)
admin.site.register(TipoDocumento)

