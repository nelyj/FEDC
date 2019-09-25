from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic.base import TemplateView

from django_weasyprint import WeasyTemplateResponseMixin

from facturas.models import Factura

from utils.utils import validarModelPorDoc
from utils.views import (
    sendToSii, LoginRequeridoPerAuth
)

from .constants import NOMB_DOC, LIST_DOC


class SendToSiiView(LoginRequeridoPerAuth, View):
    """!
    Envia el documento al sii

    @author Rodrigo Boet (rudmanmrrod at gmail.com)
    @date 24-09-2019
    @version 1.0.0
    """
    group_required = [u"Super Admin", u"Admin", u"Invitado"]

    def get(self, request, **kwargs):
        """
        Método para manejar la petición post
        """
        print(kwargs['pk'])
        print(kwargs['company'])
        print(kwargs['dte'])
        model = validarModelPorDoc(kwargs['dte'])
        model = model.objects.get(pk=kwargs['pk'])
        send_sii = sendToSii(model.compania,model.dte_xml,compania.pass_certificado)
        if(not send_sii['estado']):
            return JsonResponse({'status':send_sii['estado'], 'msg':send_sii['msg']})
        else:
            model.track_id = send_sii['track_id']
            model.save()
            return JsonResponse({'status':send_sii['estado'], 'msg':'Envíado con éxito'})


class ImprimirFactura(LoginRequiredMixin, TemplateView, WeasyTemplateResponseMixin):
    """!
    Class para imprimir la factura en PDF

    @author Rodrigo Boet (rudmanmrrod at gmail.com)
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

        if impre_cont == 'cont':
            self.template_name = "pdf/impresion.continua.pdf.html"
        if tipo_doc in LIST_DOC:
            self.model = validarModelPorDoc(tipo_doc)

            try:
                factura = self.model.objects.select_related().get(numero_factura=num_factura, compania=compania)
                return super().dispatch(request, *args, **kwargs)
            except Exception as e:
                print(e)
                factura = self.model.objects.select_related().filter(numero_factura=num_factura, compania=compania)
                if len(factura) > 1:
                    messages.error(self.request, 'Existe mas de un registro con el mismo numero de factura: {0}'.format(num_factura))
                    return redirect(reverse_lazy('facturas:lista-enviadas', kwargs={'pk': compania}))
                else:
                    messages.error(self.request, "No se encuentra registrada esta factura: {0}".format(str(num_factura)))
                    return redirect(reverse_lazy('facturas:lista-enviadas', kwargs={'pk': compania}))
        else:
            messages.error(self.request, "No existe este tipo de documento: {0}".format(str(tipo_doc)))
            return redirect(reverse_lazy('facturas:lista-enviadas', kwargs={'pk': compania}))

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
        ruta = settings.STATIC_URL +'facturas'+'/'+etiqueta+'/timbre.jpg'
        context['ruta']=ruta
        return context