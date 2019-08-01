"""!
Controlador para el manejo de tareas de modulo boletas

@author Rodrigo A. Boet (rudmanmrrod at gmail.com)
@date 01-08-2019
@version 1.0.0
"""

from django.core.serializers import serialize, deserialize

from celery.decorators import task
from celery.utils.log import get_task_logger

from utils.utils import sendToSii

from .models import Boleta, BoletaSended

logger = get_task_logger(__name__)


@task(name="envio_masivo_boletas")
def massshippingBoletas(object_states, send_sii):

    object_states = deserialize('json', object_states)
    print(object_states)
    track_id = send_sii['track_id']
    BoletaSended.objects.create(**{'track_id':track_id})
    for boleta in object_states:
        print(boleta)
        boleta.status = 'ENVIADA'
        boleta.track_id = track_id
        boleta.save()
    #messages.success(self.request, "Boleta enviada exitosamente")
    return True