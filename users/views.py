"""!
Vista que controla los procesos de los usuarios

@author Ing. Leonel P. Hernandez M. (leonelphm at gmail.com)
@copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
@date 09-01-2017
@version 1.0.0
"""
from django.core import serializers
from django import forms
from django.db.models import Q
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate, logout, login
)

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.models import (
    Group, Permission, User
)
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.mixins import (
    LoginRequiredMixin
)
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.urls import (
    reverse_lazy, reverse
)

from django.shortcuts import (
    render, redirect, get_object_or_404
)
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.views.generic.edit import (
    FormView, UpdateView
)
from multi_form_view import MultiModelFormView

from .models import UserProfile
from .forms import (
    FormularioLogin, FormularioAdminRegistro, FormularioUpdate,
    FormularioAdminRegPerfil, FormularioRegistroComun
)

from utils.views import (
    LoginRequeridoPerAuth
)
from utils.messages import MENSAJES_LOGIN, MENSAJES_START

class LoginView(FormView):
    """!
    Muestra el formulario de ingreso a la aplicación 

    @author Ing. Leonel P. Hernandez M. (leonelphm at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-01-2017
    @version 1.0.0
    """
    form_class = FormularioLogin
    template_name = 'users_login.html'
    success_url = '/inicio/'
    model = UserProfile

    def form_valid(self, form):
        """
        Valida el formulario de logeo
        @return: Dirige a la pantalla inicial de la plataforma
        """
        usuario = form.cleaned_data['usuario']
        contrasena = form.cleaned_data['contrasena']
        if '@' in usuario:
            try:
                usuario = User.objects.get(email=usuario).username
            except:
                messages.error(self.request, MENSAJES_LOGIN['CORREO_INVALIDO'] % (usuario))
        usuario = authenticate(username=usuario, password=contrasena)
        if usuario is not None:
            login(self.request, usuario)
            self.request.session['permisos'] = list(usuario.get_all_permissions())
            try:
                grupos = usuario.groups.all()
                grupo = []
                if len(grupos) > 1:
                    for g in grupos:
                        grupo += str(g),
                else:
                    grupo = str(usuario.groups.get())
            except:
                grupo = "No pertenece a un grupo"

            self.request.session['grupos'] = grupo

            if self.request.POST.get('remember_me') is not None:
                # Session expira a los dos meses si no se deslogea
                self.request.session.set_expiry(1209600)
            messages.info(self.request, MENSAJES_START['INICIO_SESION'] % (usuario.first_name, usuario.username))
        else:
            user = User.objects.filter(username=form.cleaned_data['usuario'])
            if user:
                user = user.get()
                if not user.is_active:
                    self.success_url = reverse_lazy('users:login')
                    messages.error(self.request, MENSAJES_LOGIN['CUENTA_INACTIVA'])
            else:
                self.success_url = reverse_lazy('users:login')
                messages.warning(self.request, MENSAJES_LOGIN['LOGIN_USUARIO_NO_VALIDO'])

        return super(LoginView, self).form_valid(form)


class LogOutView(RedirectView):
    """!
    Salir de la apliacion

    @author Ing. Leonel P. Hernandez M. (leonelphm at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-01-2017
    @version 1.0.0
    """
    permanent = False
    query_string = True

    def get_redirect_url(self):
        """!
        Dirige a la pantalla del login
        @return: A la url del login
        """
        logout(self.request)
        return reverse_lazy('users:login')


class ListUsersView(LoginRequeridoPerAuth, TemplateView):
    """!
    Listar usuarios de la apliacion

    @author Ing. Leonel P. Hernandez M. (leonelphm at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-01-2017
    @version 1.0.0
    """
    template_name = "users_list.html"
    model = User
    success_url = reverse_lazy('users:lista_users')
    group_required = [u"Super Admin"]

    def __init__(self):
        super(ListUsersView, self).__init__()


    def post(self, *args, **kwargs):
        '''
        Cambia el estado activo a el usuario
        @return: Dirige a la tabla que muestra los usuarios de la apliacion
        '''
        accion = self.request.POST
        activar = accion.get('activar', None)
        inactivar = accion.get('inactivar', None)
        estado = False

        if activar is not None:
            user = activar
            estado = True
        elif inactivar is not None:
            user = inactivar
            estado = False
        else:
            messages.error(self.request, "Esta intentando hacer una accion incorrecta")      
        try:
            user_act = self.model.objects.get(pk=user)
            user_act.is_active = estado
            user_act.save()
            if estado:
                messages.success(self.request, "Se ha activado el usuario: %s" % (str(user_act)))
            else:
                messages.warning(self.request, "Se ha inactivado el usuario: %s" % (str(user_act)))
        except:
            messages.info(self.request, "El usuario no existe")
        return redirect(self.success_url)


