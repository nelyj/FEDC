from boletas.models import Boleta
from facturas.models import Factura
from guia_despacho.models import guiaDespacho
from nota_credito.models import notaCredito
from nota_debito.models import notaDebito
from .SIISdk import SII_SDK


def validarModelPorDoc(tipo_doc):
    """
    Funcion para validar y asignar un modelo a el documento

    @author Rodrigo Boet (rudmanmrrod@gmail.com)
    @date 09-04-2019
    @param tipo_doc variable que define el tipo de documento
    @return objeto con del modelo asignado para el documento
    """
    if tipo_doc == 'FACT_ELEC':
        modelo = Factura
    elif tipo_doc == 'GUIA_DES_ELEC':
        modelo = guiaDespacho
    elif tipo_doc == 'NOTA_DEB_ELEC':
        modelo = notaDebito
    elif tipo_doc == 'NOTA_CRE_ELEC':
        modelo = notaCredito
    elif tipo_doc == 'BOLE_ELEC':
        modelo = Boleta
    return modelo

def sendToSii(compania,invoice, pass_certificado):
    """
    Método para enviar la factura al sii
    @param compania recibe el objeto compañia
    @param invoice recibe el xml de la factura
    @param pass_certificado recibe la contraseña del certificado
    @return dict con la respuesta
    """
    try:
        sii_sdk = SII_SDK(SII_PRODUCTION)
        seed = sii_sdk.getSeed()
        try:
            sign = sii_sdk.signXml(seed, compania, pass_certificado)
            token = sii_sdk.getAuthToken(sign)
            if(token):
                print(token)
                try:
                    invoice_reponse = sii_sdk.sendInvoice(token,invoice,compania.rut,'60803000-K')
                    return {'estado':invoice_reponse['success'],'msg':invoice_reponse['message'],
                    'track_id':invoice_reponse['track_id']}
                except Exception as e:
                    print(e)
                    return {'estado':False,'msg':'No se pudo enviar el documento'}    
            else:
                return {'estado':False,'msg':'No se pudo obtener el token del sii'}
        except Exception as e:
            print(e)
            return {'estado':False,'msg':'Ocurrió un error al firmar el documento'}
        return {'estado':True}
    except Exception as e:
        print(e)
        return {'estado':False,'msg':'Ocurrió un error al comunicarse con el sii'}

