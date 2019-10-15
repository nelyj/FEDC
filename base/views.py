import json, datetime, os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import (
    UpdateView, DeleteView
)

from django_datatables_view.base_datatable_view import BaseDatatableView
from django_weasyprint import WeasyTemplateResponseMixin

from conectores.models import Compania

from facturas.models import Factura

from folios.exceptions import ElCafNoTieneMasTimbres, ElCAFSenEncuentraVencido
from folios.models import Folio

from utils.utils import validarModelPorDoc, nombreTimbrePorDoc
from utils.views import (
    sendToSii, LoginRequeridoPerAuth
)
from .constants import NOMB_DOC, LIST_DOC


class SendToSiiView(LoginRequeridoPerAuth, View):
    """!
    Envia el documento al sii

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 24-09-2019
    @version 1.0.0
    """
    group_required = [u"Super Admin", u"Admin", u"Invitado"]

    def get(self, request, **kwargs):
        """
        Método para manejar la petición post
        """
        print(kwargs['pk'])
        print(kwargs['dte'])
        model, url = validarModelPorDoc(kwargs['dte'])
        model = model.objects.get(pk=kwargs['pk'])
        send_sii = sendToSii(model.compania,model.dte_xml,model.compania.pass_certificado)
        if(not send_sii['estado']):
            return JsonResponse({'status':send_sii['estado'], 'msg':send_sii['msg']})
        else:
            model.track_id = send_sii['track_id']
            model.save()
            return JsonResponse({'status':send_sii['estado'], 'msg':'Envíado con éxito'})


class AjaxGenericListDTETable(LoginRequiredMixin, BaseDatatableView):
    """!
    Prepara la data para mostrar en el datatable

    @author Rodrigo A. Boet (rodrigo.b at timgla.com)
    @date 19-09-2019
    @version 1.0.0
    """
    # The model we're going to show
    model = Factura
    columns = ['pk', 'numero_factura', 'compania', 'n_folio']
    # define column names that will be used in sorting
    # order is important and should be same as order of columns
    # displayed by datatables. For non sortable columns use empty
    # value like ''
    order_columns = ['pk', 'numero_factura', 'compania', 'n_folio']
    # set max limit of records returned, this is used to protect our site if someone tries to attack our site
    # and make it return huge amount of data
    max_display_length = 500


    def __init__(self):
        super(AjaxGenericListDTETable, self).__init__()

    def get_initial_queryset(self):
        """!
        Consulta el modelo Intercambio

        @return: Objeto de la consulta
        """
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        # You should not filter data returned here by any filter values entered by Intercambio. This is because
        # we need some base queryset to count total number of records.
        tipo_doc = self.kwargs['dte']
        self.model, url = validarModelPorDoc(tipo_doc)
        if self.request.GET.get(u'sistema', None) == 'True':
            return self.model.objects.filter(compania=self.kwargs['pk'], track_id=None)
        return self.model.objects.filter(compania=self.kwargs['pk']).exclude(track_id=None)

    def filter_queryset(self, qs):
        # use parameters passed in GET request to filter queryset

        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs_params = None
            q = Q(pk__istartswith=search)|Q(compania__razon_social__icontains=search)|Q(n_folio__icontains=search)|Q(numero_factura__icontains=search)
            qs_params = qs_params | q if qs_params else q
            qs = qs.filter(qs_params)
        return qs

    def prepare_results(self, qs):
        """!
        Prepara la data para mostrar en el datatable
        @return: Objeto json con los datos del DTE
        """
        # prepare list with output column data
        tipo_doc = self.kwargs['dte']
        self.model, url_model = validarModelPorDoc(tipo_doc)
        json_data = []
        for item in qs:
            if self.request.GET.get(u'sistema', None) == 'True':
                url = str(reverse_lazy('base:send_sii', kwargs={'pk':item.pk, 'dte':self.kwargs['dte']}))
                boton_enviar_sii = '<a href="#" onclick=send_to_sii("'+url+'")\
                                    class="btn btn-success">Enviar al Sii</a> '
                url_eliminar = str(reverse_lazy(url_model+'eliminar_dte', kwargs={'pk':item.pk}))
                boton_eliminar = "<a data-toggle='modal' data-target='#myModal' \
                    class='btn btn-danger' \
                    onclick=eliminar_dte('"+url_eliminar+"')>Eliminar</a>\
                     "
                boton_editar = '<a href="{0}" \
                                    class="btn btn-info">Editar</a> '.format(reverse_lazy(url_model+'actualizar', 
                                                                                          kwargs={'pk':item.pk, 'comp':self.kwargs['pk']}))
                botones_acciones = boton_enviar_sii + boton_editar +boton_eliminar
            else:
                boton_estado = '<a href="{0}"\
                                class="btn btn-success">Ver Estado</a> '.format(reverse_lazy('notaCredito:ver_estado_nc', kwargs={'pk':self.kwargs['pk'], 'slug':item.numero_factura}))
                boton_imprimir_doc = '<a  id="edit_foo" href="{0}"\
                                     target="_blank" class="btn btn-info">Imprimir</a> '.format(reverse_lazy('base:imprimir_factura', kwargs={'pk':self.kwargs['pk'], 'slug':item.numero_factura, 'doc':tipo_doc}))
                boton_imprimir_con = '<a  id="edit_foo" href="{0}?impre=cont"\
                                     target="_blank" class="btn btn-warning">Impresion continua</a>'.format(reverse_lazy('base:imprimir_factura', kwargs={'pk':self.kwargs['pk'], 'slug':item.numero_factura, 'doc':tipo_doc}))
                botones_acciones = boton_estado + boton_imprimir_doc + boton_imprimir_con
            json_data.append([
                item.numero_factura,
                item.compania.razon_social,
                item.n_folio,
                botones_acciones
            ])
        return json_data


