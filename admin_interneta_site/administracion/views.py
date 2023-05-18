from ast import Delete
from distutils.command.upload import upload
from mimetypes import init
import datetime
from multiprocessing.dummy import active_children
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views
from django.contrib.auth import authenticate, login, logout
from django.views.generic import ListView
from .models import Categorias, Video, CreditosVideo
from .forms import CategoriasForm, CreditosVideoForm, LoginForm, VideosForm
from django import forms
from django.core.files.storage import FileSystemStorage
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from .utilerias import UploaderDefault
import re
import logging
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .tasks import upload_to_bucket_task,upload_to_bucket_task_save
from urllib.parse import unquote
logger = logging.getLogger(__name__)
def add_categoria(request, num=0):
    dict({'error':'redirect-login', 'success':False})
    if not request.user.is_authenticated:
        return JsonResponse(respuesta_request)
    else:
        try:
            num = int(request.POST["num"])
            if num!=0:
                video = Categorias.objects.get(id=num)
        except:
            if (request.method=='POST'):
                respuesta_request = {'error':'campo-id', 'success':False}
                return JsonResponse(respuesta_request)
    if(num != 0 and request.method=='GET'):
        cat = Categorias.objects.get(id=num)
        form = CategoriasForm(instance=cat)
    else:
        if(num == 0 and request.method=='GET'):
            form = CategoriasForm(initial={'titulo':'', 'descripcion':'','no_videos':0})
    if(request.method=='POST'):
        if(num != 0):
            cat = Categorias.objects.get(id=num)
            form = CategoriasForm(request.POST, request.FILES, instance = cat)
        else:
             form = CategoriasForm(request.POST, request.FILES)  
        if form.is_valid():
            respuesta_request = {'error':'', 'success':True}
            upload = request.FILES['img_file']
            fss = FileSystemStorage()
            cleaned_file_name = re.sub(r'[ÁáéíóúÄëïöü\s]','_',upload.name)
            file = fss.save(cleaned_file_name, upload)
            file_url = fss.url(file)
            try:
                file_path = settings.MEDIA_ROOT+file_url.replace('media','')
                #print('la ruta del archivo es ',file_path)
                uploader = UploaderDefault()
                presigned_url = uploader.generate_url(settings.AWS_STORAGE_BUCKET_NAME,cleaned_file_name)
                presigned_url = presigned_url[0 : presigned_url.index('?')]
                print('la ruta en la web del archivo de imagen es ',presigned_url)
                instance=form.save(commit=False)
                instance.contenedor_img = presigned_url
                respuesta = uploader.upload(bucket=settings.AWS_STORAGE_BUCKET_NAME, key=cleaned_file_name,file=file_path)            
                #respuesta = upload_to_bucket_task.delay(bucket=settings.AWS_STORAGE_BUCKET_NAME, key=cleaned_file_name,file=file_path, cleaned_file=cleaned_file_name)
            except ClientError as e:
                print('error subiendo al bucket',e)
                respuesta_request = {'error':'error-file', 'success':False}
            instance.save()
            fss.delete(cleaned_file_name)   
            return JsonResponse(respuesta_request)
            #return redirect(reverse('list-categorias'))
        else:
            respuesta_request = {'error':'formulario-invalido', 'formerrors':form.errors, 'success':False}
            return JsonResponse(respuesta_request)
            # return render(request, 'administracion/add_categoria.html', {'form':form})     
    return render(request,'administracion/add_categoria.html',{'form':form})

def delete_categoria(request, num=0):
    if(request.method == 'POST'):
        if(num!= 0):
            try:
                categoria = Categorias.objects.get(id=num)
                categoria.activo = not categoria.activo
                categoria.save()
            except Categorias.DoesNotExist:
                print('error consultando video')
        else:
            categoria = Categorias.objects.first()
    else: 
        if(num!= 0):
            try:
                categoria = Categorias.objects.get(id=num)
            except Categorias.DoesNotExist:
                print('error consultando video')
        else:
            categoria = Categorias.objects.first()
    context = {
        'categoria_actual':categoria
    }
    return render(request, 'administracion/delete_categoria.html',context, {'num':num})