class StartView(LoginRequiredMixin, TemplateView):
    """!
    Muestra el inicio de la plataforma

    @author Ing. Leonel P. Hernandez M. (leonelphm at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-01-2017
    @version 1.0.0
    @return: El template inicial de la plataforma
    """
    template_name = "home.html"

    def dispatch(self, request, *args, **kwargs):
        """
        Envia una alerta al usuario que intenta acceder sin estar logeado
        @return: Direcciona al login en caso de no poseer permisos, en caso contrario usa la clase
        """
        if not request.user.is_authenticated:
            messages.warning(self.request, "Debes iniciar Sessón")
            return self.handle_no_permission()
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        """Use this to add extra context."""
        try:
            perfil = UserProfile.objects.select_related().get(fk_user=self.request.user.id)
        except:
            perfil = None
        context = super(StartView, self).get_context_data(**kwargs)
        context['userprofile'] = perfil
        return context


class RegisterView(LoginRequeridoPerAuth, MultiModelFormView):
    """!
    Muestra el formulario de registro de usuarios

    @author Ing. Leonel P. Hernandez M. (leonelphm at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-01-2017
    @version 1.0.0
    """
    template_name = "users_register.html"
    form_classes = {
      'user': FormularioAdminRegistro,
      'user_perfil': FormularioAdminRegPerfil,
    }
    success_url = reverse_lazy('utils:inicio')
    model = Group
    model_permi = Permission
    group_required = [u"Super Admin"]
    record_id=None

    def get_context_data(self, **kwargs):
        """
        Carga el formulario en la vista,para registrar usuarios
        @return: El contexto con los objectos para la vista
        """
        return super(RegisterView, self).get_context_data(**kwargs)

    def forms_valid(self, forms, **kwargs):
        """
        Valida el formulario de registro del perfil de usuario
        @return: Dirige con un mensaje de exito a el home
        """
        nuevo_usuario = forms['user'].save()
        nuevo_perfil = forms['user_perfil'].save(commit=False)
        nuevo_perfil.fk_user = nuevo_usuario
        nuevo_perfil.save()
        usuario = forms['user'].cleaned_data['username']
        grupos = forms['user'].cleaned_data['groups']
        for group in grupos:
            # Agrega a el usuario al(los) grupo(s) seleccionado(s)
            nuevo_usuario.groups.add(group.pk)
        model_user = ContentType.objects.get_for_model(User).pk
        LogEntry.objects.log_action(
            user_id=self.request.user.id,
            content_type_id=model_user,
            object_id=nuevo_usuario.id,
            object_repr=str(nuevo_usuario.username),
            action_flag=ADDITION)
        messages.success(self.request, "Usuario %s creado con exito\
                                       " % (str(usuario)))
        return super(RegisterView, self).forms_valid(forms)

        
class ModalsPerfil(LoginRequeridoPerAuth, MultiModelFormView):
    """!
    Construye el modals para la actualizacion del usuario

    @author Ing. Leonel P. Hernandez M. (leonelphm at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-01-2017
    @version 1.0.0
    """
    model = UserProfile
    form_classes = {
      'user': FormularioUpdate,
      'user_perfil': FormularioAdminRegPerfil,
    }
    template_name = 'users_modalsProfile.html'
    success_url = reverse_lazy('users:lista_users')
    success_message = 'Usuario Actualizado con exito'
    group_required = [u"Super Admin"]
    record_id = None


    def get_context_data(self, **kwargs):
        """
        Carga el formulario en la vista,para registrar usuarios
        @return: El contexto con los objectos para la vista
        """
        context = super(ModalsPerfil, self).get_context_data(**kwargs)
        self.record_id = self.kwargs.get('pk', None)
        try:
            record = self.model.objects.select_related().get(fk_user=self.record_id)
        except UserProfile.DoesNotExist:
            record = None
        context['upUser'] = record
        return context

    def get_objects(self, **kwargs):
        """
        Carga el formulario en la vista,para actualizar el perfil del  usuario
        @return: El contexto con los objectos para la vista
        """
        self.record_id = self.kwargs.get('pk', None)
        try:
            record = self.model.objects.select_related().get(fk_user=self.record_id)
        except UserProfile.DoesNotExist:
            record = None
        return {
          'user_perfil': record,
          'user': record.fk_user if record else None}

    def get_success_url(self):
        return reverse('users:lista_users')

    def forms_valid(self, forms, **kwargs):
        """
        Valida el formulario de registro del perfil de usuario
        @return: Dirige con un mensaje de exito a el home
        """
        self.record_id = self.kwargs.get('pk', None)
        if self.record_id is not None:
            objeto = get_object_or_404(User, pk=self.record_id)
            update_usuario = FormularioUpdate(self.request.POST, instance=objeto)
            update_perfil = FormularioAdminRegPerfil(self.request.POST, instance=objeto)

            messages.success(self.request, "Usuario %s Actualizado con exito\
                                           " % (str(objeto.username)))
        return super(ModalsPerfil, self).forms_valid(forms)