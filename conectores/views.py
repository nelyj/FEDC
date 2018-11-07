from django.contrib import messages
from django.views.generic.edit import FormView

from .forms import FormConector
from .models import Conector


class ConectorViews(FormView):
    """
    """
    form_class = FormConector
    template_name = 'registrar_conector.html'
    success_url = '/inicio/'
    model = Conector

    def form_valid(self,form):
        """!
        Form Valid Method

        @param form Recives form object
        @return validate True
        """
        form.save()
        msg = "Se creo el Conector con éxito"
        messages.info(self.request, msg)
        return super().form_valid(form)

    def form_invalid(self, form):
        """!
        Form Invalid Method

        @param form Recives form object
        @return errors on form
        """
        messages.error(self.request, form.errors)
    
        return super().form_invalid(form)