import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, TemplateView, RedirectView, DeleteView
# from django.views.generic.edit import DeleteView
from boletas.models import Boleta
from conectores.models import Compania
from facturas.models import Factura
from nota_credito.models import notaCredito
from nota_debito.models import notaDebito
from utils.SIISdk import SII_SDK
from utils.views import sendToSii
from .forms import ReporteCreateForm
from .models import Reporte


class SeleccionarEmpresaView(LoginRequiredMixin, TemplateView):
	"""
	Clase para seleccionar la empresa
	@author Alberto Rincones (alberto at timg.cl)
	@copyright TIMG
	@date 28-03-19 (dd-mm-YY)
	@version 1.0
	"""
	template_name = 'reportes_seleccionar_empresa.html'

	def get_context_data(self, *args, **kwargs): 

		context = super().get_context_data(*args, **kwargs)
		context['empresas'] = Compania.objects.all()
		if Compania.objects.filter(owner=self.request.user).exists():
				context['tiene_empresa'] = True
		else:
				messages.info(self.request, "Registre una empresa para continuar")
				context['tiene_empresa'] = False
		return context

	def post(self, request):

		enviadas = self.request.POST.get('enviadas', None)
		empresa = int(request.POST.get('empresa'))
		if not empresa:
				return HttpResponseRedirect('/')
		empresa_obj = Compania.objects.get(pk=empresa)
		if empresa_obj and self.request.user == empresa_obj.owner:

				return HttpResponseRedirect(reverse_lazy('reportes:crear', kwargs={'pk':empresa}))
		else:
				return HttpResponseRedirect('/')

