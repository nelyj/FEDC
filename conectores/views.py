from django.contrib import messages
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.views.generic.edit import FormView

from .forms import *
from .models import *
from datetime import datetime


class ConectorViews(FormView):
    """
    """
    form_class = FormConector
    template_name = 'registrar_conector.html'
    success_url = '/inicio/'
    model = Conector
    hasher = PBKDF2PasswordHasher

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            record = Conector.objects.filter(pk=1).first()
            if record:
                form = FormConector(instance=record)
            else:
                form = FormConector()
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
        #try:
        transaction = Conector.objects.update_or_create(
            pk=1,
            defaults={
            'usuario': form['usuario'].value(),
            'url_erp': form['url_erp'].value(),
            'url_sii': form['url_sii'].value(),
            #'password': self.hasher().encode(password=form['password'].value(), salt='salt', iterations=50000),
            'password': form['password'].value(),
            'time_cron': form['time_cron'].value(),
            'certificado': form['certificado'].value()
            })
        msg = "Se configuro el Conector con éxito"
        messages.info(self.request, msg)
        #except Exception as e:
        #    msg = "Ocurrio un problema al guardar la información"
        #    messages.error(self.request, msg)
        return super().form_valid(form)
    def form_invalid(self, form):
        """!
        Form Invalid Method

        @param form Recives form object
        @return errors on form
        """
        messages.error(self.request, form.errors)
    
        return super().form_invalid(form)

    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()

        kwargs['request'] = self.request

        return kwargs

class CompaniaViews(FormView):
    """
    """
    form_class = FormCompania
    template_name = 'registrar_compania.html'
    success_url = '/inicio/'
    model = Compania

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            record = Compania.objects.filter(pk=1).first()
            if record:
                # datetime.strftime(record.fecha_resolucion,"%d/%m/%Y")
                # record.fecha_resolucion.strftime("%Y/%m/%d")
                # datetime.strptime(record.fecha_resolucion, "%d/%m/%Y")
                form = FormCompania(instance=record)
            else:
                form = FormCompania()
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
        try:
            transaction = Compania.objects.update_or_create(
                pk=1,
                defaults={
                'owner': self.request.user,
                'rut': form['rut'].value(),
                'razon_social': form['razon_social'].value(),
                'actividad_principal': form['actividad_principal'].value(),
                'giro': form['giro'].value(),
                'direccion': form['direccion'].value(),
                'comuna': form['comuna'].value(),
                'fecha_resolucion': datetime.strptime(form['fecha_resolucion'].value(), "%d/%m/%Y"),
                'numero_resolucion': form['numero_resolucion'].value(),
                'pass_correo_sii': form['pass_correo_sii'].value(),
                'correo_sii': form['correo_sii'].value(),
                'pass_correo_intercambio': form['pass_correo_intercambio'].value(),
                'correo_intercambio': form['correo_intercambio'].value(),
                'logo': form['logo'].value()
                })
            msg = "Se configuro la Compañia con éxito"
            messages.info(self.request, msg)
        except Exception as e:
            msg = "Ocurrio un problema al guardar la información: "+str(e)
            messages.error(self.request, msg)
        return super().form_valid(form)
    def form_invalid(self, form):
        """!
        Form Invalid Method

        @param form Recives form object
        @return errors on form
        """
        print(type(form['fecha_resolucion'].value()))
        messages.error(self.request, form.errors)
    
        return super().form_invalid(form)