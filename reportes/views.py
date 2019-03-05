from django.shortcuts import render
from django.views.generic import CreateView, DetailView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect

from .forms import ReporteCreateForm
from facturas.models import Factura
from boletas.models import Boleta

# Create your views here.


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
		compania = instance.compania
		fecha_de_inicio = instance.fecha_de_inicio
		fecha_de_culminacion = instance.fecha_de_culminacion
		tipo_de_reporte = instance.tipo_de_reporte

		assert type(tipo_de_reporte) == str, "tipo no string"

		if tipo_de_reporte == "33":

			queryset_ = []
			queryset_ = [
				factura 
				for factura in Factura.objects.filter(compania=compania)
			]
			context['queryset'] = queryset_ 

			print(queryset_)

		elif tipo_de_reporte == "39":

			queryset_ = []
			queryset_ = [
				boleta 
				for boleta in Boleta.objects.filter(compania=compania)
			]
			print(queryset_)


		instance.save()
		# return super().form_valid(form)
		return HttpResponseRedirect(reverse_lazy('reportes:crear'))

	# def get_context_data(self, *args, **kwargs):

	# 	context = super().get_context_data(*args, **kwargs)

	# 	companias = [compania for compania in Compania.object.filter(owner=self.request.user)]

	# 	for compania in companias:



	# 	context['lista_de_reportes'] = [
	# 		reporte 
	# 		for reporte in Reporte.objects.filter().order_by('created')
	# 		]

	# 	print(context['lista_de_reportes'])
	
	# 	# Filtrar por usuario o empresa 

	# 	return context
		
	def get_form_kwargs(self):

		kwargs = super().get_form_kwargs()

		kwargs['request'] = self.request

		return kwargs



# class ReporteDetailView(DetailView):

# 	template_name = "reporte_detail_view.html"

# 	def get_object(self):

# 		id_ = self.kwargs.get("id", None)

# 		object_ = get_object_or_404(id=id_)

# 		return object_

# 	def get_context_data(self, *args, **kwargs):

# 		context = super().get_context_data()
# 		object_ = self.get_object()

# 		context['facturas_del_reporte'] = [
# 			factura
# 			for factura in Factura.objects.filter(created_at__range)
# 		]


# 		return context

