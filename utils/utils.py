from boletas.models import Boleta
from facturas.models import Factura
from guia_despacho.models import guiaDespacho
from nota_credito.models import notaCredito
from nota_debito.models import notaDebito


def validarModelPorDoc(tipo_doc):
    """
    Funcion para validar y asignar un modelo a el documento

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 09-04-2019
    @param tipo_doc variable que define el tipo de documento
    @return objeto con del modelo asignado para el documento
    """
    if tipo_doc == 'FACT_ELEC':
        modelo = Factura
        url = 'facturas:'
    elif tipo_doc == 'GUIA_DES_ELEC':
        modelo = guiaDespacho
        url = 'guia_despacho:'
    elif tipo_doc == 'NOTA_DEB_ELEC':
        modelo = notaDebito
        url = 'nota_debito:'
    elif tipo_doc == 'NOTA_CRE_ELEC':
        modelo = notaCredito
        url = 'nota_credito:'
    elif tipo_doc == 'BOLE_ELEC':
        modelo = Boleta
        url = 'boletas:'
    return modelo, url


def nombreTimbrePorDoc(tipo_doc):
    """
    Funcion para obtener nombre para el timbre

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 25-09-2019
    @param tipo_doc variable que define el tipo de documento
    @return nombre del objeto
    """
    if tipo_doc == 'FACT_ELEC':
        timbre = 'facturas'
    elif tipo_doc == 'GUIA_DES_ELEC':
        timbre = 'guia'
    elif tipo_doc == 'NOTA_DEB_ELEC':
        timbre = 'notas_de_debito'
    elif tipo_doc == 'NOTA_CRE_ELEC':
        timbre = 'notas_de_credito'
    elif tipo_doc == 'BOLE_ELEC':
        timbre = 'boletas'
    return timbre

def validate_number_range(value):
    """
    Funcion para validar el número de rangos

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 16-10-2019
    @param value Recibe el valor a validar
    """
    if value is not None:
        try:
            valor = float(value)
            if not (valor >= 0 and valor <= 99):
                raise ValidationError(
                    '%(value)s el valor no se encuentra en el rango de 0 - 99',
                    params={'value': value},
                )
        except ValueError:
            raise ValidationError(
                '%(value)s no es un numero valido',
                params={'value': value},
            )

def validate_string_number(value):
    """
    Funcion para validar el string de dte

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 18-10-2019
    @param value Recibe el valor a validar
    """
    if value is not None:
        if not re.match("^([a-zA-Z])([a-zA-Z0-9_])*$", value):
            raise ValidationError(
                    '%(value)s el valor debe iniciar con una letra y no debe contener caracteres especiales ni espacios',
                    params={'value': value},
                )
    else:
        raise ValidationError(
                    '%(value)s el valor es requerido',
                    params={'value': value},
                )