import datetime

from django.shortcuts import render
from django.views.generic import CreateView, DetailView, TemplateView, RedirectView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.template.loader import render_to_string
# from django.views.generic.edit import DeleteView
from .forms import ReporteCreateForm
from facturas.models import Factura
from boletas.models import Boleta
from conectores.models import Compania
from .models import Reporte

# Create your views here.
class SeleccionarEmpresaView(TemplateView):
    template_name = 'reportes_seleccionar_empresa.html'

    def get_context_data(self, *args, **kwargs): 

        context = super().get_context_data(*args, **kwargs)
        context['empresas'] = Compania.objects.filter(owner=self.request.user)
        if Compania.objects.filter(owner=self.request.user).exists():
            context['tiene_empresa'] = True
        else:
            messages.info(self.request, "Registre una empresa para continuar")
            context['tiene_empresa'] = False
        return context

    def post(self, request):

        enviadas = self.request.POST.get('enviadas', None)

        # print(enviadas)
        # enviadas = int(enviadas)

        empresa = int(request.POST.get('empresa'))

        if not empresa:
            return HttpResponseRedirect('/')
        empresa_obj = Compania.objects.get(pk=empresa)
        if empresa_obj and self.request.user == empresa_obj.owner:

            return HttpResponseRedirect(reverse_lazy('reportes:crear', kwargs={'pk':empresa}))
        else:
            return HttpResponseRedirect('/')

class ReportesCreateListView(CreateView):

	template_name = "reporte_create_list.html"
	form_class = ReporteCreateForm
	get_success_url = reverse_lazy("reportes:crear")

	# def get_success_url(self):

	# 	return self.reques

	def form_valid(self, form):
		"""
		
		"""
		context = super().get_context_data()
		instance = form.save(commit=False)
		compania = get_object_or_404(Compania, pk=self.kwargs.get('pk'))
		instance.compania = compania
		fecha_de_inicio = instance.fecha_de_inicio
		fecha_de_culminacion = instance.fecha_de_culminacion
		tipo_de_reporte = instance.tipo_de_reporte

		assert type(tipo_de_reporte) == str, "tipo no string"

		print(fecha_de_inicio, fecha_de_culminacion)
		print(instance.fecha_de_inicio, instance.fecha_de_culminacion)


		if tipo_de_reporte == "33":


			queryset_ = []
			queryset_ = [
				factura 
				for factura in Factura.objects.filter(compania=compania, created__gte=fecha_de_inicio, created__lte=fecha_de_culminacion)
			]


		elif tipo_de_reporte == "39":

			queryset_ = []
			queryset_ = [
				boleta 
				for boleta in Boleta.objects.filter(compania=compania, created__gte=fecha_de_inicio, created__lte=fecha_de_culminacion)
			]
			print(queryset_)


		try: 
			Reporte.check_reporte_len(queryset_)
		except Exception as e:

			messages.error(self.request, e)
			return super().form_invalid(form)

		print(queryset_)


		instance.save()
		# return super().form_valid(form)
		return HttpResponseRedirect(reverse_lazy('reportes:crear', kwargs={'pk': compania.pk}))

	def get_context_data(self, *args, **kwargs):

		context = super().get_context_data(*args, **kwargs)

		compania = get_object_or_404(Compania, pk=self.kwargs.get('pk'))
		print(compania)

		context['lista_de_reportes'] = Reporte.objects.filter(compania=compania).order_by('created')
		context['compania'] = compania	

	
		# Filtrar por usuario o empresa 

		return context
		


class ReporteDetailView(DetailView):

	template_name="reportes_detail.html"

	def get_context_data(self, *args, **kwargs):

		context = super().get_context_data(*args, **kwargs)

		reporte = self.get_object()

		print(reporte)

		context['facturas_del_reporte'] = Factura.objects.filter(created__gte=reporte.fecha_de_inicio, created__lte=reporte.fecha_de_culminacion)

		print(context['facturas_del_reporte'])

		return context

	def get_object(self):

		return get_object_or_404(Reporte, pk=self.kwargs.get('pk'))



class ReportesDeleteView(LoginRequiredMixin,DeleteView):

	template_name="reportes_delete.html"
	# model = Reporte
	# success_url = reverse_lazy('reportes:crear', kwargs={'pk':compania_pk})

	def get_object(self):

		user = self.request.user
		compania_pk = compania_pk = self.kwargs.get("pk")
		compania = get_object_or_404(Compania, owner=user)
		reporte_pk = self.kwargs.get("reporte_pk")
		reporte = get_object_or_404(Reporte, pk=reporte_pk)


		return reporte

	def delete(self, request, *args, **kwargs):

	    self.object = self.get_object()
	    success_url = self.get_success_url()
	    self.object.delete()
	    messages.success(self.request, "Reporte borrado exitosamente")
	    return HttpResponseRedirect(success_url)


	def get_success_url(self):

		compania_pk = self.kwargs.get("pk")

		return reverse_lazy('reportes:crear', kwargs={'pk':compania_pk})

class EnviarReporteRedirectView(LoginRequiredMixin,RedirectView):


	def get(self, *args, **kwargs):

		reporte = get_object_or_404(Reporte, pk=self.kwargs.get('pk'))
		compania = get_object_or_404(Compania, pk=self.kwargs.get('compania_pk'))


		documentos_del_reporte = Factura.objects.filter(created__gte=reporte.fecha_de_inicio, created__lte=reporte.fecha_de_culminacion)

		context = {
			'documentos_del_reporte': documentos_del_reporte,
			'compania': compania
		}

		signature_tag = render_to_string('snippets/signature.xml', {'signature':firma_electronica})

		return context


