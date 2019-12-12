import datetime
import decimal
import dicttoxml
import json
import os
import re

from collections import OrderedDict

from django.core import serializers
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView
from django.views.generic.base import TemplateView
from django.views.generic.edit import (
    UpdateView, DeleteView, FormView
)

from django_weasyprint import WeasyTemplateResponseMixin

from django_datatables_view.base_datatable_view import BaseDatatableView

from conectores.models import *
from conectores.sdkConectorERP import SdkConectorERP

from folios.models import Folio
from folios.exceptions import ElCafNoTieneMasTimbres, ElCAFSenEncuentraVencido

from utils.constantes import (
    documentos_dict, FORMA_DE_PAGO
)
from utils.CustomMixin import SeleccionarEmpresaView
from utils.views import (
    sendToSii, DecodeEncodeChain
)
from utils.SIISdk import SII_SDK

from .models import DTE
from .forms import FormCreateDte


class StartDte(SeleccionarEmpresaView):
    """
    Selecciona la empresa

    @author Rodrigo A. Boet (rodrigo.b at timgla.com)
    @date 14-10-2019
    @version 1.0.0
    """

    def post(self, request):
        empresa = int(request.POST.get('empresa'))
        if not empresa:
            return HttpResponseRedirect('/')
        empresa_obj = Compania.objects.get(pk=empresa)
        if self.request.GET.get(u'enviadas', None):
            return redirect(str(reverse_lazy('dte:lista_dte', kwargs={'pk':empresa}))+"?enviadas=1")
        elif self.request.GET.get(u'no_enviadas_erp', None) == '1':
            return HttpResponseRedirect(reverse_lazy('dte:lista_dte_erp', kwargs={'pk':empresa}))
        elif empresa_obj and self.request.user == empresa_obj.owner:
            return HttpResponseRedirect(reverse_lazy('dte:lista_dte', kwargs={'pk':empresa}))
        else:
            return HttpResponseRedirect('/')


class DteSistemaView(LoginRequiredMixin, TemplateView):
    """!
    Clase para ver el listado de notas del sistema

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 14-10-2019
    @version 1.0.0
    """
    template_name = 'dte_enviadas.html'

    def get_context_data(self, *args, **kwargs):
        """
        Método para colocar contexto en la vista
        """
        context = super().get_context_data(*args, **kwargs)
        if not self.request.GET.get(u'enviadas', None):
            context['sistema'] = True
        context['compania'] = self.kwargs.get('pk')
        return context