class ImprimirFactura(LoginRequiredMixin, TemplateView, WeasyTemplateResponseMixin):
    """!
    Class para imprimir la factura en PDF

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 21-03-2019
    @version 1.0.0
    """
    template_name = "pdf/factura.pdf.html"
    model = Factura

    def dispatch(self, request, *args, **kwargs):
        num_factura = self.kwargs['slug']
        compania = self.kwargs['pk']
        tipo_doc = self.kwargs['doc']
        impre_cont = request.GET.get('impre')
        self.model, url_model = validarModelPorDoc(tipo_doc)
        if impre_cont == 'cont':
            self.template_name = "pdf/impresion.continua.pdf.html"
        if tipo_doc in LIST_DOC:
            try:
                factura = self.model.objects.select_related().get(numero_factura=num_factura, compania=compania)
                return super().dispatch(request, *args, **kwargs)
            except Exception as e:
                print(e)
                factura = self.model.objects.select_related().filter(numero_factura=num_factura, compania=compania)
                if len(factura) > 1:
                    messages.error(self.request, 'Existe mas de un registro con el mismo numero de factura: {0}'.format(num_factura))
                    return redirect(reverse_lazy(url_model+'lista-enviadas', kwargs={'pk': compania}))
                else:
                    messages.error(self.request, "No se encuentra registrada esta factura: {0}".format(str(num_factura)))
                    return redirect(reverse_lazy(url_model+'lista-enviadas', kwargs={'pk': compania}))
        else:
            messages.error(self.request, "No existe este tipo de documento: {0}".format(str(tipo_doc)))
            return redirect(reverse_lazy(url_model+'lista-enviadas', kwargs={'pk': compania}))

    def get_context_data(self, *args, **kwargs):
        """!
        Method to handle data on get

        @date 21-03-2019
        @return Returns dict with data
        """
        context = super().get_context_data(*args, **kwargs)
        num_factura = self.kwargs['slug']
        compania = self.kwargs['pk']
        tipo_doc = self.kwargs['doc']

        context['factura'] = self.model.objects.select_related().get(numero_factura=num_factura, compania=compania)
        context['nombre_documento'] = NOMB_DOC[tipo_doc]
        etiqueta=self.kwargs['slug'].replace('º','')
        context['etiqueta'] = etiqueta

        prod = context['factura'].productos.replace('\'{','{').replace('}\'','}').replace('\'',"\"")

        productos = json.loads(prod)
        context['productos'] = productos
        nombre_timbre = nombreTimbrePorDoc(self.kwargs['doc'])
        ruta = settings.STATIC_URL +nombre_timbre+'/'+etiqueta+'/timbre.jpg'
        context['ruta']=ruta
        return context

