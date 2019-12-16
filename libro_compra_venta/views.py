import json
import decimal

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import  View, DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.db.models import Q

from django_datatables_view.base_datatable_view import BaseDatatableView

from dte.models import DTE

from conectores.models import Compania

from facturas.models import Factura

from nota_credito.models import notaCredito

from nota_debito.models import notaDebito

from utils.views import sendToSii
from utils.CustomMixin import SeleccionarEmpresaView

from .constants import dict_tipo_libro
from .forms import *
from .models import *


class StartLibro(SeleccionarEmpresaView):
    """
    Selecciona la empresa

    @author Rodrigo A. Boet (rodrigo.b at timgla.com)
    @date 12-08-2019
    @version 1.0.0
    """

    def post(self, request, *args, **kwargs):

        empresa = int(request.POST.get('empresa'))
        if not empresa:
            return HttpResponseRedirect('/')
        empresa_obj = Compania.objects.get(pk=empresa)
        if empresa_obj and self.request.user == empresa_obj.owner and self.kwargs['tipo'] == 'crear':
            return HttpResponseRedirect(reverse_lazy('libro:crear_libro', kwargs={'pk':empresa}))
        elif empresa_obj and self.request.user == empresa_obj.owner and self.kwargs['tipo'] == 'listar':
            return HttpResponseRedirect(str(reverse_lazy('libro:listar_libro', kwargs={'pk':empresa})+"?tipo_libro=1"))
        elif empresa_obj and self.request.user == empresa_obj.owner and self.kwargs['tipo'] == 'crear-compra':
            return HttpResponseRedirect(reverse_lazy('libro:crear_libro_compra', kwargs={'pk':empresa}))
        elif empresa_obj and self.request.user == empresa_obj.owner and self.kwargs['tipo'] == 'listar-compra':
            return HttpResponseRedirect(str(reverse_lazy('libro:listar_libro', kwargs={'pk':empresa})+"?tipo_libro=0"))
        else:
            return HttpResponseRedirect('/')


class CreateLibro(LoginRequiredMixin, FormView):
    """
    Registra un nuevo libro

    @author Rodrigo A. Boet (rodrigo.b at timgla.com)
    @date 12-08-2019
    @version 1.0.0
    """
    form_class = FormLibro
    template_name = 'crear_libro.html'
    success_url = '/libro/'
    model = Libro
    #model_factura = Factura
    #model_nota_cr = notaCredito
    #model_nota_db = notaDebito
    model_dte = DTE
    TWOPLACES = decimal.Decimal(10) ** -2 

    def get_context_data(self, *args, **kwargs): 

        context = super().get_context_data(*args, **kwargs)

        context['compania'] = self.kwargs['pk']
        return context

    def form_valid(self, form, *args, **kwargs):

        compania = self.kwargs['pk']
        date = form['current_date'].value()
        date_arr = date.split('/')

        start_date = date_arr[2]+"-"+date_arr[1]+"-"+'01'
        objeto_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        start_date = objeto_datetime - relativedelta(months=1)
        end_date = objeto_datetime - timedelta(days=1)  # Resta a fecha actual 1 día
        #print(objeto_datetime, start_date)
        #date_arr.reverse()
        #end_date = "-".join(date_arr)

        objects = []
        object_dte = self.model_dte.objects.filter(compania=compania, fecha__range=[start_date, end_date]).exclude(track_id=None)
        #factura = self.model_factura.objects.filter(compania=compania, fecha__range=[start_date, end_date])
        #nota_credito = self.model_nota_cr.objects.filter(compania=compania, fecha__range=[start_date, end_date])
        #nota_debito = self.model_nota_db.objects.filter(compania=compania, fecha__range=[start_date, end_date])

        for dte in object_dte:
            dte.total_doc = 1
            dte.numero_factura = dte.numero_factura.replace('º','')
            productos = dte.productos.replace('\'{','{').replace('}\'','}').replace('\'',"\"")
            json_productos = json.loads(productos)
            exento = 0
            for producto in json_productos:
                if producto['discount']:
                    f_total = producto['qty'] * producto['base_net_rate']
                    total = f_total - (f_total*(producto['discount']/100))
                    exento += decimal.Decimal(total).quantize(self.TWOPLACES)
            if(dte.descuento_global):
                nuevo_exento = dte.descuento_global
                if(dte.tipo_descuento == "%"):
                    nuevo_exento = decimal.Decimal(dte.neto).quantize(self.TWOPLACES) * decimal.Decimal(dte.descuento_global/100).quantize(self.TWOPLACES)
            exento += decimal.Decimal(nuevo_exento).quantize(self.TWOPLACES)
            dte.exento = '{0:.2f}'.format(exento)
            dte.total = '{0:.2f}'.format(decimal.Decimal(exento + decimal.Decimal(dte.neto) + decimal.Decimal(dte.compania.tasa_de_iva)).quantize(self.TWOPLACES))
            #dte.exento = abs(float(dte.total) - float(dte.neto) - float(dte.iva))

        objects.append(object_dte)
        detail = form['details'].value()
        if detail:
            xml = render_to_string('xml_lcv/resumen_periodo.xml', {'objects':objects, 'objects_details': objects})
        else:
            xml = render_to_string('xml_lcv/resumen_periodo.xml', {'objects':objects})
        if not object_dte:
            messages.warning(self.request, "No existen facturas, notas de credito o debito para esta fecha {0}/{1}".format(start_date, end_date))
            return HttpResponseRedirect(reverse_lazy('libro:crear_libro', kwargs={'pk':compania}))

        try:
            compania = Compania.objects.get(pk=compania)
            libro = self.model(
                fk_compania=compania,
                current_date=end_date,
                details=form['details'].value(),
                libro_xml=xml,
                tipo_libro=1,
                periodo=end_date
                )
            libro.save()
            messages.success(self.request, "Se registro el libro con éxito")
        except Exception as e:
            messages.error(self.request, e)

        return HttpResponseRedirect(reverse_lazy('libro:listar_libro', kwargs={'pk':compania.pk}))


