# -*- coding: utf-8 -*-
"""!
Vista que construye los controladores para las utilidades de la plataforma

@author Ing. Leonel P. Hernandez M. (leonelphm at gmail.com)
@copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
@date 09-06-2017
@version 1.0.0
"""
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render
from braces.views import GroupRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.contrib.auth.mixins import (
    PermissionRequiredMixin, LoginRequiredMixin
)
from django.shortcuts import (
    redirect
)

from .models import *
from .messages import MENSAJES_LOGIN


class LoginRequeridoPerAuth(LoginRequiredMixin, GroupRequiredMixin):
    """!
    Clase que construye el controlador para el login requerido, se sobreescribe el metodo dispatch

    @author Ing. Leonel Paolo Hernandez Macchiarulo  (leonelphm at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-06-2017
    @version 1.0.0
    """

    def dispatch(self, request, *args, **kwargs):
        """
        Envia una alerta al usuario que intenta acceder sin permisos para esta clase
        @return: Direcciona al login en caso de no poseer permisos, en caso contrario accede a la clase
        """
        if not request.user.is_authenticated:
            messages.warning(self.request, MENSAJES_LOGIN['LOGIN_REQUERIDO'])
            return self.handle_no_permission()
        valid_group = False
        grupos = request.user.groups.all()
        grupo = []
        if len(grupos) > 1:
            for g in grupos:
                grupo += str(g),
                if (str(g) in self.get_group_required()):
                    valid_group = True
        else:
            try:
                grupo = str(request.user.groups.get())
            except:
                return redirect('users:403error')
            if (grupo in self.get_group_required()):
                valid_group = True
        if not (valid_group):
            return redirect('users:403error')
        return super().dispatch(request, *args, **kwargs)


class StartView(LoginRequeridoPerAuth, TemplateView):
    """!
    Muestra el inicio de la plataforma

    @author Ing. Leonel Paolo Hernandez Macchiarulo  (leonelphm at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-01-2017
    @version 1.0.0
    @return: El template inicial de la plataforma
    """
    template_name = "utils_start.html"
    group_required = [u"Super Admin", u"Admin", u"Invitado"]


def obtenerEstados():
    """
    Función que permite obtener la lista de estados

    El método hace una lista consultando el modelo Estado

    @return: Lista de estados
    """
    try:
        if Estado.DoesNotExist:
            consulta = Estado.objects.all().values('id', 'nombre')
        else:
            consulta = [{'id': '', 'nombre': ''}]
    except:
        consulta = [{'id': '', 'nombre': ''}]

    return consulta

def obtenerMunicipios(request):
    """
    Función que permite obtener la lista de municipios asociados a un estado

    El método hace un llamado al modelo para realizar una consulta

    @param id_estado: Identificador del estado
    @type id_estado: entero

    @return: Lista de municipios asociados al estado
    """
    try:
        if Municipio.DoesNotExist:
            id_estado = request.GET.get('id_estado')
            municipios = Municipio.objects.filter(estado_id=id_estado).values('id', 'nombre')
            data = json.dumps(list(municipios), cls=DjangoJSONEncoder)
            print(data)
        else:
            data = {}
    except:
        data = {}
        pass

    return HttpResponse(data, content_type='application/json')


def obtenerParroquias(request):
    """
    Función que permite obtener la lista de municipios asociados a un estado

    El método hace un llamado al modelo para realizar una consulta

    @param id_estado: Identificador del estado
    @type id_estado: entero

    @return: Lista de municipios asociados al estado
    """
    try:
        if Municipio.DoesNotExist:
            id_municipio = request.GET.get('id_municipio')
            municipios = Parroquia.objects.filter(municipio_id=id_municipio).values('id', 'nombre')
            data = json.dumps(list(municipios), cls=DjangoJSONEncoder)
        else:
            data = {}
    except:
        data = {}
        pass

    return HttpResponse(data, content_type='application/json')


def listMunicipios():
    """
    Función que permite obtener el municipio asociado a una parroquia

    El método hace un llamado a un servicio REST de la aplicación comun

    @param id_parroquia: Identificador de la parroquia
    @type id_parroquia: entero

    @return: El municipio asociado a la parroquia
    """
    try:
        if Municipio.DoesNotExist:
            consulta = Municipio.objects.all().values('id', 'nombre')
        else:
            consulta = [{'id': '', 'nombre': ''}]
    except OperationalError:
        consulta = [{'id': '', 'nombre': ''}]

    return consulta