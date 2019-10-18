import os, datetime, json, decimal
from collections import OrderedDict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.shortcuts import (
    render, redirect
    )
from django.views.generic.base import TemplateView
from django.views.generic import ListView, CreateView

from conectores.models import *

from folios.models import Folio
from folios.exceptions import ElCafNoTieneMasTimbres, ElCAFSenEncuentraVencido

from utils.utils import validarModelPorDoc
from utils.CustomMixin import SeleccionarEmpresaView

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
        print(empresa)
        if not empresa:
            return HttpResponseRedirect('/')
        empresa_obj = Compania.objects.get(pk=empresa)
        if empresa_obj and self.request.user == empresa_obj.owner:
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

    def get_context_data(self, *args, **kwargs): 
        """
        Método para colocar contexto en la vista
        """
        context = super().get_context_data(*args, **kwargs)
        context['compania'] = self.kwargs.get('pk')
        context['impuesto'] = Compania.objects.get(pk=self.kwargs.get('pk')).tasa_de_iva
        if(self.request.method == 'POST'):
            dict_post = dict(self.request.POST.lists())
            productos = self.transform_product(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'],dict_post['descuento'],dict_post['exento'])
            context['productos'] = productos
        return context

    def get_success_url(self):
        """
        Método para retornar la url de éxito
        """
        return reverse_lazy(self.success_url, kwargs={'pk': self.kwargs['pk']})

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
        valid_r = self.validateProduct(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'],dict_post['descuento'])
        if(not valid_r['valid']):
            messages.error(self.request, valid_r['msg'])
            return super().form_invalid(form)
        productos = self.transform_product(dict_post['codigo'],dict_post['nombre'],dict_post['cantidad'],dict_post['precio'],dict_post['descuento'],dict_post['exento'])
        compania = Compania.objects.get(pk=self.kwargs.get('pk'))
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
            folio = Folio.objects.filter(empresa=self.kwargs.get('pk'),is_active=True,vencido=False,tipo_de_documento=self.object.tipo_dte).order_by('fecha_de_autorizacion').first()
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