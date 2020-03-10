import datetime, os

from base64 import b64encode
from collections import defaultdict

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string

from bs4 import BeautifulSoup
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from pdf417gen import encode, render_image

from certificados.models import Certificado
from conectores.constantes import (COMUNAS, ACTIVIDADES)
from conectores.models import Compania

from folios.models import Folio
from folios.exceptions import ElCafNoTieneMasTimbres
from mixins.models import CreationModificationDateMixin
from utils.constantes import (TIPO_DOCUMENTO, FORMA_DE_PAGO, 
    VALOR_DESCUENTO, CODIGO_REFERENCIA
)
from utils.SIISdk import SII_SDK
from utils.utils import validate_string_number


class DTE(CreationModificationDateMixin):
    """!
    Modelo DTE
    """
    compania = models.ForeignKey(Compania, on_delete=models.CASCADE)
    ref_factura = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    numero_factura = models.CharField(max_length=128, db_index=True, validators=[validate_string_number])
    senores = models.CharField(max_length=128)
    direccion = models.CharField(max_length=128)
    comuna = models.CharField(max_length=128, choices=COMUNAS)
    region = models.CharField(max_length=128)
    ciudad_receptora = models.CharField(max_length=128)
    giro = models.CharField(max_length=128)
    rut = models.CharField(max_length=128)
    fecha = models.DateField(blank=True)
    productos = models.TextField(blank=True, null=True)
    neto = models.CharField(max_length=128, blank=True, null=True)
    iva = models.CharField(max_length=128, blank=True, null=True)
    total = models.CharField(max_length=128, blank=True, null=True)
    n_folio = models.IntegerField(null=True, default=0)
    status = models.CharField(max_length=128,blank=True, null=True)
    tipo_dte = models.PositiveSmallIntegerField(choices=TIPO_DOCUMENTO)
    forma_pago = models.PositiveSmallIntegerField(choices=FORMA_DE_PAGO)
    cod_ref = models.PositiveSmallIntegerField(choices=CODIGO_REFERENCIA,blank=True, null=True)
    razon_ref = models.CharField(max_length=128,blank=True, null=True)
    descuento_global = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    glosa_descuento = models.CharField(max_length=45, blank=True, null=True)
    tipo_descuento = models.CharField(max_length=45, blank=True, null=True, choices=VALOR_DESCUENTO)
    dte_xml = models.TextField(null=True, blank=True)
    track_id = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        ordering = ('numero_factura',)
        verbose_name = 'DTE'
        verbose_name_plural = 'DTE'
        unique_together = (("compania", "numero_factura"),)
    
    def __str__(self):
        return self.numero_factura

    def recibir_folio(self, folio):
        if isinstance(folio, Folio):
            try:
                n_folio = folio.asignar_folio()
            except (ElCafNoTieneMasTimbres, ValueError):
                raise ElCafNoTieneMasTimbres
            assert type(n_folio) == int, "folio no es entero"
            self.n_folio = n_folio 
        else: 
            return 

    def _firmar_dd(data, folio, instance): 
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        productos=data.get('productos')
        primero=productos[0].get('item_name')
        data['primero']=primero
        # Ajustados montos y rut para el xml
        if('k' in folio.rut):
            folio.rut = folio.rut.replace('k','K')
        if('k' in data['rut']):
            data['rut'] = data['rut'].replace('k','K')
        if('.' in data['rut']):
            data['rut'] = data['rut'].replace('.','')
        data['neto']=str(round(float(data['neto'])))
        data['total']=str(round(abs(float(data['total']))))

        sin_aplanar = render_to_string('snippets/dd_tag.xml', {'data':data,'folio':folio, 'instance':instance, 'timestamp':timestamp})
        digest_string = sin_aplanar.replace('\n','').replace('\t','').replace('\r','')
        RSAprivatekey = RSA.importKey(folio.pem_private)
        private_signer = PKCS1_v1_5.new(RSAprivatekey)
        digest = SHA.new()
        digest.update(digest_string.encode('iso8859-1'))
        sign = private_signer.sign(digest)
        firma = '<FRMT algoritmo="SHA1withRSA">{}</FRMT>'.format(b64encode(sign).decode())
        sin_aplanar += firma
        carpeta=data['numero_factura'].replace('º','')

        try:
            xml_dir = settings.MEDIA_ROOT +carpeta
            if(not os.path.isdir(xml_dir)):
                os.makedirs(xml_dir)
            codes = encode(sin_aplanar,columns=10, security_level=5)
            image = render_image(codes,scale=1, ratio=1)
            image.save(xml_dir+'/timbre'+'.jpg')
        except Exception as e:
            print(e)
        return sin_aplanar

    
    def firmar_documento(etiqueta_DD, datos, folio, compania, instance, pass_certificado):

        """
        Llena los campos de la etiqueta <Documento>, y la firma usando la 
        plantilla signature.xml. Retorna la etiquta <Documento> con sus datos y 
        la correspondiente firma con la clave privada cargada por el usuario en
        el certificado.
        """

        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # Llena los datos de la plantilla Documento_tag.xml con la informacion pertinente
        diccionario = defaultdict(dict)
        for x,y in ACTIVIDADES:
            diccionario[x]=y
        compania.giro=diccionario.get(str(compania.giro))
        compania.giro=compania.giro[1 : -1]
        compania.actividad_principal=compania.actividad_principal[1:-1]

        # Ajustados los montos de productos para el xml
        for producto in datos['productos']:
            if(producto['discount']):
                producto['discount'] = round(abs(producto['discount']))
                discount_amount = producto['base_net_rate'] * (producto['discount']/100)
                producto['discount_amount'] = round(abs(discount_amount))
            producto['qty'] = str(abs(producto['qty']))
            producto['base_net_rate'] = str(producto['base_net_rate'])
            producto['amount'] = round(abs(producto['amount']))

        # Ajustados valores para el xml
        if('k' in folio.rut):
            folio.rut = folio.rut.replace('k','K')
        if('k' in compania.rut):
            compania.rut = compania.rut.replace('k','K')
        if('k' in datos['rut']):
            datos['rut'] = datos['rut'].replace('k','K')
        datos['numero_factura'] = datos['numero_factura'].replace('º','')
        datos['neto']=str(round(abs(float(datos['neto']))))
        datos['total']=str(round(abs(float(datos['total']))))
        if(datos['exento']):
            datos['monto_exento'] = str(round(abs(float(datos['exento']))))

        datos['iva']=str(round(abs(int(datos['iva']))))

        ref = ''
        if(instance.tipo_dte==56 or instance.tipo_dte==61):
            documento_tag = 'snippets/documento_tag_ncd.xml'
            ref = instance.ref_factura
        else:
            documento_tag = 'snippets/documento_tag.xml'
        # Llena los datos de la plantilla Documento_tag.xml con la informacion pertinente
        documento_sin_aplanar = render_to_string(
            documento_tag, {
                'datos':datos,
                'folio':folio, 
                'compania':compania, 
                'timestamp':timestamp,
                'DD':etiqueta_DD,
                'instance':instance,
                'ref':ref
            })


        sii_sdk = SII_SDK(settings.SII_PRODUCTION)
        set_dte_sin_aplanar = sii_sdk.generalSign(compania,documento_sin_aplanar,pass_certificado)

        return set_dte_sin_aplanar

    def firmar_etiqueta_set_dte(compania, folio, etiqueta_Documento, nro_dte=1):


        # Genera timestamp en formato correspondiente
        timestamp_firma = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # Ajustados los rut para el xml
        if('k' in folio.rut):
            folio.rut = folio.rut.replace('k','K')
        if('k' in compania.rut):
            compania.rut = compania.rut.replace('k','K')

        # LLena la plantilla dte_base.xml con los datos correspondientes

        if not isinstance(etiqueta_Documento, str):
            list_rest = [dte.tipo_dte for dte in etiqueta_Documento]        
            if len(list(set(list_rest))) == 1 and list(set(list_rest))[0] == 39:
                set_dte_sin_aplanar = render_to_string(
                    'snippets/set_DTE_tag_boletas.xml', {
                        'compania':compania,
                        'folio':folio,
                        'timestamp_firma':timestamp_firma,
                        'nro_dte': nro_dte,
                        'documento': etiqueta_Documento
                    }
                )
        else:
            set_dte_sin_aplanar = render_to_string(
                'snippets/dte_base.xml', {
                    'compania':compania,
                    'folio':folio,
                    'timestamp_firma':timestamp_firma,
                    'nro_dte': nro_dte,
                    'documento': etiqueta_Documento
                }
            )

        return set_dte_sin_aplanar

    def generar_documento_final(compania, etiqueta_SetDte, pass_certificado, instance):

        """
        Incorpora todo el documento firmado al la presentacion final y elimina 
        las tabulaciones.

        """
        # Incorpora todo el documento firmado al la presentacion final y elimina 
        # las tabulaciones.
        if instance.tipo_dte == 39:
            documento_final = render_to_string('snippets/boleta.xml', {'set_DTE':etiqueta_SetDte})
        else:
            documento_final = render_to_string('snippets/dte.xml', {'set_DTE':etiqueta_SetDte})

        # Se firmó el archivo xml
        sii_sdk = SII_SDK(settings.SII_PRODUCTION)
        set_dte_sin_aplanar = sii_sdk.multipleSign(compania,documento_final,pass_certificado,1)

        return '<?xml version="1.0" encoding="ISO-8859-1"?>\n'+set_dte_sin_aplanar