class DteCreateView(LoginRequiredMixin, CreateView):
    """!
    Clase para generar una nota de crédito por el sistema

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 14-10-2019
    @version 1.0.0
    """
    template_name = "crear_dte.html"
    model = DTE
    form_class = FormCreateDte
    success_url = 'dte:lista_dte'
    pk = None

    def get_context_data(self, *args, **kwargs):
        """
        Método para colocar contexto en la vista
        """
        context = super().get_context_data(*args, **kwargs)
        context['compania'] = self.kwargs.get('pk') if self.kwargs.get('pk', None) else self.pk
        context['impuesto'] =  Compania.objects.get(pk=self.pk).tasa_de_iva if self.pk else Compania.objects.get(pk=self.kwargs.get('pk')).tasa_de_iva
        if(self.request.method == 'POST'):
            dict_post = dict(self.request.POST.lists())
            productos = self.transform_product(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'],dict_post['descuento'],dict_post['exento'])
            context['productos'] = productos
        return context

    def get_form_kwargs(self):
        """
        Método para pasar datos al formulario
        """
        kwargs = super().get_form_kwargs()
        kwargs.update({'compania': self.kwargs.get('pk')})
        return kwargs

    def get_success_url(self):
        """
        Método para retornar la url de éxito
        """
        pk = self.pk if self.pk else self.kwargs['pk']
        return reverse_lazy(self.success_url, kwargs={'pk': pk})

    def form_valid(self, form, **kwargs):
        """
        Método si el formulario es válido
        """

        dict_post = dict(self.request.POST.lists())
        datetime_object = datetime.datetime.now()
        if dict_post.get('fecha', None)[0]:
            fecha = datetime.datetime.strptime(dict_post['fecha'][0], '%d/%m/%Y')
        else:
            messages.error(self.request, "Falta el campo fecha")
            return super().form_invalid(form)
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
        valid_r = self.validateProduct(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'],dict_post['descuento'])
        if(not valid_r['valid']):
            messages.error(self.request, valid_r['msg'])
            return super().form_invalid(form)
        productos = self.transform_product(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'],dict_post['descuento'],dict_post['exento'])
        compania =  Compania.objects.get(pk=self.pk) if self.pk else Compania.objects.get(pk=self.kwargs.get('pk'))
        pass_certificado = compania.pass_certificado
        descuento_global = {
            'descuento': form.cleaned_data['descuento_global'],
            'tipo_descuento': form.cleaned_data['tipo_descuento']
        }
        diccionario_general = self.load_product(productos,compania,descuento_global)
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
            folio = Folio.objects.filter(empresa=compania.pk,is_active=True,vencido=False,tipo_de_documento=self.object.tipo_dte).order_by('fecha_de_autorizacion').first()
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
        caratula_firmada = self.model.generar_documento_final(compania,documento_final_firmado,pass_certificado, self.object)
        self.object.dte_xml = caratula_firmada
        self.object.neto = diccionario_general['neto']
        self.object.total = diccionario_general['total']
        self.object.iva = compania.tasa_de_iva
        self.object.compania = compania
        self.object.save()
        messages.success(self.request, "Se creó el documento con éxito")
        return super().form_valid(form)

    def form_invalid(self, form, **kwargs):
        """
        Método si el formulario es válido
        """
        return super().form_invalid(form)

    def transform_product(self, code, name, qty, price, discount, exempt):
        """
        Método para transformar los productos en listas de diccionarios
        @param code Recibe la lista con los códigos
        @param name Recibe la lista con los nombres
        @param qty Recibe la lista con las cantidades
        @param price Recibe la lista con los precios
        @param discount Recibe la lista con los descuentos
        @param exempt Recibe la lista con los productos exentos
        @return retorna los productos como lista de diccionarios
        """
        products = []
        for i in range(len(code)):
            new_prod = {}
            new_prod['nombre'] = name[i]
            new_prod['codigo'] = code[i]
            new_prod['cantidad'] = int(qty[i])
            new_prod['precio'] = float(price[i])
            new_prod['descuento'] = int(discount[i]) if discount[i] else discount[i]
            new_prod['exento'] = int(exempt[i])
            products.append(new_prod)
        return products

    def load_product(self, prod_dict, compania, descuento):
        """
        Método para armar el json de producto
        @param prod_dict Recibe el diccionarios de productos
        @param compania Recibe el objecto de la compañia
        @param descuento Recibe si tiene descuento global
        @return retorna la data en un diccionario
        """
        neto = 0
        exento = 0
        products = []
        for producto in prod_dict:
            new_prod = OrderedDict()
            new_prod['item_name'] = producto['nombre']
            new_prod['description'] = producto['nombre']
            new_prod['item_code'] = producto['codigo']
            new_prod['qty'] = producto['cantidad']
            new_prod['base_net_rate'] = producto['precio']
            new_prod['discount'] = producto['descuento']
            new_prod['exento'] = producto['exento']
            if(producto['descuento']):
                f_total = new_prod['qty'] * new_prod['base_net_rate']
                new_prod['amount'] = f_total - (f_total*(producto['descuento']/100))
            else:
                new_prod['amount'] = new_prod['qty'] * new_prod['base_net_rate']
            products.append(new_prod)
            if(new_prod['exento']):
                exento += new_prod['amount']
            else:
                neto += new_prod['amount']
        data = OrderedDict()
        data['productos'] = products
        data['neto'] = decimal.Decimal(neto)
        data['exento'] = decimal.Decimal(exento)
        data['iva'] = decimal.Decimal(neto*(compania.tasa_de_iva/100))
        if(descuento['descuento']):
            nuevo_exento = descuento['descuento']
            if(descuento['tipo_descuento']=="%"):
                nuevo_exento = decimal.Decimal(data['neto']) * (descuento['descuento']/100)
            data['neto'] -= nuevo_exento
            data['exento'] += nuevo_exento
        data['total'] = data['exento'] + data['neto'] + data['iva']
        return data

    def validateProduct(self, code, name, qty, price, discount):
        """
        Método para validar el producto
        @param code Recibe la lista con los códigos
        @param name Recibe la lista con los nombres
        @param qty Recibe la lista con las cantidades
        @param price Recibe la lista con los precios
        @param discount Recibe la lista con descuentos
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
        for d in discount:
            if(d):
                try:
                    d = int(d)
                    if(d<0):
                        return {'valid':False,'msg':'El descuento no puede ser negativo'}
                    elif(d>=100):
                        return {'valid':False,'msg':'El descuento no puede ser mayor o igual 100%'}
                except Exception as e:
                    print(e)
                    return {'valid':False,'msg':'Los descuentos deben ser enteros'}
        return {'valid':True}


class UpdateDTEView(LoginRequiredMixin, UpdateView):
    """!
    Clase para actualizar un dte por el sistema

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 15-10-2019
    @version 1.0.0
    """
    model = DTE
    template_name = "crear_dte.html"
    form_class = FormCreateDte
    class_create = DteCreateView()

    def get_context_data(self, *args, **kwargs):
        """
        Método para colocar contexto en la vista
        """
        context = super().get_context_data(*args, **kwargs)
        context['compania'] = self.kwargs.get('comp')
        context['impuesto'] = Compania.objects.get(pk=self.kwargs.get('comp')).tasa_de_iva
        if(self.request.method == 'POST'):
            dict_post = dict(self.request.POST.lists())
            productos = self.class_create.transform_product(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'], dict_post['descuento'], dict_post['exento'])
            context['productos'] = productos

            return context
        prod = context['form']['productos'].value().replace('\'{','{').replace('}\'','}').replace('\'',"\"")
        descuento_global = {
            'descuento': context['form']['descuento_global'].value(),
            'tipo_descuento': context['form']['tipo_descuento'].value()
        }
        productos = json.loads(prod)
        productos = productos
        print(productos)
        productos = self.reverse_product(
                    productos,
                    Compania.objects.get(pk=self.kwargs.get('comp')),
                    descuento_global
                    )
        productos = self.dict_product(productos.get('productos'))

        context['productos'] = productos
        return context

    def get_form_kwargs(self):
        """
        Método para pasar datos al formulario
        """
        kwargs = super().get_form_kwargs()
        kwargs.update({'compania': self.kwargs.get('pk')})
        return kwargs

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
            new_prod['cantidad'] = int(producto.get('cantidad', 0))
            new_prod['precio'] = float(producto.get('precio')) if producto.get('precio') else 0
            new_prod['descuento'] = 0 if producto.get('exento', None) is None else float(producto.get('exento'))
            new_prod['exento'] = 0 if producto.get('exento', 0) is None else float(producto.get('exento'))

            products.append(new_prod)
        return products

    def reverse_product(self, prod_dict, compania, descuento):
        """
        Método para armar el json de producto
        @param prod_dict Recibe el diccionarios de productos
        @param compania Recibe el objecto de la compañia
        @return retorna la data en un diccionario
        """
        neto = 0
        exento = 0
        products = []
        for producto in prod_dict:
            new_prod = OrderedDict()
            new_prod['nombre'] = producto.get('item_name', None)
            new_prod['nombre'] = producto.get('description', None)
            new_prod['codigo'] = producto.get('item_code', None)
            new_prod['cantidad'] = producto.get('qty', 0)
            new_prod['precio'] = producto.get('base_net_rate', None)
            if producto.get('discount'):
                new_prod['descuento'] = float(producto.get('discount'))
            elif producto.get('discount_percentage'):
                new_prod['descuento'] = float(producto.get('discount_percentage'))
            else:
                new_prod['descuento'] = 0
            new_prod['exento'] = producto.get('exento')
            if(new_prod['descuento']):
                f_total = producto.get('qty', 0) * producto.get('base_net_rate', 0)
                new_prod['amount'] = f_total - (f_total*(new_prod['descuento']/100))
            else:
                new_prod['amount'] = producto.get('qty', 0) * producto.get('base_net_rate', 0)
            products.append(new_prod)
            if(new_prod['exento']):
                exento += new_prod['amount']
            else:
                neto += new_prod['amount']
        data = OrderedDict()
        data['productos'] = products
        data['neto'] = decimal.Decimal(neto)
        data['exento'] = decimal.Decimal(exento)
        data['iva'] = decimal.Decimal(neto*(compania.tasa_de_iva/100))
        if(descuento['descuento']):
            nuevo_exento = descuento['descuento']
            if(descuento['tipo_descuento']=="%"):
                nuevo_exento = decimal.Decimal(data['neto']) * (descuento['descuento']/100)
            data['neto'] -= nuevo_exento
            data['exento'] += nuevo_exento
        data['total'] = decimal.Decimal(data['exento']) + decimal.Decimal(data['neto']) + decimal.Decimal(data['iva'])
        return data


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
        valid_r = self.class_create.validateProduct(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'], dict_post['descuento'])
        if(not valid_r['valid']):
            messages.error(self.request, valid_r['msg'])
            return super().form_invalid(form)
        productos = self.class_create.transform_product(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'], dict_post['descuento'], dict_post['exento'])
        compania = Compania.objects.get(pk=self.kwargs.get('comp'))
        pass_certificado = compania.pass_certificado
        descuento_global = {
            'descuento': form.cleaned_data['descuento_global'],
            'tipo_descuento': form.cleaned_data['tipo_descuento']
        }
        diccionario_general = self.class_create.load_product(productos,compania, descuento_global)
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
            folio = Folio.objects.filter(empresa=self.kwargs.get('comp'), rango_desde__lte=self.object.n_folio, rango_hasta__gte=self.object.n_folio, tipo_de_documento=self.object.tipo_dte).order_by('fecha_de_autorizacion').first()
            if not folio:
                raise Folio.DoesNotExist
        except Folio.DoesNotExist:  
            messages.error(self.request, "No existe folios con este rango")
            return super().form_invalid(form)
        self.object.productos = json.dumps(diccionario_general['productos'])
        # Se generan los XML
        response_dd = self.model._firmar_dd(diccionario_general, folio, self.object)
        documento_firmado = self.model.firmar_documento(response_dd,diccionario_general,folio, compania, self.object, pass_certificado)
        documento_final_firmado = self.model.firmar_etiqueta_set_dte(compania, folio, documento_firmado)
        caratula_firmada = self.model.generar_documento_final(compania,documento_final_firmado,pass_certificado, self.object)
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
        return reverse_lazy('dte:actualizar', kwargs={'pk': self.kwargs['pk'], 'comp': self.kwargs.get('comp')})


class DeleteDTEView(LoginRequiredMixin, DeleteView):
    """
    """
    model = DTE
    template_name = "eliminar_dte.html"
    success_url = 'dte:lista_dte'

    def get_success_url(self):
        """
        Método para retornar la url de éxito
        """
        return reverse_lazy(self.success_url, kwargs={'pk': self.kwargs['comp']})


class ImprimirFactura(LoginRequiredMixin, TemplateView, WeasyTemplateResponseMixin):
    """!
    Class para imprimir la factura en PDF

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 21-03-2019
    @version 1.0.0
    """
    template_name = "pdf/factura.pdf.html"
    model = DTE

    def dispatch(self, request, *args, **kwargs):
        num_factura = self.kwargs['slug']
        compania = self.kwargs['pk']
        impre_cont = request.GET.get('impre')
        #self.model, url_model = validarModelPorDoc(tipo_doc)
        if impre_cont == 'cont':
            self.template_name = "pdf/impresion.continua.pdf.html"
        #if tipo_doc in LIST_DOC:
        try:
            factura = self.model.objects.select_related().get(numero_factura=num_factura, compania=int(compania))
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            print(e)
            factura = self.model.objects.select_related().filter(numero_factura=num_factura, compania=compania)
            if len(factura) > 1:
                messages.error(self.request, 'Existe mas de un registro con el mismo numero de factura: {0}'.format(num_factura))
                return redirect(str(reverse_lazy('dte:lista_dte', kwargs={'pk':compania}))+"?enviadas=1")
            else:
                messages.error(self.request, "No se encuentra registrada esta factura: {0}".format(str(num_factura)))
                return redirect(str(reverse_lazy('dte:lista_dte', kwargs={'pk':compania}))+"?enviadas=1")
        #else:
        #    messages.error(self.request, "No existe este tipo de documento: {0}".format(str(tipo_doc)))
        #    return redirect(reverse_lazy(url_model+'lista-enviadas', kwargs={'pk': compania}))

    def get_context_data(self, *args, **kwargs):
        """!
        Method to handle data on get

        @date 21-03-2019
        @return Returns dict with data
        """
        context = super().get_context_data(*args, **kwargs)
        num_factura = self.kwargs['slug']
        compania = self.kwargs['pk']

        context['factura'] = self.model.objects.select_related().get(numero_factura=num_factura, compania=compania)
        context['nombre_documento'] = documentos_dict[context['factura'].tipo_dte]
        etiqueta = self.kwargs['slug'].replace('º','')
        context['etiqueta'] = etiqueta
        context['referencia'] = context['factura'].ref_factura

        prod = context['factura'].productos.replace('\'{','{').replace('}\'','}').replace('\'',"\"")

        productos = json.loads(prod)
        context['productos'] = productos
        exento = 0

        for prod in productos:
            if prod['discount']:
                f_total = prod['qty'] * prod['base_net_rate']
                total = f_total - (f_total*(prod['discount']/100))
                exento += decimal.Decimal(total)

        if(context['factura'].descuento_global):
            nuevo_exento = context['factura'].descuento_global
            if(context['factura'].tipo_descuento == "%"):
                nuevo_exento = decimal.Decimal(context['factura'].neto) * decimal.Decimal(context['factura'].descuento_global/100)
            exento += nuevo_exento
        context['exento'] = decimal.Decimal(exento) 
        context['total'] = decimal.Decimal(context['exento']) + decimal.Decimal(context['factura'].neto) + decimal.Decimal(context['factura'].compania.tasa_de_iva)

        ruta = settings.STATIC_URL + context['factura'].numero_factura + '/timbre.jpg'
        context['ruta']=ruta
        return context


class AjaxGenericListDTETable(LoginRequiredMixin, BaseDatatableView):
    """!
    Prepara la data para mostrar en el datatable

    @author Rodrigo A. Boet (rodrigo.b at timgla.com)
    @date 19-09-2019
    @version 1.0.0
    """
    # The model we're going to show
    model = DTE
    columns = ['pk', 'numero_factura', 'compania', 'n_folio', 'tipo_dte']
    # define column names that will be used in sorting
    # order is important and should be same as order of columns
    # displayed by datatables. For non sortable columns use empty
    # value like ''
    order_columns = ['pk', '-numero_factura', 'compania', 'n_folio', 'tipo_dte']
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
        #qs_params = Q(tipo_dte=33)|Q(tipo_dte=56)|Q(tipo_dte=61)
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

        json_data = []
        for item in qs:
            if self.request.GET.get(u'sistema', None) == 'True':
                url = str(reverse_lazy('dte:send_sii', kwargs={'pk':item.pk}))
                boton_enviar_sii = '<a href="#" onclick=send_to_sii("'+url+'")\
                                    class="btn btn-success" id="send_dte" >Enviar al Sii</a> '
                url_eliminar = str(reverse_lazy('dte:eliminar_dte', kwargs={'pk':item.pk,'comp':self.kwargs['pk']}))
                boton_eliminar = "<a data-toggle='modal' data-target='#myModal' \
                    class='btn btn-danger' \
                    onclick=eliminar_dte('"+url_eliminar+"')>Eliminar</a>\
                     "
                boton_editar = '<a href="{0}" \
                                    class="btn btn-info">Editar</a> '.format(reverse_lazy('dte:actualizar', 
                                                                                          kwargs={'pk':item.pk, 'comp':self.kwargs['pk']}))
                botones_acciones = boton_enviar_sii + boton_editar +boton_eliminar
            else:
                boton_estado = '<a href="{0}"\
                                class="btn btn-success">Ver Estado</a> '.format(reverse_lazy('dte:ver_estado', kwargs={'pk':self.kwargs['pk'], 'slug':item.numero_factura}))
                boton_imprimir_doc = '<a  id="edit_foo" href="{0}"\
                                     target="_blank" class="btn btn-info">Imprimir</a> '.format(reverse_lazy('dte:imprimir_dte', kwargs={'pk':self.kwargs['pk'], 'slug':item.numero_factura}))
                boton_imprimir_con = '<a  id="edit_foo" href="{0}?impre=cont"\
                                     target="_blank" class="btn btn-warning">Impresion continua</a>'.format(reverse_lazy('dte:imprimir_dte', kwargs={'pk':self.kwargs['pk'], 'slug':item.numero_factura}))
                botones_acciones = boton_estado + boton_imprimir_doc + boton_imprimir_con
            json_data.append([
                item.numero_factura,
                item.compania.razon_social,
                item.n_folio,
                documentos_dict[item.tipo_dte],
                botones_acciones
            ])
        return json_data


class SendToSiiView(LoginRequiredMixin, View):
    """!
    Envia el documento al sii

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 24-09-2019
    @version 1.0.0
    """
    pk = None 
    caratula = None

    def get(self, request, **kwargs):
        """
        Método para manejar la petición get
        """
        pk = self.pk if self.pk is not None else kwargs['pk']
        caratula = self.caratula
        if caratula:
            send_sii = sendToSii(model.compania,caratula,model.compania.pass_certificado)
            if(not send_sii['estado']):
                return JsonResponse({'status':send_sii['estado'], 'msg':send_sii['msg']})
            else:
                model.track_id = send_sii['track_id']
                model.save()
                return JsonResponse({'status':send_sii['estado'], 'msg':'Envíado con éxito'})
        else:
            model = DTE.objects.get(pk=pk)
            send_sii = sendToSii(model.compania,model.dte_xml,model.compania.pass_certificado)
            if(not send_sii['estado']):
                return JsonResponse({'status':send_sii['estado'], 'msg':send_sii['msg']})
            else:
                model.track_id = send_sii['track_id']
                model.save()
                return JsonResponse({'status':send_sii['estado'], 'msg':'Envíado con éxito'})


class GetDteDataView(LoginRequiredMixin, View):
    """!
    Carga los datos del dte

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 22-10-2019
    @version 1.0.0
    """
    def get(self, request, **kwargs):
        """
        Método para manejar la petición get
        """
        try:
            dte = DTE.objects.filter(pk=kwargs['pk']).get()
            compania = dte.compania
            if(compania.owner==self.request.user):
                serialized_dte = serializers.serialize('json',
                    [dte], fields=['senores',
                        'direccion', 'comuna', 'region', 'ciudad_receptora',
                        'giro', 'rut', 'fecha', 'productos', 'total',
                        'forma_pago', 'descuento_global', 'glosa_descuento',
                        'tipo_descuento'])
                dte_object = json.loads(serialized_dte)
                return JsonResponse({'success':True, 'data':dte_object})
            else:
                return JsonResponse({'success':False, 'msg':'No puedes hacer eso'})
        except Exception as e:
            print(e)
            return JsonResponse({'success':False, 'msg':str(e)})


class VerEstado(LoginRequiredMixin, TemplateView):
    """!
    Clase para ver el estado de envio de una factura

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 04-04-2019
    @version 1.0.0
    """
    template_name = "estado_factura.html"
    model = DTE

    def get_context_data(self, *args, **kwargs):
        """!
        Method to handle data on get

        @date 04-04-2019
        @return Returns dict with data
        """
        context = super().get_context_data(*args, **kwargs)
        num_factura = self.kwargs['slug']
        compania = self.kwargs['pk']

        factura = self.model.objects.get(numero_factura=num_factura, compania=compania)
        context['factura'] = factura
        
        estado = self.get_invoice_status(factura,factura.compania,)

        if(not estado['estado']):
            messages.error(self.request, estado['msg'])
        else:
            context['estado'] = estado['status']
            context['glosa'] = estado['glosa']

        return context

    def get_invoice_status(self,factura,compania):
        """
        Método para enviar la factura al sii
        @param factura recibe el objeto de la factura
        @param compania recibe el objeto compañia
        @return dict con la respuesta
        """
        try:
            sii_sdk = SII_SDK(settings.SII_PRODUCTION)
            seed = sii_sdk.getSeed()
            try:
                sign = sii_sdk.signXml(seed, compania, compania.pass_certificado)
                token = sii_sdk.getAuthToken(sign)
                if(token):
                    print(token)
                    estado = sii_sdk.checkDTEstatus(compania.rut,factura.track_id,token)
                    return {'estado':True,'status':estado['estado'],'glosa':estado['glosa']} 
                else:
                    return {'estado':False,'msg':'No se pudo obtener el token del sii'}
            except Exception as e:
                print(e)
                return {'estado':False,'msg':'Ocurrió un error al firmar el documento'}
            return {'estado':True}
        except Exception as e:
            print(e)
            return {'estado':False,'msg':'Ocurrió un error al comunicarse con el sii'}


class ListarDteDesdeERP(LoginRequiredMixin, TemplateView):
    """
    Clase para listar todos los DTE que se encuentran en el ERPNext

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 20-11-2019
    @version 1.0.0
    """
    template_name = 'listar_dte_erp.html'
    decode_encode = DecodeEncodeChain()

    def dispatch(self, *args, **kwargs):

        compania = self.kwargs.get('pk')

        usuario = Conector.objects.filter(empresa=compania).first()

        if not usuario:

            messages.info(self.request,
                          "No posee conectores asociados a esta empresa")
            return HttpResponseRedirect(reverse_lazy(
                                        'facturas:seleccionar-empresa'
                                        ))

        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compania = self.kwargs.get('pk')
        context['id_empresa'] = compania

        try:
            usuario = Conector.objects.filter(t_documento='33',empresa=compania).first()
        except Exception as e:
            print(e)

        passw = usuario.password.strip()
        passw = self.decode_encode.decrypt(passw).decode("utf-8")
        erp = SdkConectorERP(usuario.url_erp, usuario.usuario, passw)
        try:
            response, session = erp.login()
        except Exception as e:
            messages.warning(self.request, "No se pudo establecer conexion con el ERP Next, se genera el siguiente error: "+str(e))
        try:
            lista = erp.list_limit(session)
            lista_guia = erp.list_delivery(session)
            erp_data = json.loads(lista.text)

            erp_data_guia = json.loads(lista_guia.text)

        except Exception as e:
            session.close()
            messages.warning(self.request, "Error al obtener el listado de dte del ERP Next, se genera el siguiente error: "+str(e))
            return context

        # Todas las facturas, guias y boletas sin discriminacion 
        data = erp_data['data']
        data_guia = erp_data_guia.get('data', [])

        # Consulta en la base de datos todos los numeros de facturas
        # cargadas por la empresa correspondiente para hacer una comparacion
        # con el ERP y eliminar las que ya se encuentran cargadas
        enviadas = [factura.numero_factura for factura in DTE.objects.filter(compania=compania).only('numero_factura')]

        # Agrega todos los dte
        # y crea una nueva lista con todas las facturas
        solo_facturas  = []
        for i , item in enumerate(data):

            if item['name'].startswith(''):

                solo_facturas.append(item['name'])
        solo_guias = []
        for i , item in enumerate(data_guia):

            solo_guias.append(item['name'])

        # Verifica si la factura que vienen del ERP 
        # ya se encuentran cargadas en el sistema
        # y en ese caso las elimina de la lista
        solo_nuevas = []
        for i , item in enumerate(solo_facturas):

            #valor = item.replace('º','')
            valor = re.sub('[^a-zA-Z0-9 \n\.]', '', item)
            valor = valor.replace(' ', '')
            if not valor in enviadas:
                solo_nuevas.append(item)

        for i , item in enumerate(solo_guias):
            valor = re.sub('[^a-zA-Z0-9 \n\.]', '', item)
            valor = valor.replace(' ', '')
            if not valor in enviadas:
                solo_nuevas.append(item)

        context['detail']=[]
        for tmp in solo_nuevas:
            try:
                aux = erp.list(session, str(tmp))
                if aux.status_code == 200:
                    context['detail'].append(json.loads(aux.text))
                elif aux.status_code == 404:
                    aux = erp.list_delivery(session, str(tmp))
                    if aux.text:
                        context['detail'].append(json.loads(aux.text))
            except Exception as e:
                session.close()
                messages.warning(self.request, "Error al obtener el listado de dte del ERP Next, se genera el siguiente error: "+str(e))
        session.close()
        return context


class SaveDteErp(LoginRequiredMixin, FormView):
    """
    Clase para controlar el proceso de guardado

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 22-11-2019
    @version 1.0.0
    """
    model = DTE
    template_name = "crear_dte.html"
    form_class = FormCreateDte
    decode_encode = DecodeEncodeChain()
    class_create = DteCreateView()
    class_update = UpdateDTEView()

    def type_dte(self, tipo_documento):
        """
        """
        if tipo_documento.startswith('Boleta'):
            return 39
        elif tipo_documento.startswith('Factura'):
            return 33
        elif tipo_documento.startswith('Nota de Debito'):
            return 61
        elif tipo_documento.startswith('Nota de Credito'):
            return 56
        elif tipo_documento.startswith('Guía de Despacho'):
            return 52
        else:
            return ''

    def get_initial(self):
        initial = super().get_initial()
        url = self.kwargs['slug']
        compania = self.kwargs['pk']

        try:
            usuario = Conector.objects.filter(empresa=compania).first()
        except Exception as e:
            print(e)

        passw = usuario.password.strip()
        passw = self.decode_encode.decrypt(passw).decode("utf-8")

        erp = SdkConectorERP(usuario.url_erp, usuario.usuario, passw)
        try:
            response, session = erp.login()
        except Exception as e:
            messages.warning(self.request, "No se pudo establecer conexion con el ERP Next, se genera el siguiente error: "+str(e))
        try:
            aux = erp.list(session, url)
            aux=json.loads(aux.text)
            session.close()
            context={}
            context['factura'] = dict(zip(aux['data'].keys(), aux['data'].values()))
            context['factura']['sales_team'] = context['factura']['sales_team'][0]['sales_person']
            context['factura']['total_taxes_and_charges'] = round(abs(float(context['factura']['total_taxes_and_charges'])))
        except Exception as e:
            print(e)
            messages.warning(self.request, "No se pudo establecer conexion con el ERP Next, se genera el siguiente error: "+str(e))

        valor = re.sub('[^a-zA-Z0-9 \n\.]', '', self.kwargs['slug'])
        valor = valor.replace(' ', '')
        initial['numero_factura']=valor
        tipo_dte = self.type_dte(context.get('factura').get('tipo_de_documento', None))
        initial['tipo_dte'] = tipo_dte
        try:
            initial['senores']=context['factura']['customer_name']
        except Exception as e:
            initial['senores']=""
        try:
            initial['comuna']=context['factura']['comuna']
        except Exception as e:
            initial['comuna']=""
        try:
            initial['ciudad_receptora']=context['factura']['ciudad_receptora']
        except Exception as e:
            initial['ciudad_receptora']=""
        try:
            initial['giro']=context['factura']['giro']
        except Exception as e:
            self.form_class.base_fields['giro'].initial=""
        # self.form_class.base_fields['condicion_venta'].initial=context['factura']['']
        # self.form_class.base_fields['vencimiento'].initial=context['factura']['']
        try:
            initial['vendedor']=context['factura']['sales_team']
        except Exception as e:
            initial['vendedor']=""
        try:
            initial['rut']=context['factura']['rut']
        except Exception as e:
            initial['rut']=""

        try:
            fecha = datetime.datetime.strptime(context['factura']['posting_date'], '%Y-%m-%d')
            initial['fecha'] = fecha.strftime("%d/%m/%Y")
        except Exception as e:
            initial['fecha']=""
        # self.form_class.base_fields['guia'].initial=context['factura']['']
        try:
            initial['orden_compra']=context['factura']['po_no']
        except Exception as e:
            initial['orden_compra']=""
        try:
            initial['nota_venta']=context['factura']['orden_de_venta']
        except Exception as e:
            initial['nota_venta']=""
        try:
            initial['productos']=context['factura']['items']
        except Exception as e:
            initial['productos']=""
        try:
            initial['monto_palabra']=context['factura']['in_words']
        except Exception as e:
            initial['monto_palabra']=""
        try:
            initial['neto']=context['factura']['net_total']
        except Exception as e:
            initial['neto']=""
        # self.form_class.base_fields['excento'].initial=context['factura']['']
        try:
            initial['iva']=context['factura']['total_taxes_and_charges']
        except Exception as e:
            initial['iva']=""
        try:
            initial['total']=context['factura']['rounded_total']
        except Exception as e:
            initial['total']=""
        return initial

    def get_form_kwargs(self):
        """
        Método para pasar datos al formulario
        """
        kwargs = super().get_form_kwargs()
        kwargs.update({'compania': self.kwargs.get('pk')})
        return kwargs

    def get_context_data(self, *args, **kwargs):
        """
        Método para colocar contexto en la vista
        """
        context = super().get_context_data(*args, **kwargs)
        context['impuesto'] = Compania.objects.get(pk=self.kwargs.get('pk')).tasa_de_iva
        context['compania'] = self.kwargs.get('pk')
        try:
            context['impuesto'] = Compania.objects.get(pk=self.kwargs.get('comp')).tasa_de_iva
        except:
            pass
        if(self.request.method == 'POST'):
            dict_post = dict(self.request.POST.lists())
            productos = self.class_create.transform_product(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'], dict_post['descuento'], dict_post['exento'])
            context['productos'] = productos

            return context
        if context['form']['productos'].value():
            prod = str(context['form']['productos'].value()).replace('\'{','{').replace('}\'','}').replace('\'',"\"")

            descuento_global = {
                'descuento': context['form']['descuento_global'].value(),
                'tipo_descuento': context['form']['tipo_descuento'].value()
            }

            productos = json.loads(prod)
            productos = productos
            productos = self.class_update.reverse_product(
                        productos,
                        Compania.objects.get(pk=self.kwargs.get('pk')),
                        descuento_global
                        )
            productos = self.class_update.dict_product(productos.get('productos'))

            context['productos'] = productos
        return context

    def form_valid(self, form, **kwargs):
        #DteCreateView.as_view(pk=self.kwargs.get('pk')).form_valid(form)(self.request)
        return DteCreateView.as_view(pk=self.kwargs.get('pk'))(self.request)#.form_valid(form)

    def get_success_url(self):
        """
        Método para retornar la url de éxito
        """
        return reverse_lazy('dte:save_dte_erp', kwargs={'pk': self.kwargs['pk'], 'slug': self.kwargs.get('slug')})


class SendDteErpToSii(LoginRequiredMixin, View):
    """
    Clase para controlar el proceso de envio directo al Sii

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 27-11-2019
    @version 1.0.0
    """
    model = DTE
    decode_encode = DecodeEncodeChain()
    erp_dte = SaveDteErp()
    class_update = UpdateDTEView()
    class_create = DteCreateView()

    def get(self, request, *args, **kwargs):
        """
        Metodo para obtener el numeo de DTE y procesarlo desde el ERP al Sii y guardarlo en la plataforma
        """

        compania = kwargs.get('pk')
        urls = request.GET.getlist('pk', [])

        try:
            usuario = Conector.objects.filter(empresa=compania).first()
        except Exception as e:
            print(e)

        passw = usuario.password.strip()
        passw = self.decode_encode.decrypt(passw).decode("utf-8")
        erp = SdkConectorERP(usuario.url_erp, usuario.usuario, passw)
        try:
            response, session = erp.login()
        except Exception as e:
            print(e)
            messages.warning(self.request, "No se pudo establecer conexion con el ERP Next, se genera el siguiente error: "+str(e))

        for url in urls:
            dte_list = []
            #url = url.replace(' ', '%20')
            #print(url)
            try:
                aux = erp.list(session, url)
                if aux.status_code == 200:
                    aux = json.loads(aux.text)
                elif aux.status_code == 404:
                    aux = erp.list_delivery(session, url)
                    if aux.text:
                        aux = json.loads(aux.text)

                context = {}
                context['factura'] = dict(zip(aux['data'].keys(),
                                          aux['data'].values()))

                if len(context['factura']['sales_team']) > 0:
                    context['factura']['sales_team'] = context['factura']['sales_team'][0].get('sales_person', None)
                else:
                    context['factura']['sales_team'] = context['factura']['sales_team']
                context['factura']['total_taxes_and_charges'] = round(abs(float(context['factura']['total_taxes_and_charges'])))
            except Exception as e:
                print(e)
                context = {}
                context['factura'] = {}
                messages.warning(self.request, "No se pudo establecer conexion con el ERP Next, se genera el siguiente error: "+str(e))

            cleanr = re.compile('<.*?>')
            valor = re.sub('[^a-zA-Z0-9 \n\.]', '', url)
            valor = valor.replace(' ', '')
            numero_factura = valor
            tipo_dte = self.erp_dte.type_dte(str(context.get('factura').get('tipo_de_documento', None)))
            senores = context.get('factura').get('customer_name', None)
            comuna = context.get('factura').get('comuna_receptora') if context.get('factura').get('comuna_receptora') else 'Arica'
            shipping_address = context.get('factura').get('shipping_address')
            shipping_address = shipping_address.replace('\n', ' ') if shipping_address else 'Direccion'
            shipping_address = re.sub(cleanr, '', shipping_address)
            ciudad_receptora = shipping_address
            giro = context.get('factura').get('giro')
            vendedor = context.get('factura').get('sales_team')
            rut = context.get('factura').get('rut')
            if rut is None:
                return JsonResponse({'status':False, 'msg':'El DTE no tiene Rut'})
            try:
                fecha = datetime.datetime.strptime(context.get('factura').get('posting_date'), '%Y-%m-%d')
                fecha = fecha.strftime('%Y-%m-%d')
            except:
                fecha = datetime.datetime.now()
                fecha = fecha.strftime('%Y-%m-%d')
            orden_compra = context.get('factura').get('po_no')
            nota_venta = context.get('factura').get('orden_de_venta')
            productos = context.get('factura').get('items')
            monto_palabra = context.get('factura').get('in_words')
            neto = context.get('factura').get('net_total')
            descuento = context.get('factura').get('additional_discount_percentage')
            descuento = descuento if descuento is not None else 0
            iva = context.get('factura').get('total_taxes_and_charges')
            total = context.get('factura').get('rounded_total')

            prod = str(productos).replace('\'{','{').replace('}\'','}').replace('\'',"\"")

            descuento_global = {
                'descuento': float(descuento),
                'tipo_descuento': '%'
            }

            productos_json = json.loads(prod)
            productos = productos_json
            productos = self.class_update.reverse_product(
                        productos,
                        Compania.objects.get(pk=compania),
                        descuento_global
                        )
            productos = self.class_update.dict_product(productos.get('productos'))

            productos = productos
            dte = DTE(
                    compania=Compania.objects.get(pk=compania),
                    numero_factura=numero_factura,
                    senores=senores,
                    direccion=shipping_address,
                    comuna=comuna,
                    region=shipping_address,
                    ciudad_receptora=ciudad_receptora,
                    giro=giro,
                    rut=rut,
                    fecha=fecha,
                    productos=productos_json,
                    neto=neto,
                    iva=iva,
                    total=total,
                    tipo_dte=tipo_dte,
                    tipo_descuento='%',
                    descuento_global=float(descuento),
                    forma_pago=FORMA_DE_PAGO[0][0],
                )
            # Se verifica el folio

            try:
                folio = Folio.objects.filter(empresa=compania, is_active=True,
                                             vencido=False,
                                             tipo_de_documento=tipo_dte).order_by('fecha_de_autorizacion').first()
                if not folio:
                    raise Folio.DoesNotExist
            except Folio.DoesNotExist:
                return JsonResponse({'status':False, 'msg':"No posee folios para asignacion de timbre"})
            try:
                folio.verificar_vencimiento()
            except ElCAFSenEncuentraVencido:
                return JsonResponse({'status':False, 'msg':"El CAF se encuentra vencido"})
            try:
                dte.recibir_folio(folio)
            except (ElCafNoTieneMasTimbres, ValueError):
                return JsonResponse({'status':False, 'msg':"Ya ha consumido todos sus timbres"})


            compania =  Compania.objects.get(pk=compania)
            pass_certificado = compania.pass_certificado

            diccionario_general = self.class_create.load_product(productos,
                                                                 compania,
                                                                 descuento_global)
            diccionario_general['rut'] = dte.rut
            diccionario_general['numero_factura'] = dte.numero_factura
            diccionario_general['senores'] = dte.senores
            diccionario_general['giro'] = dte.giro
            diccionario_general['direccion'] = dte.region
            diccionario_general['comuna'] = dte.comuna

            diccionario_general['ciudad_receptora'] = dte.ciudad_receptora

            diccionario_general['forma_pago'] = dte.forma_pago

            response_dd = self.model._firmar_dd(diccionario_general, folio, dte)

            documento_firmado = self.model.firmar_documento(response_dd,
                                                            diccionario_general,
                                                            folio,
                                                            compania,
                                                            dte,
                                                            pass_certificado)
            dte.save()
            dte_list.append(dte.pk)
        # end for
        session.close()
        if len(dte_list) > 1 or dte.tipo_dte == 39:
            dte_boletas = DTE.objects.filter(compania_id=compania.pk, pk__in=dte_list).exclude(status='ENVIADA')

            documento_final_firmado = self.model.firmar_etiqueta_set_dte(compania,
                                                                     folio,
                                                                     dte_boletas, dte_boletas.count())
        else:
            dte_boletas = None
            documento_final_firmado = self.model.firmar_etiqueta_set_dte(compania,
                                                                     folio,
                                                                     documento_firmado)
        print(documento_final_firmado)
        caratula_firmada = self.model.generar_documento_final(compania,
                                                              documento_final_firmado,
                                                              pass_certificado, dte)
        if dte_boletas:
            for dte_b in dte_boletas:
                dte_b.dte_xml = caratula_firmada
                dte_b.save()
            return SendToSiiView.as_view(caratula=caratula_firmada)(self.request)
        else:
            dte.dte_xml = caratula_firmada
            dte.save()
            return SendToSiiView.as_view(pk=dte.pk)(self.request) #.get()


class DeatailDTE(LoginRequiredMixin, TemplateView):
    template_name = 'detail_dte_erp.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            usuario = Conector.objects.filter(pk=1).first()
        except Exception as e:
            print(e)
        decode_encode = DecodeEncodeChain()
        passw = usuario.password.strip()
        passw = decode_encode.decrypt(passw).decode("utf-8")

        erp = SdkConectorERP(usuario.url_erp, usuario.usuario, passw)
        response, session = erp.login()

        aux = erp.list(session, str(kwargs['slug']))

        aux=json.loads(aux.text)
        xml = dicttoxml.dicttoxml(aux)
        context['keys'] = list(aux['data'].keys())
        context['values'] = list(aux['data'].values())
        session.close()
        return context