class ListarLibrosViews(LoginRequiredMixin, TemplateView):
    """
    Lista los libros

    @author Rodrigo A. Boet (rodrigo.b at timgla.com)
    @date 12-08-2019
    @version 1.0.0
    """
    template_name = 'listar_libro.html'

    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(*args, **kwargs)
        tipo_libro = self.request.GET.get('tipo_libro', None)
        context['tipo_libro'] = tipo_libro
        return context

class AjaxListTable(LoginRequiredMixin, BaseDatatableView):
    """!
    Prepara la data para mostrar en el datatable

    @author Rodrigo A. Boet (rodrigo.b at timgla.com)
    @date 12-08-2019
    @version 1.0.0
    """
    # The model we're going to show
    model = Libro
    columns = ['current_date', 'details', 'libro_xml', 'enviada']
    # define column names that will be used in sorting
    # order is important and should be same as order of columns
    # displayed by datatables. For non sortable columns use empty
    # value like ''
    order_columns = ['-current_date', 'details', 'libro_xml']
    # set max limit of records returned, this is used to protect our site if someone tries to attack our site
    # and make it return huge amount of data
    max_display_length = 500


    def __init__(self):
        super(AjaxListTable, self).__init__()

    def get_initial_queryset(self):
        """!
        Consulta el modelo Intercambio

        @return: Objeto de la consulta
        """
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        # You should not filter data returned here by any filter values entered by Intercambio. This is because
        # we need some base queryset to count total number of records.
        libro = self.kwargs['tipo_libro']

        return self.model.objects.filter(
                        fk_compania=self.kwargs['pk'],
                        tipo_libro=libro
                        ).order_by('-current_date')


    def filter_queryset(self, qs):
        # use parameters passed in GET request to filter queryset

        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs_params = None
            if search in "Si" or search in "si":
                search = True
            elif search in "No" or search in "no":
                search = False
            q = Q(pk__istartswith=search)|Q(current_date__icontains=search)|Q(details__icontains=search)|Q(libro_xml__icontains=search)
            qs_params = qs_params | q if qs_params else q
            qs = qs.filter(qs_params)
        return qs

    def prepare_results(self, qs):
        """!
        Prepara la data para mostrar en el datatable
        @return: Objeto json con los datos del intercambio
        """

        libro = self.kwargs['tipo_libro']

        # prepare list with output column data
        json_data = []
        for item in qs:

            detail = "Si" if item.details else "No"

            ver = "<a data-toggle='modal' data-target='#myModal' \
                    class='btn btn-block btn-info btn-xs fa fa-search' \
                    onclick='modal_detalle_libro({0})'></a>\
                    ".format(str(item.pk))
            if not item.enviada:
                send = "<a class='btn btn-block btn-success btn-xs fa fa-paper-plane'\
                        onclick='enviar_libro(this, {0}, {1})'></a>\
                    ".format(str(item.pk), libro)
            else:
                send = ""
            json_data.append([
                item.current_date.strftime("%Y-%m-%d"),
                detail,
                item.libro_xml,
                ver + send,
            ])

        return json_data


class LibroDetailView(LoginRequiredMixin, DetailView):
    """
    Clase para el detalle de intercambio
    @author Rodrigo A. Boet (rodrigo.b at timgla.com)
    @copyright TIMG
    @date 12-08-2019
    @version 1.0
    """
    template_name = "libro_detail.html"
    model = Libro


