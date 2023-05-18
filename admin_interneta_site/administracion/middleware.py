from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from urllib.parse import urlparse


def is_user_loged_in(get_response):

    def middleware(request):
        ruta = urlparse(request.build_absolute_uri()).path
        # Código que se ejecutará antes del llamado a la vista.
        response = get_response(request)
        #response["Access-Control-Allow-Origin"] = "*"
        if not request.user.is_authenticated:
            if ruta == '/administracion/iniciarsesion/':
                return response
            if ruta.startswith('/api') or ruta == '/admin/':
                print('ruta valida en middleware',response)
                return response
            else: 
                return redirect(reverse('login'))
        # Código que se ejecutará después del llamado a la vista.
        return response

    return middleware