from collections import OrderedDict
from django.forms.models import model_to_dict
class UpdateDTEView(LoginRequiredMixin, UpdateView):
    """
    """
    model = Factura
    success_url ='actualizar:actualizar'

    def get_context_data(self, *args, **kwargs):
        """
        Método para colocar contexto en la vista
        """
        context = super().get_context_data(*args, **kwargs)
        context['compania'] = self.kwargs.get('comp')
        context['impuesto'] = Compania.objects.get(pk=self.kwargs.get('comp')).tasa_de_iva
        if(self.request.method == 'POST'):
            dict_post = dict(self.request.POST.lists())
            productos = self.transform_product(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'])
            context['productos'] = productos

            return context

        prod = context['form']['productos'].value().replace('\'{','{').replace('}\'','}').replace('\'',"\"")

        productos = json.loads(prod)
        productos = productos
        productos = self.reverse_product(
                    productos,
                    Compania.objects.get(pk=self.kwargs.get('comp')))
        productos = self.dict_product(productos['productos'])

        context['productos'] = productos
        return context

    def dict_product(self, prod):
        """
        Método para transformar los productos en listas de diccionarios
        @param prod Recibe diccionario de productos
        @return retorna los productos como lista de diccionarios
        """
        products = []
        for producto in prod:
            new_prod = {}
            new_prod['nombre'] = producto['nombre']
            new_prod['codigo'] = producto['codigo']
            new_prod['cantidad'] = int(producto['amount'])
            new_prod['precio'] = float(producto['precio'])
            products.append(new_prod)
        return products

    def reverse_product(self, prod_dict, compania):
        """
        Método para armar el json de producto
        @param prod_dict Recibe el diccionarios de productos
        @param compania Recibe el objecto de la compañia
        @return retorna la data en un diccionario
        """
        total = 0
        products = []
        for producto in prod_dict:
            new_prod = OrderedDict()
            new_prod['nombre'] = producto['item_name']
            new_prod['nombre'] = producto['description']
            new_prod['codigo'] = producto['item_code']
            new_prod['cantidad'] = producto['qty']
            new_prod['precio'] = producto['base_net_rate']
            amount = producto['qty'] * producto['base_net_rate']
            new_prod['amount'] = amount
            products.append(new_prod)
            total += new_prod['amount']
        neto = total - (total*(compania.tasa_de_iva/100))
        data = OrderedDict()
        data['productos'] = products
        data['neto'] = neto
        data['total'] = total
        return data

    def transform_product(self, code, name, qty, price):
        """
        Método para transformar los productos en listas de diccionarios
        @param code Recibe la lista con los códigos
        @param name Recibe la lista con los nombres
        @param qty Recibe la lista con las cantidades
        @param price Recibe la lista con los precios
        @return retorna los productos como lista de diccionarios
        """
        products = []
        for i in range(len(code)):
            new_prod = {}
            new_prod['nombre'] = name[i]
            new_prod['codigo'] = code[i]
            new_prod['cantidad'] = int(qty[i])
            new_prod['precio'] = float(price[i])
            products.append(new_prod)
        return products

    def load_product(self, prod_dict, compania):
        """
        Método para armar el json de producto
        @param prod_dict Recibe el diccionarios de productos
        @param compania Recibe el objecto de la compañia
        @return retorna la data en un diccionario
        """
        total = 0
        products = []
        for producto in prod_dict:
            new_prod = OrderedDict()
            new_prod['item_name'] = producto['nombre']
            new_prod['description'] = producto['nombre']
            new_prod['item_code'] = producto['codigo']
            new_prod['qty'] = producto['cantidad']
            new_prod['base_net_rate'] = producto['precio']
            new_prod['amount'] = new_prod['qty'] * new_prod['base_net_rate']
            products.append(new_prod)
            total += new_prod['amount']
        neto = total - (total*(compania.tasa_de_iva/100))
        data = OrderedDict()
        data['productos'] = products
        data['neto'] = neto
        data['total'] = total
        return data

    def validateProduct(self, code, name, qty, price):
        """
        Método para validar el producto
        @param code Recibe la lista con los códigos
        @param name Recibe la lista con los nombres
        @param qty Recibe la lista con las cantidades
        @param price Recibe la lista con los precios
        @return retorna los productos como lista de diccionarios
        """
        for i in range(len(code)):
            for j in range(i+1,len(code)):
                if(code[i]==code[j]):
                    return {'valid':False,'msg':'No pueden existir códigos dúplicados'}
        for q in qty:
            try:
                int(q)
            except Exception as e:
                return {'valid':False,'msg':'Las cantidades deben ser enteras'}
        for p in price:
            try:
                float(p)
            except Exception as e:
                return {'valid':False,'msg':'El precio debe ser un número'}
        return {'valid':True}

    def form_valid(self, form, **kwargs):
        """
        Método si el formulario es válido
        """

        dict_post = dict(self.request.POST.lists())
        datetime_object = datetime.datetime.now()
        fecha = datetime.datetime.strptime(dict_post['fecha'][0], '%d/%m/%Y')
        if 'codigo' not in self.request.POST or 'nombre' not in self.request.POST\
            or 'cantidad' not in self.request.POST or 'precio' not in self.request.POST:
            messages.error(self.request, "Debe cargar al menos un producto")
            return super().form_invalid(form)
        if(len(dict_post['codigo']) == 0 or len(dict_post['nombre']) == 0\
            or len(dict_post['cantidad']) == 0 or len(dict_post['precio']) == 0):
            messages.error(self.request, "Debe cargar al menos un producto")
            return super().form_invalid(form)
        if(len(dict_post['codigo']) != len(dict_post['nombre']) or\
            len(dict_post['cantidad']) != len(dict_post['precio']) or\
            len(dict_post['codigo']) != len(dict_post['cantidad']) or\
            len(dict_post['cantidad']) != len(dict_post['nombre'])):
            messages.error(self.request, "Faltan valores por llenar en la tabla")
            return super().form_invalid(form)

        if fecha > datetime_object:
            messages.error(self.request, "La fecha no puede ser mayor a la fecha actual, por favor verifica nuevamente la fecha")
            return super().form_invalid(form)
        valid_r = self.validateProduct(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'])
        if(not valid_r['valid']):
            messages.error(self.request, valid_r['msg'])
            return super().form_invalid(form)
        productos = self.transform_product(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'])
        compania = Compania.objects.get(pk=self.kwargs.get('comp'))
        pass_certificado = compania.pass_certificado
        diccionario_general = self.load_product(productos,compania)
        self.object = form.save(commit=False)
        diccionario_general['rut'] = self.object.rut
        diccionario_general['numero_factura'] = self.object.numero_factura
        diccionario_general['senores'] = self.object.senores
        diccionario_general['giro'] = self.object.giro
        diccionario_general['direccion'] = self.object.region
        diccionario_general['comuna'] = self.object.comuna
        try:
            diccionario_general['ciudad_receptora'] = self.object.ciudad_receptora
        except:
            pass
        diccionario_general['forma_pago'] = form.cleaned_data['forma_pago']
        # Se verifica el folio
        try:
            folio = Folio.objects.filter(empresa=self.kwargs.get('comp'),is_active=True,vencido=False,tipo_de_documento=33).order_by('fecha_de_autorizacion').first()
            if not folio:
                raise Folio.DoesNotExist
        except Folio.DoesNotExist:  
            messages.error(self.request, "No posee folios para asignacion de timbre")
            return super().form_invalid(form)
        try:
            folio.verificar_vencimiento()
        except ElCAFSenEncuentraVencido:
            messages.error(self.request, "El CAF se encuentra vencido")
            return super().form_invalid(form)
        try:
            self.object.recibir_folio(folio)
        except (ElCafNoTieneMasTimbres, ValueError):
            messages.error(self.request, "Ya ha consumido todos sus timbres")
            return super().form_invalid(form)
        self.object.productos = json.dumps(diccionario_general['productos'])
        # Se generan los XML
        response_dd = self.model._firmar_dd(diccionario_general, folio, self.object)
        documento_firmado = self.model.firmar_documento(response_dd,diccionario_general,folio, compania, self.object, pass_certificado)
        documento_final_firmado = self.model.firmar_etiqueta_set_dte(compania, folio, documento_firmado)
        caratula_firmada = self.model.generar_documento_final(compania,documento_final_firmado,pass_certificado)
        self.object.dte_xml = caratula_firmada
        self.object.neto = diccionario_general['neto']
        self.object.total = diccionario_general['total']
        self.object.iva = compania.tasa_de_iva
        self.object.compania = compania
        self.object.save()
        # Se crea el arhivo del xml
        try:
            xml_dir = settings.MEDIA_ROOT +'notas_de_credito'+'/'+self.object.numero_factura
            if(not os.path.isdir(xml_dir)):
                os.makedirs(xml_dir)
            f = open(xml_dir+'/'+self.object.numero_factura+'.xml','w')
            f.write(caratula_firmada)
            f.close()
        except Exception as e:
            messages.error(self.request, 'Ocurrio el siguiente Error: '+str(e))
            return super().form_valid(form)
        messages.success(self.request, "Se Actualizo el documento con éxito")
        return super().form_valid(form)

    def get_success_url(self):
        """
        Método para retornar la url de éxito
        """
        return reverse_lazy(self.success_url, kwargs={'pk': self.kwargs['pk'], 'comp': self.kwargs.get('comp')})


class DeleteDTEView(LoginRequiredMixin, DeleteView):
    """
    """
    model = Factura
    template_name = "eliminar_dte.html"
