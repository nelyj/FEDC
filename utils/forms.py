# -*- coding: utf-8 -*-
from dal import autocomplete
from django import forms

from .models import (
    Pais, Estado, Municipio, Parroquia
)


class EstadoForm(forms.ModelForm):
    pais = forms.ModelChoiceField(
    queryset=Pais.objects.all(),
    widget=autocomplete.ModelSelect2(url='utils:pais_autocomplete')
    )

    class Meta:
        model = Estado
        fields = ('__all__')


class MunicipioForm(forms.ModelForm):
    estado = forms.ModelChoiceField(
    queryset=Estado.objects.all(),
    widget=autocomplete.ModelSelect2(url='utils:estado_autocomplete')
    )

    class Meta:
        model = Municipio
        fields = ('__all__')


class ParroquiaForm(forms.ModelForm):
    municipio = forms.ModelChoiceField(
    queryset=Municipio.objects.all(),
    widget=autocomplete.ModelSelect2(url='utils:municipio_autocomplete')
    )

    class Meta:
        model = Parroquia
        fields = ('__all__')