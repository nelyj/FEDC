from django import template

from utils.constantes import documentos_dict

register = template.Library()

@register.filter(name='tipo_dte')
def convertTypeDte(value):
    """!
    Funcion para convertir los valores del tipo de documento

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 22-10-2019
    @version 1.0.0
    """
    return documentos_dict.get(value, "Este tipo de documento no existe: {}".format(value))
