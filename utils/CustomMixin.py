from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView

from conectores.models import Compania


class SeleccionarEmpresaView(LoginRequiredMixin,TemplateView):
    """
    Clase personalizada para la selección de empresa
    """
    template_name = 'select_empresa.html'

    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(*args, **kwargs)
        context['empresas'] = Compania.objects.all()
        if context['empresas']:
            context['tiene_empresa'] = True
        else:
            messages.info(self.request, "Registre una empresa para continuar")
            context['tiene_empresa'] = False
        return context
