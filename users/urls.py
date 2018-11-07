# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib.auth.views import (
    password_reset, password_reset_done,
    )

from .forms import PasswordResetForm
from .ajaxs import *
from .views import *

app_name = 'users'
urlpatterns = [
    url(r'^$', LoginView.as_view(), name="login"),
    url(r'^logout/$', LogOutView.as_view(), name="logout"),

     # Reset password all users
    url(r'^accounts/password/reset/$', password_reset,
        {'post_reset_redirect': '/accounts/password/done/',
         'template_name': 'users_forgot.html',
         'password_reset_form': PasswordResetForm},
        name="forgot"),
    url(r'^accounts/password/done/$', password_reset_done,
        {'template_name': 'users_pass_reset_done.html'},
        name='reset_done'),

    # Urls Access Super Admin
    url(r'^lista-usuarios/$', ListUsersView.as_view(), name="lista_users"),
    url(r'^perfil/(?P<pk>\d+)/$', ModalsPerfil.as_view(),
        name="modal_perfil"),
    url(r'^registrar/$', RegisterView.as_view(), name="registrar"),

    # Ajax list Users, for Super Admin
    url(r'^listar-usuarios/$', ListUsersAjaxView.as_view(),
        name="listar_users"),
]