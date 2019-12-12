import json

from requests import Session


class SdkConectorERP:
    """
    Clase que maneja la conexion con el erp contiene pequeñas herramientas para gestionar la conexion

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 19-11-2019
    @version 1.0.0
    """
    api_login = '/api/method/login'
    api_invoice_limit = '/api/resource/Sales%20Invoice/?limit_page_length'
    api_list_invoice = '/api/resource/Sales%20Invoice/'
    api_list_delivery= '/api/resource/Delivery%20Note/'

    def __init__(self, url, user, password):
        """
        """
        self.url = url
        self.user = user
        self.password = password

    def login(self):
        """
        Metodo para logear y crear la sesion del usuario

        @param self atributos de la clase
        @return response y session
        """
        url = self.url + self.api_login
        session = Session()
        payload = {"usr": self.user, "pwd": self.password}
        headers = {'content-type': "application/json"}

        response = session.get(url, data=json.dumps(payload), headers=headers, verify=False)

        return response, session

    def list_limit(self, session):
        """
        Metodo para listar las facturas con un limite

        @param self atributos de la clase
        @param session objeto de sesion del usuario
        @return response respuesta del servidor
        """
        url = self.url + self.api_invoice_limit
        response = session.get(url,  verify=False)

        return response

    def list(self, session, slug=None):
        """
        Metodo para listar todas las facturas del erp

        @param self atributos de la clase
        @param session objeto de sesion del usuario
        @return response respuesta del servidor
        """
        url = self.url + self.api_list_invoice + slug if slug else self.url + self.api_list_invoice
        response = session.get(url, verify=False)

        return response

    def list_delivery(self, session, slug=None):
        """
        Metodo para listar las guias de despacho con un limite o con un detalle

        @param self atributos de la clase
        @param session objeto de sesion del usuario
        @return response respuesta del servidor
        """
        url = self.url + self.api_list_delivery + slug if slug else self.url + self.api_list_delivery + '?limit_page_length'
        response = session.get(url, verify=False)

        return response