def update_video(request):
    respuesta_request = dict({'error':'redirect-login', 'success':False})
    if not request.user.is_authenticated:
        #return redirect('login')
        return JsonResponse(respuesta_request)
    else:
        try:
            num = int(request.POST["num"])
            if num!=0:
                video = Video.objects.get(id=num)
        except:
            respuesta_request = {'error':'campo-id', 'success':False}
            return JsonResponse(respuesta_request)
        if(request.method=='POST'):
            form = VideosForm(request.POST, request.FILES)
            if(num!=0):
                form = VideosForm(request.POST,request.FILES, instance=video)
            form.fields['id_categoria'].queryset=Categorias.objects.all()                
            if form.is_valid():
                respuesta_request = {'error':'', 'success':True}
                upload = request.FILES['aws_file']
                upload_img = request.FILES['img_file']
                # fss = FileSystemStorage()
                cleaned_file_name = re.sub(r'[ÁáéíóúÄëïöü\s]','_',upload.name)
                cleaned_file_img_name = re.sub(r'[ÁáéíóúÄëïöü\s]','_',upload_img.name)
                # file = fss.save(cleaned_file_name, upload)
                # file_img = fss.save(cleaned_file_img_name, upload_img)
                # file_url = fss.url(file)
                # file_img_url = fss.url(file_img)
                file_url = unquote(request.POST["file_url"])
                file_img_url = unquote(request.POST["file_img_url"])
                #print('el nombre del archivo es ',file_url,upload.name)
                try:
                    file_path = settings.MEDIA_ROOT+file_url.replace('media','')
                    file_img_path = settings.MEDIA_ROOT+file_img_url.replace('media','')
                    #print('la ruta del archivo es ',file_path)
                    uploader = UploaderDefault()
                    presigned_url = uploader.generate_url(settings.AWS_STORAGE_BUCKET_NAME,cleaned_file_name)
                    presigned_url = presigned_url[0 : presigned_url.index('?')]
                    presigned_img_url = uploader.generate_url(settings.AWS_STORAGE_BUCKET_NAME,cleaned_file_img_name)
                    presigned_img_url = presigned_img_url[0 : presigned_img_url.index('?')]
                    print('la ruta en la web del archivo es ',presigned_url)
                    print('la ruta en la web del archivo de imagen es ',presigned_img_url)

                    instance=form.save(commit=False)   
                    instance.contenedor_img = presigned_img_url
                    instance.save()                
                    respuesta = upload_to_bucket_task_save.delay(bucket=settings.AWS_STORAGE_BUCKET_NAME, key=cleaned_file_name,file=file_path,cleaned_file=cleaned_file_name, id_modelo=num,url_prefirmado=presigned_url)
                    respuestaimg = upload_to_bucket_task.delay(bucket=settings.AWS_STORAGE_BUCKET_NAME, key=cleaned_file_img_name,file=file_img_path,cleaned_file=cleaned_file_img_name)
                    # uploader = UploaderDefault()
                    # fss = FileSystemStorage()
                    # #logger.warning('invocación de tarea asíncrona upload_to_bucket_task')
                    # respuesta = uploader.upload(bucket=settings.AWS_STORAGE_BUCKET_NAME, key=cleaned_file_name,file=file_path)
                    # respuestaimg = uploader.upload(bucket=settings.AWS_STORAGE_BUCKET_NAME, key=cleaned_file_img_name,file=file_img_path)
                    # fss.delete(cleaned_file_name)
                    # fss.delete(cleaned_file_img_name)
                    # instance.contenedor_aws = presigned_url
                    # instance.save()
                    logger.warning('fin de guardado del video: '+instance.titulo+' en aws')
                except ClientError as e:
                    print('error subiendo al bucket',e)
                    respuesta_request = {'error':'error-file', 'success':False}
                # instance.save()
                #return redirect(reverse('list-videos'))
                return JsonResponse(respuesta_request)
            else:
                print('errores en el formulario update_video',form.errors)
                respuesta_request = {'error':'formulario-invalido', 'formerrors':form.errors, 'success':False}
                #return redirect(reverse('list-videos'))
                return JsonResponse(respuesta_request)
        else:
            return redirect(reverse('list-videos'))

