"""!
Controlador para el manejo de tareas de modulo boletas

@author Rodrigo A. Boet (rudmanmrrod at gmail.com)
@date 01-08-2019
@version 1.0.0
"""

from django.core.serializers import deserialize
from celery.decorators import task
from celery.utils.log import get_task_logger

from conectores.models import *

from folios.models import Folio

from utils.utils import sendToSii

from .models import Boleta, BoletaSended

logger = get_task_logger(__name__)


@task(name="envio_masivo_boletas")
def massshippingBoletas(compania_id):

    compania = Compania.objects.get(pk=compania_id)
    pass_certificado = compania.pass_certificado
    object_states = Boleta.objects.filter(compania_id=compania_id).exclude(status='ENVIADA')
    
    folio = Folio.objects.filter(empresa=compania_id,is_active=True,vencido=False,tipo_de_documento=39).order_by('fecha_de_autorizacion').first()

    documento_final_firmado = Boleta.firmar_etiqueta_set_dte(compania, folio, object_states)
    caratula_firmada = Boleta.generar_documento_final(compania,documento_final_firmado,pass_certificado)
    send_sii = sendToSii(compania,caratula_firmada,pass_certificado)


    if(not send_sii['estado']):
        logger.warning(send_sii['msg'])
        return False
    else:
        track_id = send_sii['track_id']
        BoletaSended.objects.create(**{'track_id':track_id})
        for boleta in object_states:
            boleta.status = 'ENVIADA'
            boleta.track_id = track_id
            boleta.save()
        return True