@method_decorator(csrf_exempt, name='dispatch')
class LibroSendView(LoginRequiredMixin, View):
    """
    Clase para enviar el libro
    @author Rodrigo A. Boet (rodrigo.b at timgla.com)
    @copyright TIMG
    @date 14-08-2019
    @version 1.0
    """
    def post(self, request, pk, tipo_libro):
        """!
        Método para enviar el libro
        @param request Recibe el objeto de la petición
        @param pk Recibe el pk del libro
        @return: Objeto json con success y message
        """
        # tipo_libro = self.kwargs['tipo_libro']
        if tipo_libro == 0:
            tipo_libro_xml = dict_tipo_libro[tipo_libro]
        elif tipo_libro == 1:
            tipo_libro_xml = dict_tipo_libro[tipo_libro]
        try:
            libro = Libro.objects.get(pk=pk)
            if(not libro.enviada):
                signed_xml = libro.sign_base(tipo_libro_xml,'MENSUAL','TOTAL')
                compania = libro.fk_compania
                send_sii = sendToSii(compania,signed_xml,compania.pass_certificado)
                if(not send_sii['estado']):
                    messages.error(self.request, send_sii['msg'])
                    return JsonResponse(False, safe=False)
                else:
                    libro.enviada = True
                    libro.track_id = send_sii['track_id']
                    libro.periodo = datetime.datetime.strptime(libro.periodo, '%Y-%m')
                    libro.save()
                    messages.success(self.request, "Libro envíado con éxito")
                    return JsonResponse(True, safe=False)
            else:
                messages.info(self.request, "Éste libro ya fue envíado")
                return JsonResponse(True, safe=False)
        except Exception as e:
            print(e)
            messages.error(self.request, "Libro incorrecto")
            return JsonResponse(False, safe=False)


class LibroItems:

    def __init__(self, tipo_dte, n_folio, observaciones, exento, total):
        self.tipo_dte = tipo_dte
        self.n_folio = n_folio
        self.observaciones = observaciones
        self.exento = exento
        self.total = total


class CreateLibroCompra(LoginRequiredMixin, FormView):
    """
    Registra un nuevo libro

    @author Rodrigo A. Boet (rodrigo.b at timgla.com)
    @date 09-11-2019
    @version 1.0.0
    """
    form_class = formsetFac
    template_name = 'crear_libro_compra.html'
    success_url = '/libro/'
    model = DetailLibroCompra
    model_dte = DTE
    TWOPLACES = decimal.Decimal(10) ** -2

    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(*args, **kwargs)

        context['compania'] = self.kwargs['pk']
        return context

    def form_valid(self, form, *args, **kwargs):
        compania = self.kwargs['pk']

        periodo = self.request.POST.get('periodo', None)
        if periodo == '':
            messages.error(self.request, "El periodo es requerido")
            return super().form_invalid(form, *args, **kwargs)
        objects = []
        for libro_compra in form:
            tipo_dte = libro_compra.cleaned_data['tipo_dte']
            n_folio = libro_compra.cleaned_data['n_folio']
            observaciones = libro_compra.cleaned_data['observaciones']
            monto_exento = libro_compra.cleaned_data['monto_exento']
            monto_afecto = libro_compra.cleaned_data['monto_afecto']
            exento = '{0:.2f}'.format(monto_exento)
            total = '{0:.2f}'.format(monto_afecto)
            libro_items = LibroItems(tipo_dte, n_folio,
                                     observaciones, exento, total)
            objects.append(libro_items)

        xml = render_to_string('xml_lcv/resumen_periodo_compra.xml',
                               {'objects': objects})
        date_arr = periodo.split('/')
        current_date = date_arr[2]+"-"+date_arr[1]+"-"+date_arr[0]
        periodo = datetime.datetime.strptime(current_date, "%Y-%m-%d")
        try:
            compania = Compania.objects.get(pk=compania)
            libro = Libro(
                    fk_compania=compania,
                    current_date=current_date,
                    details=False,
                    libro_xml=xml,
                    tipo_libro=0,
                    periodo=periodo
                    )
            libro.save()
        except Exception as e:
            messages.error(self.request, e)
        for libro_compra in form:
            crear_libro = libro_compra.save(commit=False)
            crear_libro.fk_libro = libro
            crear_libro.save()

        self.success_url = reverse_lazy('libro:crear_libro_compra',
                                        kwargs={'pk': self.kwargs['pk']}
                                        )
        messages.success(self.request, "Libro de compra creado con éxito")
        return super().form_valid(form, *args, **kwargs)
