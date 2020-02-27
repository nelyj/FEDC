import imaplib, email, os, json

import pytz

from datetime import datetime
from base64 import b64decode,b64encode

from django.conf import settings
from django.db.models import Q
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView, RedirectView, ListView, DetailView
from django_datatables_view.base_datatable_view import BaseDatatableView

from utils.views import (
    LoginRequeridoPerAuth
)
from conectores.models import Compania
from .models import Intercambio, DteIntercambio


class SeleccionarEmpresaIntercambioView(LoginRequiredMixin, TemplateView):
  """
  Clase para seleccionar la empresa en el intercambio
  @author Alberto Rincones (alberto at timg.cl)
  @copyright TIMG
  @date 08-04-19 (dd-mm-YY)
  @version 1.0
  """
  template_name = 'intercambio_seleccionar_empresa.html'

  def get_context_data(self, *args, **kwargs): 

    context = super().get_context_data(*args, **kwargs)
    context['empresas'] = Compania.objects.all()
    if context['empresas']:
        context['tiene_empresa'] = True
    else:
        messages.info(self.request, "Registre una empresa para continuar")
        context['tiene_empresa'] = False
    return context

  def post(self, request):

    empresa = int(request.POST.get('empresa'))

    if not empresa:
        return HttpResponseRedirect('/')
    empresa_obj = Compania.objects.get(pk=empresa)
    if empresa_obj and self.request.user == empresa_obj.owner:

        return HttpResponseRedirect(reverse_lazy('intercambios:lista', kwargs={'pk':empresa}))
    else:
        return HttpResponseRedirect('/')

class IntercambiosListView(LoginRequiredMixin, TemplateView):
  """
  Clase para el listado de intercambios
  @author Alberto Rincones (alberto at timg.cl)
  @copyright TIMG
  @date 01-04-19 (dd-mm-YY)
  @version 1.0
  """
  template_name = "intercambio_list.html"

  def get_queryset(self):
    pk=self.kwargs.get('pk')
    user = self.request.user
    compania = Compania.objects.get(pk=pk)

    queryset = Intercambio.objects.filter(receptor=compania).order_by('-fecha_de_recepcion')
    print(queryset)
    return queryset



class IntercambiosDetailView(LoginRequiredMixin, DetailView):
  """
  Clase para el detalle de intercambio
  @author Alberto Rincones (alberto at timg.cl)
  @copyright TIMG
  @date 01-04-19 (dd-mm-YY)
  @version 1.0
  """

  template_name="intercambio_detail.html"

  def get_context_data(self, *args, **kwargs): 

    context = super().get_context_data(*args, **kwargs)
    compania_pk=self.kwargs.get('pk')
    intercambio_pk=self.kwargs.get('inter_pk')
    intercambio = get_object_or_404(
      Intercambio, 
      receptor=compania_pk, 
      pk=intercambio_pk
    )
    context['dte_intercambio'] = DteIntercambio.objects.select_related().filter(id_intercambio=intercambio)
    return context

  def get_object(self):
    compania_pk=self.kwargs.get('pk')
    intercambio_pk=self.kwargs.get('inter_pk')
    intercambio = get_object_or_404(
      Intercambio, 
      receptor=compania_pk, 
      pk=intercambio_pk
    )
    
    return intercambio

from .tasks import updateInbox




class ListIboxAjaxView(LoginRequeridoPerAuth, BaseDatatableView):

    """!
    Prepara la data para mostrar en el datatable

    @author Rodrigo A. Boet (rodrigo.b at timgla.com)
    @date 16-07-2019
    @version 1.0.0
    """
    # The model we're going to show
    model = Intercambio
    # define the columns that will be returned
    columns = ['pk', 'fecha_de_recepcion', 'remisor', 'titulo', 'cantidad_dte']
    # define column names that will be used in sorting
    # order is important and should be same as order of columns
    # displayed by datatables. For non sortable columns use empty
    # value like ''
    order_columns = ['-fecha_de_recepcion', 'remisor', 'titulo', 'cantidad_dte']
    # set max limit of records returned, this is used to protect our site if someone tries to attack our site
    # and make it return huge amount of data
    max_display_length = 500
    group_required = [u"Super Admin", 'Admin']

    def __init__(self):
        super(ListIboxAjaxView, self).__init__()

    def get_initial_queryset(self):
        """!
        Consulta el modelo Intercambio

        @return: Objeto de la consulta
        """
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        # You should not filter data returned here by any filter values entered by Intercambio. This is because
        # we need some base queryset to count total number of records.
        return self.model.objects.all().order_by('-fecha_de_recepcion')

    def filter_queryset(self, qs):
        # use parameters passed in GET request to filter queryset

        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs_params = None
            q = Q(pk__istartswith=search)|Q(fecha_de_recepcion__icontains=search)|Q(remisor__icontains=search)|Q(titulo__icontains=search)|Q(cantidad_dte__istartswith=search)
            qs_params = qs_params | q if qs_params else q
            qs = qs.filter(qs_params)
        return qs

    def prepare_results(self, qs):
        """!
        Prepara la data para mostrar en el datatable
        @return: Objeto json con los datos del intercambio
        """
        # prepare list with output column data
        json_data = []
        for item in qs:
            try:
              fecha = item.fecha_de_recepcion.strftime("%Y-%m-%d %H:%M:%S")
            except:
              fecha = "Error al obtener fecha"
            detail = "<a data-toggle='modal' data-target='#myModal' \
                    class='btn btn-block btn-info btn-xs fa fa-search' \
                    onclick='modal_inbox({0})'></a>\
                    ".format(str(item.pk))
            json_data.append([
                str(item.pk),
                fecha,
                item.remisor,
                item.titulo,
                item.cantidad_dte,
                detail
            ])
            
        return json_data