def update_file_video(request):
    respuesta_request = dict({'error':'redirect-login', 'success':False})
    if not request.user.is_authenticated:
        return JsonResponse(respuesta_request)
    else:
        try:
            num = int(request.POST["num"])
            if num!=0:
                video = Video.objects.get(id=num)
        except:
            respuesta_request = {'error':'campo-id', 'success':False}
            return JsonResponse(respuesta_request)
        if(request.method=='POST'):
            form = VideosForm(request.POST, request.FILES)
            if(num!=0):
                form = VideosForm(request.POST,request.FILES, instance=video)
            form.fields['id_categoria'].queryset=Categorias.objects.all()                
            if form.is_valid():
                respuesta_request = {'error':'', 'success':True}
                instance=form.save(commit=True)
                instance.contenedor_aws = 'Ninguno'
                instance.save()
                upload = request.FILES['aws_file']
                upload_img = request.FILES['img_file']
                fss = FileSystemStorage()
                cleaned_file_name = re.sub(r'[ÁáéíóúÄëïöü\s]','_',upload.name)
                cleaned_file_img_name = re.sub(r'[ÁáéíóúÄëïöü\s]','_',upload_img.name)
                file = fss.save(cleaned_file_name, upload)
                file_img = fss.save(cleaned_file_img_name, upload_img)
                file_url = fss.url(file)
                file_img_url = fss.url(file_img)
                numero=instance.id
                respuesta_request = {'error':'','files_urls':[file_url,file_img_url],'numero':numero,'success':True}
                return JsonResponse(respuesta_request)
            else:
                print('errores en el formulario update_file_video',form.errors)
                respuesta_request = {'error':'formulario-invalido', 'formerrors':form.errors, 'success':False}
                return JsonResponse(respuesta_request)
        else:
            respuesta_request={'error':'list-videos',success:False}
            return JsonResponse(respuesta_request)

def add_video(request,num=0):    
    if num!=0:
        try:
            video = Video.objects.get(id=num)
            form = VideosForm(instance=video)
        except Video.DoesNotExist:
            form = VideosForm(initial={'titulo':''})
    else:
        form = VideosForm(initial={'titulo':''})
        form.fields['id_categoria'].queryset=Categorias.objects.all()
    
    return render(request,'administracion/add_video.html',{'form':form})


def delete_video(request, num=0):
    if(request.method == 'POST'):
        if(num!= 0):
            try:
                video = Video.objects.get(id=num)
                video.activo = not video.activo
                video.save()
            except Video.DoesNotExist:
                print('error consultando video')
        else:
            video = Video.objects.first()
    else: 
        if(num!= 0):
            try:
                video = Video.objects.get(id=num)
            except Video.DoesNotExist:
                print('error consultando video')
        else:
            video = Video.objects.first()
    context = {
        'video_actual':video
    }
    return render(request, 'administracion/delete_video.html',context, {'num':num})


