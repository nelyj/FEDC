from django import forms
from django.forms import ModelForm
from django.forms.widgets import PasswordInput

from .models import Conector


class FormConector(ModelForm):

    class Meta:
        model = Conector
        fields = ['url', 'usuario', 'password']

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['usuario'].widget.attrs.update({'class': 'form-control'})
        self.fields['usuario'].required = True
        self.fields['usuario'].empty_label = 'Seleccione Usuario'

        self.fields['url'].widget.attrs.update({'class': 'form-control', 
                                                'placeholder': 'Configurar Url'})
        self.fields['url'].required = True

        self.fields['password'].widget = PasswordInput()
        self.fields['password'].widget.attrs.update({'class': 'form-control', 
                                                'placeholder': 'Password'})
        self.fields['password'].required = True