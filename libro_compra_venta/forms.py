from django import forms

from .models import *

class FormLibro(forms.ModelForm):
    """
    """
    class Meta:
        model = Libro
        exclude = ('libro_xml',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.fields['current_date'].widget.attrs.update({'class': 'form-control','placeholder':'DD/MM/YYYY','readonly':'readonly'})
        self.fields['details'].widget.attrs.update({'class': 'form-control'})