def add_creditos_video(request,num=0, method=0):
    if not request.user.is_authenticated:
        return redirect('login')
    anio = currentDate = datetime.date.today().year
    if(num!= 0):
        try:
            creditos = CreditosVideo.objects.get(id_video=num)
            form = CreditosVideoForm(instance=creditos)
        except CreditosVideo.DoesNotExist:
            form = CreditosVideoForm(initial={'codigo_identificacion':'','anio_produccion':anio,
        'sinopsis':'','direccion_realizacion':'','asistentes_realizacion':'','guion':'','camara':'',
        'foto_fija':'','color':True,'duracion_mins':30,'reparto':'','testimonios':'','idioma':'',
        'musica':'','edicion':'','produccion_ejecutiva':''})
    else:
        form = CreditosVideoForm(initial={'codigo_identificacion':'','anio_produccion':anio,
        'sinopsis':'','direccion_realizacion':'','asistentes_realizacion':'','guion':'','camara':'',
        'foto_fija':'','color':True,'duracion_mins':30,'reparto':'','testimonios':'','idioma':'',
        'musica':'','edicion':'','produccion_ejecutiva':''})
    return render(request,'administracion/add_creditos_video.html',{'form':form})

def update_creditos_video(request):
    if(request.method=='POST'):
        form = CreditosVideoForm(request.POST)
        num = int(request.POST["num"])
        # print('entre a formulario con valor de id ',num)
        if(num!= 0):
            # print('consultando creditos')
            try:
                creditos = CreditosVideo.objects.get(id_video=num)
                form = CreditosVideoForm(request.POST,instance=creditos)
            except CreditosVideo.DoesNotExist:
                # print('excepción consultando creditos')
                form = CreditosVideoForm(request.POST)

        if form.is_valid():
            form.non_field_errors = forms.ValidationError('Su cuenta está desactivada')
            print('formulario validado')
            if(num!=0):
                form.save(commit=False)
                form.instance.id_video = Video.objects.get(id=num)
                form.save(commit=True)
                return redirect(reverse('list-videos'))
            else:
                form.save()
                return redirect(reverse('list-videos'))
        else:
            return render(request,'administracion/add_creditos_video.html',{'form':form})
    return redirect(reverse('list-videos')) #redirect(reverse('new-video',{'num':num}))

def nuevo_video(request,num=0):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        return render(request, 'administracion/new_video.html',{'num':num})

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        return render(request,'dashboard.html')

def user_login(request):
    if(request.method == 'POST'):
        form = LoginForm(request.POST, initial={'username':'', 'password':''})
        if(form.is_valid()):
            cd = form.cleaned_data
            user = authenticate(request,
            username=cd['username'],
            password=cd['password'])
            if user is not None:
                if user.is_active and user.is_staff:
                    login(request,user)
                    return render(request,'dashboard.html')
                else:
                    form.non_field_errors = forms.ValidationError('Su cuenta está desactivada')
                    return render(request, 'administracion/iniciar_sesion.html', {'form':form})
            else:
                form.non_field_errors =  forms.ValidationError('Nombre de usuario o contraseña inválida')
                return render(request, 'administracion/iniciar_sesion.html', {'form':form})
        else:
            form.non_field_errors = forms.ValidationError('Por favor llene correctamente todos los campos')
            return render(request, 'administracion/iniciar_sesion.html', {'form':form})
    else:
        form = LoginForm(initial={'username':'', 'password':''})
    return render(request, 'administracion/iniciar_sesion.html', {'form':form})

def site_logout(request):
    logout(request)
    return redirect('/')


# Create your views here.
class CategoriasView(ListView):
    model=Categorias
    paginate_by=5
    template_name= 'administracion/listado_categorias.html'

class VideosView(ListView):
    model=Video
    paginate_by=5
    queryset=Video.objects.all().select_related('id_categoria').prefetch_related('creditos_por_video')
    template_name = 'administracion/listado_videos.html'
    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        query = self.request.GET.get('q')
        entero = ''
        if query:
            try:
                entero = int(query)
                pass
            except:
                pass
            if isinstance(entero,int):
                print('el entero es ',entero)
                return qs.filter(Q(creditos_por_video__anio_produccion=entero))
            else:
                return qs.filter(Q(titulo=query) | Q(creditos_por_video__codigo_identificacion=query) |
                Q(creditos_por_video__direccion_realizacion = query) | 
                Q(id_categoria__titulo=query) | Q(id_categoria__titulo=query))
        return qs
        

