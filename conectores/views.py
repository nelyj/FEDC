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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            record = Conector.objects.get(pk=1)
            form = FormConector(instance=record)
            context['form']=form
        except Exception as e:
            raise e
        return context

    def form_valid(self,form):
        """!
        Form Valid Method

        @param form Recives form object
        @return validate True
        """
        print(form['usuario'].value())
        try:
            transaction = Conector.objects.update_or_create(
                pk=1,
                defaults={
                'usuario': form['usuario'].value(),
                'url_erp': form['url_erp'].value(),
                'url_sii': form['url_sii'].value(),
                'password': form['password'].value(),
                'time_cron': form['time_cron'].value()
                })
            msg = "Se configuro el Conector con éxito"
            messages.info(self.request, msg)
        except Exception as e:
            msg = "Ocurrio un problema al guardar la información"
            messages.error(self.request, msg)
        return super().form_valid(form)
    def form_invalid(self, form):
        """!
        Form Invalid Method

        @param form Recives form object
        @return errors on form
        """
        messages.error(self.request, form.errors)
    
        return super().form_invalid(form)