class ReportesCreateListView(LoginRequiredMixin, CreateView):
	"""
	Clase para crear y listar los reportes
	@author Alberto Rincones (alberto at timg.cl)
	@copyright TIMG
	@date 28-03-19 (dd-mm-YY)
	@version 1.0
	"""

	template_name = "reporte_create_list.html"
	form_class = ReporteCreateForm
	get_success_url = reverse_lazy("reportes:crear")
	def form_valid(self, form):
		"""
		
		"""
		context = super().get_context_data()
		instance = form.save(commit=False)
		compania = get_object_or_404(Compania, pk=self.kwargs.get('pk'))
		instance.compania = compania
		fecha_de_inicio = instance.fecha_de_inicio
		fecha_de_culminacion = instance.fecha_de_culminacion
		tipo_de_operacion = instance.tipo_de_operacion
		if(instance.tipo_de_envio!='TOTAL'):
			instance.periodo_tributario = fecha_de_inicio.strftime("%Y-%m")
		else:
			from calendar import monthrange
			date = instance.periodo_tributario.split('-')
			last_day = monthrange(int(date[0]), int(date[1]))[1]
			fecha_de_inicio = datetime.datetime(int(date[0]), int(date[1]), 1)
			instance.fecha_de_inicio = fecha_de_inicio
			fecha_de_culminacion = datetime.datetime(int(date[0]), int(date[1]), last_day)
			instance.fecha_de_culminacion = fecha_de_culminacion
		report_context = {
			'compania': compania,
			'reporte': instance,
			'periodo_tributario': instance.periodo_tributario,
			'resumen_periodos':[],
			'detalles':[]
		}

		if tipo_de_operacion == "VENTA":

			facturas_queryset_ = [
				factura 
				for factura in Factura.objects.filter(
					compania=compania, 
					created__gte=fecha_de_inicio, 
					created__lte=fecha_de_culminacion
				)
			]
			nota_credito_queryset = [
				nota_credito
				for nota_credito in notaCredito.objects.filter(
					compania=compania,
					created__gte=fecha_de_inicio,
					created__lte=fecha_de_culminacion
				)
			]
			nota_debito_queryset = [
				nota_debito
				for nota_debito in notaDebito.objects.filter(
					compania=compania,
					created__gte=fecha_de_inicio,
					created__lte=fecha_de_culminacion
				)
			]
			facturas_data = self.generar_resumen_periodos(facturas_queryset_)
			nota_credito_data = self.generar_resumen_periodos(nota_credito_queryset)
			nota_debito_data = self.generar_resumen_periodos(nota_debito_queryset)

			if facturas_data:
				report_context['resumen_periodos'].append(
					facturas_data)
			if nota_credito_data:
				report_context['resumen_periodos'].append(
					nota_credito_data)

			if(len(facturas_queryset_)>0):
				report_context['detalles'].extend(facturas_queryset_)
			if(len(nota_credito_queryset)>0):
				report_context['detalles'].extend(nota_credito_queryset)
			if(len(nota_debito_queryset)>0):
				report_context['detalles'].extend(nota_debito_queryset)

		elif tipo_de_operacion == "COMPRA":

			messages.info(self.request, "No posee documentos de intercambio")
			return HttpResponseRedirect(reverse_lazy('reportes:crear', kwargs={'pk': compania.pk}))

		try: 
			Reporte.check_reporte_len(report_context['detalles'])
		except Exception as e:
			messages.error(self.request, e)
			return super().form_invalid(form)

		for report in report_context['resumen_periodos']:
			report['tot_mnt_total'] = abs(report['tot_mnt_total'])
			report['tot_mnt_neto'] = round(abs(report['tot_mnt_neto']))

		for report in report_context['detalles']:

			report.neto = round(abs(float(report.neto)))
			report.total = round(abs(float(report.total)))
			report.numero_factura = report.numero_factura.replace('º','')
			if 'k' in report.rut:
				report.rut = report.rut.replace('k','K')
			report.rut = report.rut.replace('.','')

		caratula = render_to_string('xml_templates/caratula_.xml', report_context)
		report_context['caratula'] = caratula
		report_context['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
		envio_libro = render_to_string('xml_templates/envioLibro_.xml', report_context)
		# Agregada la firma
		sii_sdk = SII_SDK(settings.SII_PRODUCTION)
		libro_firmado = sii_sdk.generalSign(compania,envio_libro,compania.pass_certificado)
		instance.xml_reporte = '<?xml version="1.0" encoding="ISO-8859-1"?>\n'+libro_firmado
		#instance.xml_reporte = '<?xml version="1.0" encoding="ISO-8859-1"?>\n'+envio_libro

		#print(libro_firmado)

		instance.save()
		messages.info(self.request, "Reporte creado exitosamente")
		return HttpResponseRedirect(reverse_lazy('reportes:crear', kwargs={'pk': compania.pk}))

	def get_context_data(self, *args, **kwargs):

		context = super().get_context_data(*args, **kwargs)
		compania = get_object_or_404(Compania, pk=self.kwargs.get('pk'))
		context['lista_de_reportes'] = Reporte.objects.filter(compania=compania).reverse()
		context['compania'] = compania	
		return context

	def generar_resumen_periodos(self, queryset):

		if len(queryset) == 0:

			return 

		tot_mnt_exe=0
		tot_mnt_neto=0
		tot_op_iva_rec=0
		tot_mnt_iva=0
		tot_mnt_total=0

		for item in queryset:
			if item.excento:
				tot_mnt_exe += float(item.excento)
			if item.iva: 
				tot_op_iva_rec += 1
				tot_mnt_iva += float(item.iva)
			if item.neto:
				tot_mnt_neto += float(item.neto)
			if item.total:
				tot_mnt_total += float(item.total)


		data = dict(
			tpo_doc=queryset[0].TIPO_DE_DOCUMENTO,
			tot_doc=len(queryset),
			tot_mnt_exe=int(tot_mnt_exe),
			tot_mnt_neto=int(tot_mnt_neto),
			tot_op_iva_rec=int(tot_op_iva_rec),
			tot_mnt_iva=int(tot_mnt_iva),
			tot_mnt_total=int(tot_mnt_total)
		)

		return data

	# def generar_detalles(self, **kwargs): 

class ReporteDetailView(LoginRequiredMixin, DetailView):
	"""
	Clase para ver el detalle de un reporte
	@author Alberto Rincones (alberto at timg.cl)
	@copyright TIMG
	@date 11-04-19 (dd-mm-YY)
	@version 1.0
	"""

	template_name="reportes_detail.html"

	def get_context_data(self, *args, **kwargs):

		context = super().get_context_data(*args, **kwargs)
		reporte = self.get_object()
		context['facturas_del_reporte'] = Factura.objects.filter(
			created__gte=reporte.fecha_de_inicio, 
			created__lte=reporte.fecha_de_culminacion
			)
		return context

	def get_object(self):

		return get_object_or_404(Reporte, pk=self.kwargs.get('pk'))



class ReportesDeleteView(LoginRequiredMixin,DeleteView):
	"""
	Clase para eliminar un reporte
	@author Alberto Rincones (alberto at timg.cl)
	@copyright TIMG
	@date 11-04-19 (dd-mm-YY)
	@version 1.0
	"""

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

class ReporteXMLView(LoginRequiredMixin,View):
	"""
	Clase para generar el xml para descargar
	@author Rodrigo Boet (rodrigoale.b at timg.cl)
	@copyright TIMG
	@date 17-04-19 (dd-mm-YY)
	@version 1.0
	"""

	def get(self, request, **kwargs):
		"""!
		Método para obtener el xml del libo
		@param request Objeto con la petición
		@param kwargs Argumentos de la vista
		@return HttpResponse con el adjunto
		"""
		reporte = Reporte.objects.get(pk=self.kwargs['pk'])
		filename = 'libro.xml'
		response = HttpResponse(reporte.xml_reporte, content_type='application/xml')
		response['Content-Disposition'] = 'attachment; filename='+filename
		return response

class ReporteSendToSiiView(LoginRequiredMixin,View):
	"""
	Clase para envíar el reporte al sii
	@author Rodrigo Boet (rodrigoale.b at timg.cl)
	@copyright TIMG
	@date 17-04-19 (dd-mm-YY)
	@version 1.0
	"""

	def get(self, request, **kwargs):
		"""!
		Método para obtener el xml del libo
		@param request Objeto con la petición
		@param kwargs Argumentos de la vista
		@return redirect a la vista normal
		"""
		reporte = Reporte.objects.get(pk=self.kwargs['pk'])
		compania = Compania.objects.get(pk=self.kwargs['compania'])
		if(not reporte.enviado):
			send_sii = sendToSii(compania,reporte.xml_reporte,compania.pass_certificado)
			if(not send_sii['estado']):
					messages.error(self.request, send_sii['msg'])
			else:
				reporte.track_id = send_sii['track_id']
				reporte.enviado = True
				reporte.save()
				messages.success(request, "Se envío el libro correctamente")
		else:
			messages.info(request, "Éste libro ya fue envíado al sii")
		return redirect(reverse_lazy('reportes:crear', kwargs={'pk': self.kwargs['compania']}))
