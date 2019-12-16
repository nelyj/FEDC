from django import template

register = template.Library()


@register.filter(name='format_mil')
def formatSeparadorMiles(value, separador = '.'):
    """!
    Funcion para convertir los valores numericos en separadores de miles con "." por defecto

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 15-10-2019
    @version 1.0.0
    """
    if value == '':
        return 0
    cadena = float(value)
    if separador == '.':
        lista_decimal = "{0:,}".format(cadena).replace(',','.').split('.')[-1:]
        lista_num = "{0:,}".format(cadena).replace(',','.').split('.')[:-1]
        return '.'.join(lista_num)+","+ lista_decimal[0]
    elif separador == ',':
        return "{0:,}".format(cadena)
    else:
        lista_decimal = "{0:,}".format(cadena).replace(',',separador).split('.')[-1:]
        lista_num = "{0:,}".format(cadena).replace(',', separador).split('.')[:-1]
        return '.'.join(lista_num)+","+ lista_decimal[0]
