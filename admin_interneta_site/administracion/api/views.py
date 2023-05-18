from cgitb import lookup
from multiprocessing.dummy import active_children
from rest_framework import generics
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import api_view
from ..models import Categorias,Video, CreditosVideo, ComentariosVideo, Video, RelatoVideo
from ..models import VerificacionRegistroUsuario, FavoritosUsuarioVideo
from ..models import VisitasVideo, EventoAcervo,FavoritosUsuarioRelato,VisitasRelato
from ..models import EventoAcervo,VisitasEvento, CalificacionVideo
from .serializers import CambiarPasswordSerializer, LoginSerializer, RegisterSerializer,VideoShortSerializer, UsuariosSerializer,CalfificacionVideoParaListado
from .serializers import CategoriasSerializer, VideoSerializer, CreditosVideoSerializer, ComentariosVideoSerializer, IndexedComentariosVideoSerializer
from .serializers import RelatoVideoSerializer
from .serializers import EventosResponseSerializer, AnswerComentariosSerializer, VideosFavoritosSerializer,VideosMarcadosFavoritosSerializer,EventosAcervoSerializer
from .serializers import RelatosFavoritosSerializer,RelatosMarcadosFavoritosSerializer,RelatosMarcadosDetalleFavoritosSerializer,RelatoVideoParaVisitasSerializer
from .serializers import CalificacionVideoSerializer
from .serializers import EventoParaVisitasSerializer
from rest_framework import permissions
from rest_framework.pagination import LimitOffsetPagination
import uuid, re, datetime, pytz, traceback, sys
from opensearchpy import OpenSearch
from django.db.models import Prefetch,Count,Sum, Avg
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from ..utilerias import UploaderDefault
from django.core.files.storage import FileSystemStorage
from rest_framework.parsers import MultiPartParser
from django.conf import settings
import datetime
import calendar
from django.utils.timezone import make_aware
from operator import itemgetter
from django.db.models import Q

host = 'opensearch-nodo'
port = 9200
auth = ('admin', 'admin')
USUARIO_GENERICO = 0
PAGINACION = 10
PAGINACION_RELATOS = 30

class StandardResultsSetPagination(LimitOffsetPagination):
    default_limit = 10
    limit_query_param  = 'limit'
    offset_query_param = 'offset'
    max_limit  = 100

class LoginView(APIView):
    permission_classes=[permissions.AllowAny]
    def post(self,request):
        serializer=LoginSerializer(data=request.data)
        try:
            if serializer.is_valid():
                user=serializer.validated_data["usuario"]
                serializer_response = UsuariosSerializer(user)
                return Response(serializer_response.data,status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        except AssertionError as err:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes=(permissions.IsAuthenticated,)
    def get(self,request):
        user = User.objects.get(id=request.user.id)
        serializer = UsuariosSerializer(user)
        return Response(serializer.data)

class RegisterUser(generics.CreateAPIView):
    permission_classes=[permissions.AllowAny]
    queryset=User.objects.all()
    serializer_class=RegisterSerializer

class SendChangePwdLink(APIView):
    permission_classes=[permissions.AllowAny]
    def post(self,request):
        try:
            if(request.data["email"]==""):
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except KeyError as err:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user=User.objects.filter(email=request.data["email"])
        if(len(user)>0):
            guid = uuid.uuid4().hex
            verificacion = VerificacionRegistroUsuario.objects.create(id_usuario=User.objects.get(email=request.data["email"]),
            link=guid,
            is_reset=True)
            verificacion.save()
            verificacion_update = VerificacionRegistroUsuario.objects.get(link=guid)
            fecha_nueva = verificacion_update.insert_time + datetime.timedelta(days=1)
            verificacion_update.vigencia_time=fecha_nueva
            verificacion_update.save()
            return Response(status = status.HTTP_201_CREATED)
        
        return Response(status = status.HTTP_400_BAD_REQUEST)

class ResetPassword(APIView):
    permission_classes=[permissions.AllowAny]
    def post(self,request):
        guid = request.data.get('guid')
        password = request.data.get('password')
        password2 = request.data.get("password2")
        if not guid or not password or not password2:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = CambiarPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        verificacion = VerificacionRegistroUsuario.objects.filter(link=guid,is_reset=True,utilizado=False)
        if(len(verificacion)==0):
            return Response({"link":"El vínculo no es válido"},status=status.HTTP_400_BAD_REQUEST)
        if verificacion[0].vigencia_time.timestamp() < datetime.datetime.now().timestamp():
            return Response({"link":"El vínculo expiró"})
        update_verificacion = VerificacionRegistroUsuario.objects.get(link=guid)
        user = update_verificacion.id_usuario
        user.set_password(password)
        user.save()
        update_verificacion.utilizado=True
        update_verificacion.save()
        return Response(status = status.HTTP_200_OK)
        
class ValidateRegister(APIView):
    permission_classes=[permissions.AllowAny]
    def post(self, request):
        guid = request.data.get('guid')
        username = request.data.get('username')
        if not guid or not username:
            return Response({"detail":"El vínculo no es válido"},status=status.HTTP_400_BAD_REQUEST)
        try:
            verifica = VerificacionRegistroUsuario.objects.get(link=guid)
        except ObjectDoesNotExist as not_exist:
            return Response({"detail":"El vínculo no es válido"},status = status.HTTP_404_NOT_FOUND)
        if(datetime.datetime.now().timestamp() > verifica.vigencia_time.timestamp() or verifica.utilizado > 0):
            return Response({"detail":"El vínculo expiró, verifique su cuenta o solicite un nuevo vínculo"},status = status.HTTP_404_NOT_FOUND)
        usuario = verifica.id_usuario
        usuario.is_active = True
        usuario.save()
        verifica.utilizado = 1
        verifica.save()
        return Response(status = status.HTTP_200_OK)

class CategoriasListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Categorias.objects.filter(activo = True).order_by('titulo')
    serializer_class = CategoriasSerializer

class CategoriaView(generics.RetrieveAPIView):
    lookup_field = 'id'
    queryset = Categorias.objects.filter(activo=True)
    serializer_class = CategoriasSerializer

class VideosListView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'id_categoria'
    def get(self,request,pk):
        videos = Video.objects.filter(id_categoria = pk, activo =True).select_related('id_categoria').order_by('titulo')
        serializer = VideoSerializer(videos, many=True)
        return Response(serializer.data)

class VideosShortListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'id_categoria'
    pagination_class = StandardResultsSetPagination
    def get(self,request):
        videos = Video.objects.filter(activo =True).select_related('id_categoria').order_by('titulo')
        serializer = VideoShortSerializer(videos, many=True)
        page = self.paginate_queryset(serializer.data)
        return self.get_paginated_response(page)

class VideosFindView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'id_categoria'
    pagination_class = StandardResultsSetPagination
    def get(self,request,query):
        videos = Video.objects.filter(titulo__icontains=query, activo=True).select_related('id_categoria').order_by('titulo')
        serializer = VideoSerializer(videos, many=True)
        page = self.paginate_queryset(serializer.data)
        return self.get_paginated_response(page)

class UsersFindView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    def get(self,request,query):
        User = get_user_model()
        usuarios = User.objects.filter(username__icontains=query,is_active=True).order_by('username')
        serializer = UsuariosSerializer(usuarios,many=True)
        page = self.paginate_queryset(serializer.data)
        return self.get_paginated_response(page)

class AddVisitaVideoView(APIView):
    permission_classes=[permissions.AllowAny]
    queryset=VisitasVideo.objects.all()
    
    def post(self,request):
        visitas_video = None
        autor = None
        try:
            id_video = int(request.data["id_video"])
            autor = User.objects.get(username="usuario_generico")
            if id_video > 0:
                visitas_video = VisitasVideo.objects.get(id_video=Video.objects.get(id=id_video),id_usuario=autor)
        except ObjectDoesNotExist as not_exist:
            if(visitas_video is not None):
                visitas_video.visitas = visitas_video.visitas+1
                visitas_video.save()
            elif autor is not None and visitas_video is None:
                video=Video.objects.get(id=id_video)
                visitas_video=VisitasVideo.objects.create(id_video=video,id_usuario=autor,visitas=1)
                visitas_video.save()
            else:
                return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
            return Response(status=status.HTTP_201_CREATED)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"detail":err.message},status=status.HTTP_404_NOT_FOUND)
        if visitas_video is not None:
            visitas_video.visitas = visitas_video.visitas+1
            visitas_video.save()
            return Response(status=status.HTTP_201_CREATED)
        elif autor is not None and visitas_video is None:
            video=Video.objects.get(id=id_video)
            visitas_video=VisitasVideo.objects.create(id_video=video,id_usuario=autor,visitas=1)
            visitas_video.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

class AddVisitaVideoViewAuth(APIView):
    permission_classes=[permissions.IsAuthenticated]
    queryset=VisitasVideo.objects.all()
    
    def post(self,request):
        visitas_video = None
        autor = None
        try:
            id_video = int(request.data["id_video"])
            autor = self.request.user
            if id_video > 0:
                visitas_video = VisitasVideo.objects.get(id_video=Video.objects.get(id=id_video),id_usuario=autor)
        except ObjectDoesNotExist as not_exist:
            if(visitas_video is not None):
                visitas_video.visitas = visitas_video.visitas+1
                visitas_video.save()
            elif autor is not None and visitas_video is None:
                video=Video.objects.get(id=id_video)
                visitas_video=VisitasVideo.objects.create(id_video=video,id_usuario=autor,visitas=1)
                visitas_video.save()
            else:
                return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
            return Response(status=status.HTTP_201_CREATED)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"detail":err.message},status=status.HTTP_404_NOT_FOUND)
        if visitas_video is not None:
            visitas_video.visitas = visitas_video.visitas+1
            visitas_video.save()
            return Response(status=status.HTTP_201_CREATED)
        elif autor is not None and visitas_video is None:
            video=Video.objects.get(id=id_video)
            visitas_video=VisitasVideo.objects.create(id_video=video,id_usuario=autor,visitas=1)
            visitas_video.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

class VisitasVideoDetail(APIView):
    permission_classes=[permissions.AllowAny]
    def get(self,request,pk):
        videos=Video.objects.prefetch_related(Prefetch('visitas_por_video',queryset=VisitasVideo.objects.select_related("id_usuario")))
        videos=[i for i in videos if i.id==pk]
        serializer=VideoSerializer(videos,many=True)
        return Response(serializer.data)

class VisitasVideoList(APIView):
    permission_classes=[permissions.AllowAny]
    def get(self,request):
        videos=Video.objects.annotate(total_visitas=Sum('visitas_por_video__visitas')).prefetch_related(Prefetch('visitas_por_video',queryset=VisitasVideo.objects.select_related("id_usuario"))).order_by('-total_visitas')
        serializer=VideoSerializer(videos,many=True)
        return Response(serializer.data)

class VideoView(generics.RetrieveAPIView):
    lookup_field="id"
    queryset = Video.objects.filter(activo=True).prefetch_related('favoritos_por_video').prefetch_related(Prefetch("comentarios_por_video",queryset=ComentariosVideo.objects.filter(parent_document_id__isnull=True))).annotate(total_comentarios=Count("comentarios_por_video__id_video", filter=Q(comentarios_por_video__parent_document_id__isnull=True))).select_related('id_categoria')
    serializer_class = VideoSerializer

class CreditosVideoView(APIView):
    lookup_field="id_video"
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    def get(self,request,pk):
        creditos = CreditosVideo.objects.filter(id_video = pk)
        serializer = CreditosVideoSerializer(creditos,many=True)
        return Response(serializer.data)

class AllVideosListView(generics.ListAPIView):
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    queryset = Video.objects.filter(activo=True).prefetch_related('favoritos_por_video').prefetch_related(Prefetch("comentarios_por_video",queryset=ComentariosVideo.objects.filter(parent_document_id__isnull=True))).annotate(total_comentarios=Count("comentarios_por_video__id_video", filter=Q(comentarios_por_video__parent_document_id__isnull=True))).select_related('id_categoria').order_by('titulo')
    serializer_class= VideoSerializer

class FavoritosUsuarioVideoListado(generics.ListAPIView):
    permission_classes=[permissions.IsAuthenticated]
    serializer_class=VideosMarcadosFavoritosSerializer
    pagination_class = StandardResultsSetPagination
    def get_queryset(self):
        videos = Video.objects.all().prefetch_related('favoritos_por_video',Prefetch('relatos_por_video',queryset=RelatoVideo.objects.select_related("id_autor")))
        salida = []
        for vid in videos:
            for fav in vid.favoritos_por_video.all():
                if fav.id_usuario == self.request.user and vid.activo and not any(x for x in salida if x.id == vid.id):
                    salida.append(vid)
        return salida

class FavoritosUsuarioVideoSingle(APIView):
    permission_classes=[permissions.AllowAny]
    def get(self,request,pk):
        try:
            salida =Video.objects.all().prefetch_related('favoritos_por_video')
            videos = [i for i in salida if i.id == pk]
            serializer = VideosMarcadosFavoritosSerializer(videos, many=True)
            if(len(videos)> 0):
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"detail":err.message},status=status.HTTP_400_BAD_REQUEST)

class FavoritosVideoSingleUser(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def get(self,request):
        try:
            salida =Video.objects.all().prefetch_related('favoritos_por_video').order_by('titulo')
            videos = []
            for vid in salida:
                for fav in vid.favoritos_por_video.all():
                    if fav.id_usuario.username == self.request.user.username and not any(x for x in videos if x.id == vid.id):
                        videos.append(vid)
            serializer = VideosMarcadosFavoritosSerializer(videos, many=True)
            if(len(videos)> 0):
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"detail":err.message},status=status.HTTP_400_BAD_REQUEST)

class AddFavoritoUsuarioVideo(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def put(self,request):
        video_found=None
        try:
            video=int(request.data["id_video"])
            video_found=Video.objects.get(id=video)
            favorito=FavoritosUsuarioVideo.objects.filter(id_usuario=request.user,id_video=video_found)
            if(video_found is not None):
                serializer=VideosFavoritosSerializer(data={"id_usuario":request.user.id,"id_video":video_found.id})
                if serializer.is_valid():
                    print('serializador de video favorito válido')
                    if(len(favorito) == 0):
                        FavoritosUsuarioVideo.objects.create(id_usuario=request.user,id_video=video_found)
                        return Response(serializer.data,status = status.HTTP_201_CREATED)
                    else:
                        return Response(status = status.HTTP_404_NOT_FOUND)
                else:
                    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(serializer.data,status = status.HTTP_201_CREATED)
        except ObjectDoesNotExist  as err:
            print('error general ',err)
        return Response(status = status.HTTP_400_BAD_REQUEST)
    def delete(self,request):
        video_found=None
        try:
            video=int(request.data["id_video"])
            video_found=Video.objects.get(id=video)
            favorito=FavoritosUsuarioVideo.objects.filter(id_usuario=request.user,id_video=video_found)
            if len(favorito)>0:
                if(video_found is not None):
                    serializer=VideosFavoritosSerializer(data={"id_usuario":request.user.id,"id_video":video_found.id})
                    if serializer.is_valid():
                        x = 0
                        for fav in favorito:
                            fav.delete()
                            x+=1
                        return Response(serializer.data,status = status.HTTP_201_CREATED)
                    else:
                        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist  as err:
            print('error general ',err)
        except Exception  as err:
            print('error general ',err)
        return Response(status = status.HTTP_400_BAD_REQUEST)

class EventoByUser(APIView):
    permission_classes=[permissions.IsAuthenticated]
    queryset=EventoAcervo.objects.all(),
    parser_classes=[MultiPartParser]
    def put(self,request):
        evento_existe=None
        try:
            user = request.user
            titulo = request.data["titulo"]
            descripcion = request.data["descripcion"]
            duracion = int(request.data["duracion"])
            fecha_inicio = request.data["fechainicio"]  #datetime.strptime(request.data["fechainicio"],"%Y-%-m-%-d %-I-%M %p")
            fecha_fin = request.data["fechafin"]    #datetime.strptime(request.data["fechafin"],"%Y-%-m-%-d %-I-%M %p")
            evento_existe = EventoAcervo.objects.get(fechainicio=fecha_inicio,fechafin__lte=fecha_fin)
        except ObjectDoesNotExist as err:
            if(evento_existe is None):
                serializer=EventosAcervoSerializer(data=request.data)
                if serializer.is_valid():
                    if 'filefield' in request.data:
                        presigned_url = ""
                        print('guardando imagen de evento') 
                        upload = request.data['filefield']
                        fss = FileSystemStorage()
                        print("el archivo original de imagen del evento es ",upload)
                        cleaned_file_name = re.sub(r'[ÁáéíóúÄëïöü\s]','_',uuid.uuid4().hex+"_"+upload.name)
                        file = fss.save(cleaned_file_name, upload)
                        file_url = fss.url(file)
                        file_path = settings.MEDIA_ROOT+file_url.replace('media','')
                        print("el archivo original de imagen del evento es ",file_path)
                        uploader = UploaderDefault()
                        presigned_url = uploader.generate_url(settings.AWS_STORAGE_BUCKET_NAME,"EventosImagenes/{}".format(cleaned_file_name))
                        presigned_url = presigned_url[0 : presigned_url.index('?')]
                        print('la ruta en la web del archivo de imagen del evento es ',presigned_url)
                        respuesta = uploader.upload(bucket=settings.AWS_STORAGE_BUCKET_NAME, key="EventosImagenes/{}".format(cleaned_file_name),file=file_path) 
                        fss.delete(cleaned_file_name)
                        evento = EventoAcervo.objects.create(id_usuario=user,titulo=titulo,descripcion=descripcion,duracion=duracion,fechainicio=fecha_inicio,fechafin=fecha_fin,contenedor_img=presigned_url)
                    else:
                        evento = EventoAcervo.objects.create(id_usuario=user,titulo=titulo,descripcion=descripcion,duracion=duracion,fechainicio=fecha_inicio,fechafin=fecha_fin)
                    evento.save()
                    return Response(status=status.HTTP_201_CREATED)
                else:
                    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail":"No es posible ingresar un evento en la misma fecha y horario que uno existente"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print(error)
            if not hasattr(error,'message'):
                return Response({"detail":"Ocurrió un error inesperado"},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"detail":error.message},status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_404_NOT_FOUND)


class EventosPorMes(generics.ListAPIView):
    permission_classes=[permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
    def get(self,request,pk):
        try:
            if(int(pk) > 0):
                fecha_actual = make_aware(datetime.datetime(datetime.datetime.now().year,pk,1))
                fecha_fin = make_aware(datetime.datetime(fecha_actual.year, fecha_actual.month,calendar.monthrange(fecha_actual.year, fecha_actual.month)[1]))
                print('las fechas del rango de eventos son ',fecha_actual,fecha_fin)
                salida = EventoAcervo.objects.filter(fechainicio__gte=fecha_actual, fechafin__lte=fecha_fin).select_related('id_usuario')
                serializer = EventosResponseSerializer(salida, many=True)
                page = self.paginate_queryset(serializer.data)
                return self.get_paginated_response(page)
                # return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                fecha_actual = make_aware(datetime.datetime(datetime.datetime.now().year,1,1))
                fecha_fin = make_aware(datetime.datetime(fecha_actual.year, 12,31))
                print('las fechas del rango de eventos son mayores a',fecha_actual,fecha_fin)
                salida = EventoAcervo.objects.filter(fechainicio__gte=fecha_actual,fechafin__lte=fecha_fin).select_related('id_usuario')
                page = self.paginate_queryset(serializer.data)
                return self.get_paginated_response(page)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"detail":err.message},status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)

class CommentByVideo(APIView):
    permission_classes=[permissions.AllowAny]
    queryset = ComentariosVideo.objects.all()
    def put(self,request):
        try:
            video = Video.objects.get(id=int(request.data["id_video"]))
            categoria = re.sub("\s+","-",video.id_categoria.titulo)
            categoria_sin_reemplazo = video.id_categoria.titulo
            autor = USUARIO_GENERICO
            if request.data["id_autor"] !="usuario_generico":
                autor = int(request.data["id_autor"])
            document_id = uuid.uuid4().hex
            comment = request.data["comentario"]
            serializer=ComentariosVideoSerializer(data={"id_autor":autor,"id_video":video.id,"document_id":document_id, "indexed_fields":{'titulo_categoria':categoria,"titulo_video":video.titulo, "comentario":comment}})
            if serializer.is_valid() or (serializer.errors["id_autor"] is not None and 
            serializer.errors["id_autor"][0] == "Clave primaria \"0\" inválida - objeto no existe."):
                fecha_comentario_actual = datetime.datetime.now(pytz.timezone('America/Mexico_City'))
                User = get_user_model()
                autor_nuevo = None
                if(autor != USUARIO_GENERICO):
                    try:
                        autor_nuevo = User.objects.get(id=int(serializer["id_autor"].value))
                    except:
                        pass
                else:
                    autor_nuevo = User.objects.get(username='usuario_generico')
                comment_db = ComentariosVideo.objects.create(id_autor=autor_nuevo,id_video=video,document_id=document_id, update_time=fecha_comentario_actual)
                client = OpenSearch(
                hosts = [{'host': host, 'port': port}],
                http_compress = True,
                http_auth = auth,
                # client_cert = client_cert_path,
                # client_key = client_key_path,
                use_ssl = True,
                verify_certs = False,
                ssl_assert_hostname = False,
                ssl_show_warn = False,
                #ca_certs = ca_certs_path
                )
                index_name = 'comentarios-interneta-videos-2'
                index_body = {
                'settings': {
                'index': {
                'number_of_shards': 4
                    },
                },
                "mappings":{
                "properties": {
                "titulo_video": {"type": "text", "analyzer": "spanish"},
                "titulo_categoria": {"type": "text", "analyzer": "spanish"},
                "id_video": {"type": "integer"},
                "document_id": {"type": "keyword"},
                "ultima_fecha": {"type": "date", "format":"date_hour_minute_second_fraction"},
                "comentario": {"type": "text", "analyzer": "spanish"},
                "autor":{"type":"keyword"},
                "respuestas":{"type":"integer"}
                        }
                    }
                }
                nombreautor = "usuario_generico" if autor_nuevo is None else autor_nuevo.username
                if not client.indices.exists(index_name):
                    response = client.indices.create(index_name, body=index_body)
                    print('cree el índice ',index_name,'el índice existe ',client.indices.exists(index_name))
                document = {'titulo_categoria':categoria_sin_reemplazo,"titulo_video":video.titulo, "comentario":comment, "id_video":video.id,"document_id":document_id,"ultima_fecha":fecha_comentario_actual.strftime("%Y-%m-%dT%H:%M:%S.%f"),"autor":nombreautor,
                "respuestas":0}
                indexacion = client.index(index=index_name,body=document,refresh=True)
                comment_db.save()
                return Response(status = status.HTTP_201_CREATED)
            return Response(serializer.errors,status.HTTP_404_NOT_FOUND)
        except Exception as err:
            print('excepción general ',err)
            return Response(status = status.HTTP_400_BAD_REQUEST)

class CommentByVideoAuth(APIView):
    permission_classes=[permissions.IsAuthenticated]
    queryset = ComentariosVideo.objects.all()
    def put(self,request):
        try:
            video = Video.objects.get(id=int(request.data["id_video"]))
            categoria = re.sub("\s+","-",video.id_categoria.titulo)
            categoria_sin_reemplazo = video.id_categoria.titulo
            document_id = uuid.uuid4().hex
            comment = request.data["comentario"]
            serializer=ComentariosVideoSerializer(data={"id_autor":request.user.id,"id_video":video.id,"document_id":document_id, "indexed_fields":{'titulo_categoria':categoria,"titulo_video":video.titulo, "comentario":comment}})
            if serializer.is_valid():
                fecha_comentario_actual = datetime.datetime.now(pytz.timezone('America/Mexico_City'))
                autor_nuevo = request.user
                comment_db = ComentariosVideo.objects.create(id_autor=autor_nuevo,id_video=video,document_id=document_id, update_time=fecha_comentario_actual)
                client = OpenSearch(
                hosts = [{'host': host, 'port': port}],
                http_compress = True,
                http_auth = auth,
                # client_cert = client_cert_path,
                # client_key = client_key_path,
                use_ssl = True,
                verify_certs = False,
                ssl_assert_hostname = False,
                ssl_show_warn = False,
                #ca_certs = ca_certs_path
                )
                index_name = 'comentarios-interneta-videos-2'
                index_body = {
                'settings': {
                'index': {
                'number_of_shards': 4
                    },
                },
                "mappings":{
                "properties": {
                "titulo_video": {"type": "text", "analyzer": "spanish"},
                "titulo_categoria": {"type": "text", "analyzer": "spanish"},
                "id_video": {"type": "integer"},
                "document_id": {"type": "keyword"},
                "ultima_fecha": {"type": "date", "format":"date_hour_minute_second_fraction"},
                "comentario": {"type": "text", "analyzer": "spanish"},
                "autor":{"type":"keyword"},
                "respuestas":{"type":"integer"}
                        }
                    }
                }
                nombreautor = "usuario_generico" if autor_nuevo is None else autor_nuevo.username
                print('el nombre del autor en la creación del comentario autorizado es',nombreautor)
                if not client.indices.exists(index_name):
                    response = client.indices.create(index_name, body=index_body)
                    print('cree el índice ',index_name,'el índice existe ',client.indices.exists(index_name))
                document = {'titulo_categoria':categoria_sin_reemplazo,"titulo_video":video.titulo, "comentario":comment, "id_video":video.id,"document_id":document_id,"ultima_fecha":fecha_comentario_actual.strftime("%Y-%m-%dT%H:%M:%S.%f"),"autor":nombreautor,
                "respuestas":0}
                indexacion = client.index(index=index_name,body=document,refresh=True)
                comment_db.save()
                return Response(status = status.HTTP_201_CREATED)
            return Response(serializer.errors,status.HTTP_404_NOT_FOUND)
        except Exception as err:
            print('excepción general ',err)
            return Response(status = status.HTTP_400_BAD_REQUEST)

class AnswerCommentByVideoAuth(APIView):
    permission_classes=[permissions.IsAuthenticated]
    queryset = ComentariosVideo.objects.all()
    def put(self,request):
        try:
            video = Video.objects.get(id=int(request.data["id_video"]))
            document_id = uuid.uuid4().hex
            comment = request.data["comentario"]
            parent_document_id = request.data["parent_document_id"]
            serializer=AnswerComentariosSerializer(data={"id_autor":request.user.id,"document_id":document_id,"parent_document_id":parent_document_id, "indexed_fields":{"comentario":comment}})
            if serializer.is_valid():
                fecha_comentario_actual = datetime.datetime.now(pytz.timezone('America/Mexico_City'))
                autor_nuevo = request.user
                comment_db = ComentariosVideo.objects.create(id_autor=autor_nuevo,id_video=video,document_id=document_id, parent_document_id=parent_document_id, update_time=fecha_comentario_actual)
                client = OpenSearch(
                hosts = [{'host': host, 'port': port}],
                http_compress = True,
                http_auth = auth,
                # client_cert = client_cert_path,
                # client_key = client_key_path,
                use_ssl = True,
                verify_certs = False,
                ssl_assert_hostname = False,
                ssl_show_warn = False,
                #ca_certs = ca_certs_path
                )
                parent_index = "comentarios-interneta-videos-2"
                index_name = 'respuestas-comentarios-interneta-videos-2'
                index_body = {
                'settings': {
                'index': {
                'number_of_shards': 2
                    },
                },
                "mappings": {
                "properties": {
                "autor": {
                    "type": "keyword"
                },
                "comentario": {
                    "type": "text",
                    "analyzer": "spanish"
                },
                "document_id": {
                    "type": "keyword"
                },
                "parent_document_id": {
                    "type": "keyword"
                },
                "respuestas": {
                    "type": "integer"
                },
                "ultima_fecha": {
                    "type": "date",
                    "format": "date_hour_minute_second_fraction"
                }
                }
                },
                }
                nombreautor = "usuario_generico" if autor_nuevo is None else autor_nuevo.username
                print('el nombre del autor en la creación del comentario autorizado es',nombreautor)
                body_update = {"query": {
                "term": {
                "document_id": parent_document_id
                }
                },
                "script" : {
                "source": "ctx._source.respuestas += params.newValue",
                "lang": "painless",
                "params" : {
                "newValue" : 1
                }
                }
                }
                if not client.indices.exists(index_name):
                    response = client.indices.create(index_name, body=index_body)
                    print('cree el índice ',index_name,'el índice existe ',client.indices.exists(index_name))
                document = {"comentario":comment, "document_id":document_id,"parent_document_id":parent_document_id, "ultima_fecha":fecha_comentario_actual.strftime("%Y-%m-%dT%H:%M:%S.%f"),"autor":nombreautor,
                "respuestas":0}
                indexacion = client.index(index=index_name,body=document,refresh=True)
                client.update_by_query(index=parent_index,body=body_update)
                comment_db.save()
                return Response(status = status.HTTP_201_CREATED)
            return Response(serializer.errors,status.HTTP_404_NOT_FOUND)
        except Exception as err:
            print('excepción general ',err)
            return Response(status = status.HTTP_400_BAD_REQUEST)

class RelatoByVideo(APIView):
    permission_classes=[permissions.AllowAny]
    queryset = ComentariosVideo.objects.all()
    def put(self,request):
        try:
            video = Video.objects.get(id=int(request.data["id_video"]))
            categoria = re.sub("\s+","-",video.id_categoria.titulo)
            categoria_sin_reemplazo = video.id_categoria.titulo
            autor = USUARIO_GENERICO
            if request.data["id_autor"] !="usuario_generico":
                autor = int(request.data["id_autor"])
            document_id = uuid.uuid4().hex
            relato = request.data["relato"]
            serializer = RelatoVideoSerializer(data={"id_autor":autor,"id_video":video.id,"document_id":document_id, "indexed_fields":{'titulo_categoria':categoria,"titulo_video":video.titulo}, "relato":relato})
            if serializer.is_valid() or (serializer.errors["id_autor"] is not None and 
            serializer.errors["id_autor"][0] == "Clave primaria \"0\" inválida - objeto no existe."):
                fecha_relato_actual = datetime.datetime.now(pytz.timezone('America/Mexico_City'))
                User = get_user_model()
                autor_nuevo = None
                if(autor != USUARIO_GENERICO):
                    try:
                        autor_nuevo = User.objects.get(id=int(serializer["id_autor"].value))
                    except:
                        pass
                else:
                    autor_nuevo = User.objects.get(username='usuario_generico')
                relato_db = RelatoVideo.objects.create(id_autor=autor_nuevo,id_video=video,document_id=document_id, update_time=fecha_relato_actual)
                client = OpenSearch(
                hosts = [{'host': host, 'port': port}],
                http_compress = True,
                http_auth = auth,
                # client_cert = client_cert_path,
                # client_key = client_key_path,
                use_ssl = True,
                verify_certs = False,
                ssl_assert_hostname = False,
                ssl_show_warn = False,
                #ca_certs = ca_certs_path
                )
                index_name = 'relatostextuales-interneta-videos-2'
                index_body = {
                'settings': {
                'index': {
                'number_of_shards': 4
                    },
                },
                "mappings":{
                "properties": {
                "titulo_video": {"type": "text", "analyzer": "spanish"},
                "titulo_categoria": {"type": "text", "analyzer": "spanish"},
                "id_video": {"type": "integer"},
                "document_id": {"type": "keyword"},
                "ultima_fecha": {"type": "date", "format":"date_hour_minute_second_fraction"},
                "relato": {"type": "text", "analyzer": "spanish"},
                "autor":{"type":"keyword"},
                "espodcast":{"type":"boolean"},
                "contenedor_aws":{"type":"keyword"}
                        }
                    }
                }
                nombreautor = "usuario_generico" if autor_nuevo is None else autor_nuevo.username
                if not client.indices.exists(index_name):
                    response = client.indices.create(index_name, body=index_body)
                    print('cree el índice ',index_name,'el índice existe ',client.indices.exists(index_name))
                document = {'titulo_categoria':categoria_sin_reemplazo,"titulo_video":video.titulo, "relato":relato, "id_video":video.id,"document_id":document_id,"ultima_fecha":fecha_relato_actual.strftime("%Y-%m-%dT%H:%M:%S.%f"),"autor":nombreautor,"espodcast":False,"contenedor_aws":""}
                indexacion = client.index(index=index_name,body=document,refresh=True)
                relato_db.save()
                return Response(status = status.HTTP_201_CREATED)
            return Response(serializer.errors,status.HTTP_404_NOT_FOUND)
        except Exception as err:
            print('excepción general ',err)
            return Response(status = status.HTTP_400_BAD_REQUEST)


class RelatoTextualByVideoAuth(APIView):
    permission_classes=[permissions.IsAuthenticated]
    queryset = ComentariosVideo.objects.all()
    parser_classes=[MultiPartParser]
    def put(self,request):
        try:
            print('entre a envío de relato o podcast')
            serializer = RelatoVideoSerializer(data=request.data)
            document_id = uuid.uuid4().hex
            print('finaliza envío de relato o podcast')
            if(serializer.is_valid() or (serializer.errors["id_autor"] is not None and 
            serializer.errors["id_autor"][0] == "Clave primaria \"0\" inválida - objeto no existe.")):
                video = Video.objects.get(id=serializer["id_video"].value)
                categoria = re.sub("\s+","-",video.id_categoria.titulo)
                categoria_sin_reemplazo = video.id_categoria.titulo
                relato = serializer["relato"].value
                espodcast = serializer["espodcast"].value
                if(serializer.is_valid() or (serializer.errors["id_autor"] is not None and 
            serializer.errors["id_autor"][0] == "Clave primaria \"0\" inválida - objeto no existe.")):
                    print('guardando objeto relato e indexando')
                    fecha_relato_actual = datetime.datetime.now(pytz.timezone('America/Mexico_City'))
                    User = get_user_model()
                    autor_nuevo = request.user
                    relato_db = RelatoVideo.objects.create(id_autor=autor_nuevo,id_video=video,document_id=document_id, update_time=fecha_relato_actual)
                    client = OpenSearch(
                    hosts = [{'host': host, 'port': port}],
                    http_compress = True,
                    http_auth = auth,
                    # client_cert = client_cert_path,
                    # client_key = client_key_path,
                    use_ssl = True,
                    verify_certs = False,
                    ssl_assert_hostname = False,
                    ssl_show_warn = False,
                    #ca_certs = ca_certs_path
                    )
                    index_name = 'relatostextuales-interneta-videos-2'
                    index_body = {
                    'settings': {
                    'index': {
                        'number_of_shards': 4
                        },
                    },
                    "mappings":{
                        "properties": {
                        "titulo_video": {"type": "text", "analyzer": "spanish"},
                        "titulo_categoria": {"type": "text", "analyzer": "spanish"},
                        "id_video": {"type": "integer"},
                        "document_id": {"type": "keyword"},
                        "ultima_fecha": {"type": "date", "format":"date_hour_minute_second_fraction"},
                        "relato": {"type": "text", "analyzer": "spanish"},
                        "autor":{"type":"keyword"},
                        "espodcast":{"type":"boolean"},
                        "contenedor_aws":{"type":"keyword"}
                            }
                        }
                    }
                    nombreautor = "usuario_generico" if autor_nuevo is None else autor_nuevo.username
                    if not client.indices.exists(index_name):
                        response = client.indices.create(index_name, body=index_body)
                        print('cree el índice ',index_name,'el índice existe ',client.indices.exists(index_name))
                    document = {'titulo_categoria':categoria_sin_reemplazo,"titulo_video":video.titulo, "relato":relato, "id_video":video.id,"document_id":document_id,"ultima_fecha":fecha_relato_actual.strftime("%Y-%m-%dT%H:%M:%S.%f"),"autor":nombreautor, "espodcast":False, "contenedor_aws":""}
                    indexacion = client.index(index=index_name,body=document,refresh=True)
                    relato_db.save()
                    return Response(status = status.HTTP_201_CREATED)
            return Response(serializer.errors,status.HTTP_404_NOT_FOUND)
        except Exception as err:
            print('excepción general ',err,sys.exc_info())
            return Response(status = status.HTTP_400_BAD_REQUEST)

class RelatoByVideoAuth(APIView):
    permission_classes=[permissions.IsAuthenticated]
    queryset = ComentariosVideo.objects.all()
    parser_classes=[MultiPartParser]
    def put(self,request):
        try:
            print('entre a envío de relato o podcast')
            serializer = RelatoVideoSerializer(data=request.data)
            document_id = uuid.uuid4().hex
            serializer.initial_data["id_autor"] = request.user.id
            serializer.initial_data["document_id"] = document_id
            print('finaliza envío de relato o podcast')
            if(serializer.is_valid() or (serializer.errors["id_autor"] is not None and 
            serializer.errors["id_autor"][0] == "Clave primaria \"0\" inválida - objeto no existe.")):
                video = Video.objects.get(id=serializer["id_video"].value)
                categoria = re.sub("\s+","-",video.id_categoria.titulo)
                categoria_sin_reemplazo = video.id_categoria.titulo
                relato = serializer["relato"].value
                espodcast = serializer["espodcast"].value
                presigned_url = ""
                print('guardando podcast')
                upload = request.data['filefield']
                fss = FileSystemStorage()
                print("el archivo original del blob es ",upload)
                cleaned_file_name = re.sub(r'[ÁáéíóúÄëïöü\s]','_',uuid.uuid4().hex+".wav")
                file = fss.save(cleaned_file_name, upload)
                file_url = fss.url(file)
                file_path = settings.MEDIA_ROOT+file_url.replace('media','')
                print("el archivo original del blob es ",file_path)
                uploader = UploaderDefault()
                presigned_url = uploader.generate_url(settings.AWS_STORAGE_BUCKET_NAME,cleaned_file_name)
                presigned_url = presigned_url[0 : presigned_url.index('?')]
                print('la ruta en la web del archivo de podcast es ',presigned_url)
                print('el relato finalmente es ',relato)
                respuesta = uploader.upload(bucket=settings.AWS_STORAGE_BUCKET_NAME, key=cleaned_file_name,file=file_path)     
                fss.delete(cleaned_file_name)
                serializer = RelatoVideoSerializer(data={"id_autor":request.user.id,"id_video":video.id,"document_id":document_id, "indexed_fields":{'titulo_categoria':categoria,"titulo_video":video.titulo},"relato":relato,"espodcast":espodcast, "contenedor_aws":presigned_url})
                if(serializer.is_valid()):
                    print('guardando objeto relato e indexando')
                    fecha_relato_actual = datetime.datetime.now(pytz.timezone('America/Mexico_City'))
                    User = get_user_model()
                    autor_nuevo = request.user
                    relato_db = RelatoVideo.objects.create(id_autor=autor_nuevo,id_video=video,document_id=document_id, update_time=fecha_relato_actual)
                    client = OpenSearch(
                    hosts = [{'host': host, 'port': port}],
                    http_compress = True,
                    http_auth = auth,
                    # client_cert = client_cert_path,
                    # client_key = client_key_path,
                    use_ssl = True,
                    verify_certs = False,
                    ssl_assert_hostname = False,
                    ssl_show_warn = False,
                    #ca_certs = ca_certs_path
                    )
                    index_name = 'relatostextuales-interneta-videos-2'
                    index_body = {
                    'settings': {
                    'index': {
                        'number_of_shards': 4
                        },
                    },
                    "mappings":{
                        "properties": {
                        "titulo_video": {"type": "text", "analyzer": "spanish"},
                        "titulo_categoria": {"type": "text", "analyzer": "spanish"},
                        "id_video": {"type": "integer"},
                        "document_id": {"type": "keyword"},
                        "ultima_fecha": {"type": "date", "format":"date_hour_minute_second_fraction"},
                        "relato": {"type": "text", "analyzer": "spanish"},
                        "autor":{"type":"keyword"},
                        "espodcast":{"type":"boolean"},
                        "contenedor_aws":{"type":"keyword"}
                            }
                        }
                    }
                    nombreautor = "usuario_generico" if autor_nuevo is None else autor_nuevo.username
                    if not client.indices.exists(index_name):
                        response = client.indices.create(index_name, body=index_body)
                        print('cree el índice ',index_name,'el índice existe ',client.indices.exists(index_name))
                    document = {'titulo_categoria':categoria_sin_reemplazo,"titulo_video":video.titulo, "relato":relato, "id_video":video.id,"document_id":document_id,"ultima_fecha":fecha_relato_actual.strftime("%Y-%m-%dT%H:%M:%S.%f"),"autor":nombreautor, "espodcast":espodcast, "contenedor_aws":presigned_url}
                    indexacion = client.index(index=index_name,body=document,refresh=True)
                    relato_db.save()
                    #fss.delete(cleaned_file_name)
                    return Response(status = status.HTTP_201_CREATED)
            return Response(serializer.errors,status.HTTP_404_NOT_FOUND)
        except Exception as err:
            print('excepción general ',err,sys.exc_info())
            return Response(status = status.HTTP_400_BAD_REQUEST)

class SearchAnswerComment(APIView):
    permission_classes=[permissions.AllowAny]
    queryset = ComentariosVideo.objects.all()
    def post(self,request):
        try:
            index_name = 'respuestas-comentarios-interneta-videos-2'
            parent_document = request.data["parent_document"]
            # pagina_inicial = request.data["pagina_inicial"]
            client = OpenSearch(
                hosts = [{'host': host, 'port': port}],
                http_compress = True,
                http_auth = auth,
                use_ssl = True,
                verify_certs = False,
                ssl_assert_hostname = False,
                ssl_show_warn = False,
                )
            consulta = {
                    # "from":pagina_inicial,
                    # "size":PAGINACION,
                    "query":{
                            "term":{
                                "parent_document_id":parent_document
                            }
                    },
                    "sort":[
                        {
                        "ultima_fecha":{
                            "order":"asc",
                            "unmapped_type":"date"
                        }
                        }
                    ],
                    "track_total_hits": True
                }
            respuesta = client.search(
            body=consulta,
            index=index_name
            )
            listarespuesta=[]
            for hit in respuesta["hits"]["hits"]:
                listarespuesta.append({
                "comentario":hit["_source"]["comentario"],
                "ultima_fecha":hit["_source"]["ultima_fecha"],
                "autor": "anónimo" if hit["_source"]["autor"] == "usuario_generico" else hit["_source"]["autor"],
                "document_id":hit["_source"]["document_id"],
                "total":respuesta["hits"]["total"]["value"],
                # "paginacion":PAGINACION})
                })
            return Response(listarespuesta,status = status.HTTP_200_OK)
        except Exception as err:
            print('excepción general ',err)
            return Response(status = status.HTTP_400_BAD_REQUEST)

class SearchSingleComment(APIView):
    permission_classes = [permissions.AllowAny]
    queryset = ComentariosVideo.objects.all()
    def post(self, request):
        lista_respuesta = []
        try:
            index_name = 'comentarios-interneta-videos-2'
            identificador = request.data["identificador"]
            client = OpenSearch(
                hosts = [{'host': host, 'port': port}],
                http_compress = True,
                http_auth = auth,
                use_ssl = True,
                verify_certs = False,
                ssl_assert_hostname = False,
                ssl_show_warn = False,
                )
            consulta = {
                    "query":{
                        "term":{
                            "document_id":identificador
                        }
                    },
                    "sort":[
                        {
                        "ultima_fecha":{
                            "order":"desc",
                            "unmapped_type":"date"
                        }
                        }
                    ],
                    "track_total_hits": True
                }
            
            respuesta = client.search(
                body=consulta,
                index=index_name
            )
            listarespuesta=[]
            for hit in respuesta["hits"]["hits"]:
                    listarespuesta.append({"titulo_categoria":hit["_source"]["titulo_categoria"],
                    "titulo_video":hit["_source"]["titulo_video"],
                    "comentario":hit["_source"]["comentario"],
                    "id_video":hit["_source"]["id_video"],
                    "ultima_fecha":hit["_source"]["ultima_fecha"],
                    "autor": "anónimo" if hit["_source"]["autor"] == "usuario_generico" else hit["_source"]["autor"],
                    "respuestas":hit["_source"]["respuestas"],
                    "document_id":hit["_source"]["document_id"],
                    "total":respuesta["hits"]["total"]["value"],
                    "paginacion":PAGINACION})
            return Response(listarespuesta,status = status.HTTP_200_OK)
        except Exception as err:
            print(err)
            return Response(status = status.HTTP_400_BAD_REQUEST)

class SearchComment(APIView):
    permission_classes=[permissions.AllowAny]
    queryset = ComentariosVideo.objects.all()
    def post(self,request):
        try:
            index_name = 'comentarios-interneta-videos-2'
            query = request.data["query"]
            categoria = request.data["categoria"]
            frase = request.data["frase"]
            autor = request.data["autor"]
            puede = request.data["puede"]
            prefijo = request.data["prefijo"]
            video = request.data["video"]
            pagina_inicial = request.data["pagina_inicial"]
            client = OpenSearch(
                hosts = [{'host': host, 'port': port}],
                http_compress = True,
                http_auth = auth,
                use_ssl = True,
                verify_certs = False,
                ssl_assert_hostname = False,
                ssl_show_warn = False,
                )
            if (not isinstance(pagina_inicial,int) or (video !="" and not isinstance(video,int)) or (query == "" and prefijo == "" and video=="")):
                print(type(video))
                print('peticion incorrecta',video is not int)
                return Response(status = status.HTTP_400_BAD_REQUEST)
            consulta = None
            #consulta no especificada, video especificado
            if(video != "" and query == "" and categoria == "" and frase == False and puede == "" and prefijo == ""):
                print("nada")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                            "range":{
                                "id_video":{
                                    "gt":(video-1),
                                    "lte":video
                                }
                            }
                    },
                    "sort":[
                        {
                        "ultima_fecha":{
                            "order":"desc",
                            "unmapped_type":"date"
                        }
                        }
                    ],
                    "track_total_hits": True
                }
            #categoria no especificada, video especificado
            if(video != "" and categoria == "" and query!="" and frase == False and puede == "" and prefijo == ""):
                print("nada y video",video)
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match":{
                                "comentario":query
                            }
                        }],
                        "filter":{
                            "range":{
                                "id_video":{
                                    "gt":(video-1),
                                    "lte":video
                                }
                            }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video != "" and categoria == "" and query!="" and frase == True and puede == "" and prefijo == ""):
                print("frase y video ",video)
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase":{
                                "comentario":query
                            }
                        }]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video != "" and categoria == "" and query!="" and frase == False and puede == "" and prefijo != ""):
                print("prefijo y video ",video)
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_bool_prefix":{
                                "comentario":query+" "+prefijo
                            }
                        }]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video != "" and categoria == "" and query!="" and frase == True and puede == "" and prefijo != ""):
                print("frase y prefijo y video ",video)
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase_prefix":{
                                "comentario":query+" "+prefijo
                            }
                        }]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            #categoria no especificada, video no especificado
            if(video == "" and categoria == "" and query!="" and frase == False and puede == "" and prefijo == ""):
                print("nada")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match":{
                                "comentario":query
                            }
                        }]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria == "" and query!="" and frase == True and puede == "" and prefijo == ""):
                print("frase")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase":{
                                "comentario":query
                            }
                        }]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria == "" and query!="" and frase == False and puede == "" and prefijo != ""):
                print("prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_bool_prefix":{
                                "comentario":query+" "+prefijo
                            }
                        }]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria == "" and query!="" and frase == True and puede == "" and prefijo != ""):
                print("frase y prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase_prefix":{
                                "comentario":query+" "+prefijo
                            }
                        }]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            #categoría no especificada y opcionales especificados
            if(video == "" and categoria == "" and query!="" and frase == False and puede != "" and prefijo == ""):
                print('puede')
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match":{
                                "comentario":query
                            }
                        }],
                        "should":[{
                            "match":{
                                "comentario":puede
                            }
                        }
                        ]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria == "" and query!="" and frase == True and puede != "" and prefijo == ""):
                print('frase y puede')
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase":{
                                "comentario":query
                            }
                        }],
                        "should":[{
                            "match":{
                                "comentario":puede
                            }
                        }
                        ]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria == "" and query!="" and frase == False and puede != "" and prefijo != ""):
                print("puede y prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_bool_prefix":{
                                "comentario":query+" "+prefijo
                            }
                        }],
                        "should":[{
                            "match":{
                                "comentario":puede
                            }
                        }
                        ]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria == "" and query!="" and frase == True and puede != "" and prefijo != ""):
                print("frase, puede y prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase_prefix":{
                                "comentario":query+" "+prefijo
                            }
                        }],
                        "should":[{
                            "match":{
                                "comentario":puede
                            }
                        }
                        ]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            #categoria especificada
            if(video == "" and categoria != "" and query!="" and frase == False and puede == "" and prefijo == ""):
                print("categoria")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match":{
                                "comentario":query
                            }
                        }],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria != "" and query!="" and frase == True and puede == "" and prefijo == ""):
                print("categoria y frase")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase":{
                                "comentario":query
                            }
                        }],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria != "" and query!="" and frase == False and puede == "" and prefijo != ""):
                print("categoría y prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_bool_prefix":{
                                "comentario":query+" "+prefijo
                            }
                        }],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria != "" and query!="" and frase == True and puede == "" and prefijo != ""):
                print("categoría, frase y prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase_prefix":{
                                "comentario":query+" "+prefijo
                            }
                        }],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            # opcionales y categorías especificadas
            if(video == "" and categoria != "" and query!="" and frase == False and puede != "" and prefijo == ""):
                print("categoría y puede")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match":{
                                "comentario":query
                            }
                        }],
                        "should":[{
                            "match":{
                                "comentario":puede
                            }
                        }
                        ],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria != "" and query!="" and frase == True and puede != "" and prefijo == ""):
                print("categoría, frase y puede")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase":{
                                "comentario":query
                            }
                        }],
                       "should":[{
                            "match":{
                                "comentario":puede
                            }
                        }
                        ],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria != "" and query!="" and frase == False and puede != "" and prefijo != ""):
                print("categoría, puede y prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_bool_prefix":{
                                "comentario":query+" "+prefijo
                            }
                        }],
                        "should":[{
                            "match":{
                                "comentario":puede
                            }
                        }
                        ],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria != "" and query!="" and frase == True and puede != "" and prefijo != ""):
                print("categoría, frase, puede y prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase_prefix":{
                                "comentario":query+" "+prefijo
                            }
                        }],
                        "should":[{
                            "match":{
                                "comentario":puede
                            }
                        }
                        ],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if consulta is None:
                return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
            print('la consulta es ',consulta)
            respuesta = client.search(
                body=consulta,
                index=index_name
            )
            listarespuesta=[]
            for hit in respuesta["hits"]["hits"]:
                if autor=="":
                    listarespuesta.append({"titulo_categoria":hit["_source"]["titulo_categoria"],
                    "titulo_video":hit["_source"]["titulo_video"],
                    "comentario":hit["_source"]["comentario"],
                    "id_video":hit["_source"]["id_video"],
                    "ultima_fecha":hit["_source"]["ultima_fecha"],
                    "autor": "anónimo" if hit["_source"]["autor"] == "usuario_generico" else hit["_source"]["autor"],
                    "respuestas":hit["_source"]["respuestas"],
                    "document_id":hit["_source"]["document_id"],
                    "total":respuesta["hits"]["total"]["value"],
                    "paginacion":PAGINACION})
                else:
                    if (hit["_source"]["autor"] == "usuario_generico" and autor=="anónimo"):
                        listarespuesta.append({"titulo_categoria":hit["_source"]["titulo_categoria"],
                        "titulo_video":hit["_source"]["titulo_video"],
                        "comentario":hit["_source"]["comentario"],
                        "id_video":hit["_source"]["id_video"],
                        "ultima_fecha":hit["_source"]["ultima_fecha"],
                        "autor": "anónimo" if hit["_source"]["autor"] == "usuario_generico" else hit["_source"]["autor"],
                        "respuestas":hit["_source"]["respuestas"],
                        "document_id":hit["_source"]["document_id"],
                        "total":respuesta["hits"]["total"]["value"],
                        "paginacion":PAGINACION})
                    if (hit["_source"]["autor"] != "usuario_generico" and autor==hit["_source"]["autor"]):
                        listarespuesta.append({"titulo_categoria":hit["_source"]["titulo_categoria"],
                        "titulo_video":hit["_source"]["titulo_video"],
                        "comentario":hit["_source"]["comentario"],
                        "id_video":hit["_source"]["id_video"],
                        "ultima_fecha":hit["_source"]["ultima_fecha"],
                        "autor": "anónimo" if hit["_source"]["autor"] == "usuario_generico" else hit["_source"]["autor"],
                        "respuestas":hit["_source"]["respuestas"],
                        "document_id":hit["_source"]["document_id"],
                        "total":respuesta["hits"]["total"]["value"],
                        "paginacion":PAGINACION})
                    # total_con_autor = len(listarespuesta)
                    # for elem in listarespuesta:
                    #     elem["total"] = total_con_autor
                    
            return Response(listarespuesta,status = status.HTTP_200_OK)
        except Exception as err:
            print(err)
            return Response(status = status.HTTP_400_BAD_REQUEST)

class SearchSingleRelato(APIView):
    permission_classes = [permissions.AllowAny]
    queryset = RelatoVideo.objects.all()
    def post(self, request):
        lista_respuesta = []
        try:
            index_name = 'relatostextuales-interneta-videos-2'
            identificador = request.data["identificador"]
            client = OpenSearch(
                hosts = [{'host': host, 'port': port}],
                http_compress = True,
                http_auth = auth,
                use_ssl = True,
                verify_certs = False,
                ssl_assert_hostname = False,
                ssl_show_warn = False,
                )
            consulta = {
                    "query":{
                        "term":{
                            "document_id":identificador
                        }
                    },
                    "sort":[
                        {
                        "ultima_fecha":{
                            "order":"desc",
                            "unmapped_type":"date"
                        }
                        }
                    ],
                    "track_total_hits": True
                }
            
            respuesta = client.search(
                body=consulta,
                index=index_name
            )
            for hit in respuesta["hits"]["hits"]:
                lista_respuesta.append({"titulo_categoria":hit["_source"]["titulo_categoria"],
                "titulo_video":hit["_source"]["titulo_video"],
                "relato":hit["_source"]["relato"],
                "id_video":hit["_source"]["id_video"],
                "ultima_fecha":hit["_source"]["ultima_fecha"],
                "autor": "anónimo" if hit["_source"]["autor"] == "usuario_generico" else hit["_source"]["autor"],
                "document_id":hit["_source"]["document_id"],
                "espodcast":hit["_source"]["espodcast"],
                "contenedor_aws":hit["_source"]["contenedor_aws"],
                "total":respuesta["hits"]["total"]["value"]})
        except Exception as err:
            print('error consultando un solo relato',err)
            return Response(status = status.HTTP_400_BAD_REQUEST)
        return Response(lista_respuesta,status = status.HTTP_200_OK)

class SearchBySeveralRelatos(APIView):
    permission_classes = [permissions.AllowAny]
    queryset = RelatoVideo.objects.all()
    def post(self, request):
        lista_respuesta = []
        try:
            index_name = 'relatostextuales-interneta-videos-2'
            relatos = request.data["relatos"]
            client = OpenSearch(
                hosts = [{'host': host, 'port': port}],
                http_compress = True,
                http_auth = auth,
                use_ssl = True,
                verify_certs = False,
                ssl_assert_hostname = False,
                ssl_show_warn = False,
                )
            consulta = {
                    "query":{
                        "terms":{
                            "document_id":relatos
                        }
                    },
                    "sort":[
                        {
                        "ultima_fecha":{
                            "order":"desc",
                            "unmapped_type":"date"
                        }
                        }
                    ],
                    "track_total_hits": True
                }
            
            respuesta = client.search(
                body=consulta,
                index=index_name
            )
            for hit in respuesta["hits"]["hits"]:
                lista_respuesta.append({"titulo_categoria":hit["_source"]["titulo_categoria"],
                "titulo_video":hit["_source"]["titulo_video"],
                "relato":hit["_source"]["relato"],
                "id_video":hit["_source"]["id_video"],
                "ultima_fecha":hit["_source"]["ultima_fecha"],
                "autor": "anónimo" if hit["_source"]["autor"] == "usuario_generico" else hit["_source"]["autor"],
                "document_id":hit["_source"]["document_id"],
                "espodcast":hit["_source"]["espodcast"],
                "contenedor_aws":hit["_source"]["contenedor_aws"],
                "total":respuesta["hits"]["total"]["value"]})
        except Exception as err:
            print('error consultando un solo relato',err)
            return Response(status = status.HTTP_400_BAD_REQUEST)
        return Response(lista_respuesta,status = status.HTTP_200_OK)
        
class CountRelatos(APIView):
    permission_classes=[permissions.AllowAny]
    queryset=RelatoVideo.objects.values('document_id').count()
    def get(self,request):
        try:
            cuenta=self.queryset
            print('la cuenta de relatos es ',cuenta)
            return Response({"result":cuenta},status=status.HTTP_200_OK)     
        except Exception as err:
            return Response({"detail":str(err)},status=status.HTTP_400_BAD_REQUEST)
class SearchRelato(APIView):
    permission_classes=[permissions.AllowAny]
    queryset = RelatoVideo.objects.all()
    def post(self,request):
        try:
            id_documento = None
            index_name = 'relatostextuales-interneta-videos-2'
            query = request.data["query"]
            categoria = request.data["categoria"]
            frase = request.data["frase"]
            autor = request.data["autor"]
            puede = request.data["puede"]
            prefijo = request.data["prefijo"]
            video = request.data["video"]
            pagina_inicial = request.data["pagina_inicial"]
            try:
                id_documento = request.data["id_documento"]
                print('El id del documento es ',id_documento)
            except:
                pass
            client = OpenSearch(
                hosts = [{'host': host, 'port': port}],
                http_compress = True,
                http_auth = auth,
                use_ssl = True,
                verify_certs = False,
                ssl_assert_hostname = False,
                ssl_show_warn = False,
                )
            if (not isinstance(pagina_inicial,int) or (video !="" and not isinstance(video,int))):
                print(type(video))
                print('peticion incorrecta',video is not int)
                return Response(status = status.HTTP_400_BAD_REQUEST)
            consulta = None
            #nada especificado, todos los relatos
            if(video == "" and query == "" and categoria == "" and frase == False and puede == "" and prefijo == ""):
                print("todos los relatos")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "sort":[
                        {
                        "ultima_fecha":{
                            "order":"desc",
                            "unmapped_type":"date"
                        }
                        }
                    ],
                    "track_total_hits": True
                }
            #nada especificado, todos los relatos, excepto el documento especificado
            if(video == "" and id_documento is not None and query == "" and categoria == "" and frase == False and puede == "" and prefijo == ""):
                print("todos los relatos")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must_not":{
                                "term":{
                                    "document_id":id_documento
                                }
                            }
                        }
                    },
                    "sort":[
                        {
                        "ultima_fecha":{
                            "order":"desc",
                            "unmapped_type":"date"
                        }
                        }
                    ],
                    "track_total_hits": True
                }
            #consulta no especificada, video especificado
            if(video != "" and query == "" and categoria == "" and frase == False and puede == "" and prefijo == ""):
                print("nada")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                            "range":{
                                "id_video":{
                                    "gt":(video-1),
                                    "lte":video
                                }
                            }
                        },
                    "sort":[
                        {
                        "ultima_fecha":{
                            "order":"desc",
                            "unmapped_type":"date"
                        }
                        }
                    ],
                    "track_total_hits": True
                }
            #consulta no especificada, video especificado, excepto el documento específico
            if(video != "" and id_documento is not None and query == "" and categoria == "" and frase == False and puede == "" and prefijo == ""):
                print("nada")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must_not":{
                                "term":{
                                    "document_id":id_documento
                                }
                            },
                            "must":{
                                "range":{
                                "id_video":{
                                    "gt":(video-1),
                                    "lte":video
                                }
                            }
                            }
                        }
                    },
                    "sort":[
                        {
                        "ultima_fecha":{
                            "order":"desc",
                            "unmapped_type":"date"
                        }
                        }
                    ],
                    "track_total_hits": True
                }
            #categoria no especificada, video especificado
            if(video != "" and categoria == "" and query!="" and frase == False and puede == "" and prefijo == ""):
                print("nada y video",video)
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match":{
                                "relato":query
                            }
                        }],
                        "filter":{
                            "range":{
                                "id_video":{
                                    "gt":(video-1),
                                    "lte":video
                                }
                            }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video != "" and categoria == "" and query!="" and frase == True and puede == "" and prefijo == ""):
                print("frase y video ",video)
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase":{
                                "relato":query
                            }
                        }]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video != "" and categoria == "" and query!="" and frase == False and puede == "" and prefijo != ""):
                print("prefijo y video ",video)
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_bool_prefix":{
                                "relato":query+" "+prefijo
                            }
                        }]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video != "" and categoria == "" and query!="" and frase == True and puede == "" and prefijo != ""):
                print("frase y prefijo y video ",video)
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase_prefix":{
                                "relato":query+" "+prefijo
                            }
                        }]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            #categoria no especificada, video no especificado
            if(video == "" and categoria == "" and query!="" and frase == False and puede == "" and prefijo == ""):
                print("nada")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match":{
                                "relato":query
                            }
                        }]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria == "" and query!="" and frase == True and puede == "" and prefijo == ""):
                print("frase")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase":{
                                "relato":query
                            }
                        }]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria == "" and query!="" and frase == False and puede == "" and prefijo != ""):
                print("prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_bool_prefix":{
                                "relato":query+" "+prefijo
                            }
                        }]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria == "" and query!="" and frase == True and puede == "" and prefijo != ""):
                print("frase y prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase_prefix":{
                                "relato":query+" "+prefijo
                            }
                        }]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            #categoría no especificada y opcionales especificados
            if(video == "" and categoria == "" and query!="" and frase == False and puede != "" and prefijo == ""):
                print('puede')
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match":{
                                "relato":query
                            }
                        }],
                        "should":[{
                            "match":{
                                "relato":puede
                            }
                        }
                        ]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria == "" and query!="" and frase == True and puede != "" and prefijo == ""):
                print('frase y puede')
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase":{
                                "relato":query
                            }
                        }],
                        "should":[{
                            "match":{
                                "relato":puede
                            }
                        }
                        ]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria == "" and query!="" and frase == False and puede != "" and prefijo != ""):
                print("puede y prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_bool_prefix":{
                                "relato":query+" "+prefijo
                            }
                        }],
                        "should":[{
                            "match":{
                                "relato":puede
                            }
                        }
                        ]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria == "" and query!="" and frase == True and puede != "" and prefijo != ""):
                print("frase, puede y prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase_prefix":{
                                "relato":query+" "+prefijo
                            }
                        }],
                        "should":[{
                            "match":{
                                "relato":puede
                            }
                        }
                        ]
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            #categoria especificada
            if(video == "" and categoria != "" and query!="" and frase == False and puede == "" and prefijo == ""):
                print("categoria")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match":{
                                "relato":query
                            }
                        }],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria != "" and query!="" and frase == True and puede == "" and prefijo == ""):
                print("categoria y frase")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase":{
                                "relato":query
                            }
                        }],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria != "" and query!="" and frase == False and puede == "" and prefijo != ""):
                print("categoría y prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_bool_prefix":{
                                "relato":query+" "+prefijo
                            }
                        }],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria != "" and query!="" and frase == True and puede == "" and prefijo != ""):
                print("categoría, frase y prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase_prefix":{
                                "relato":query+" "+prefijo
                            }
                        }],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            # opcionales y categorías especificadas
            if(video == "" and categoria != "" and query!="" and frase == False and puede != "" and prefijo == ""):
                print("categoría y puede")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match":{
                                "relato":query
                            }
                        }],
                        "should":[{
                            "match":{
                                "relato":puede
                            }
                        }
                        ],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria != "" and query!="" and frase == True and puede != "" and prefijo == ""):
                print("categoría, frase y puede")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase":{
                                "relato":query
                            }
                        }],
                       "should":[{
                            "match":{
                                "relato":puede
                            }
                        }
                        ],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria != "" and query!="" and frase == False and puede != "" and prefijo != ""):
                print("categoría, puede y prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_bool_prefix":{
                                "relato":query+" "+prefijo
                            }
                        }],
                        "should":[{
                            "match":{
                                "relato":puede
                            }
                        }
                        ],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if(video == "" and categoria != "" and query!="" and frase == True and puede != "" and prefijo != ""):
                print("categoría, frase, puede y prefijo")
                consulta = {
                    "from":pagina_inicial,
                    "size":PAGINACION_RELATOS,
                    "query":{
                        "bool":{
                            "must":[
                        {
                            "match_phrase_prefix":{
                                "relato":query+" "+prefijo
                            }
                        }],
                        "should":[{
                            "match":{
                                "relato":puede
                            }
                        }
                        ],
                        "filter":{
                            "match":{
                                "titulo_categoria": categoria
                                }
                        }
                    }
                },
                "sort":[
                    {
                    "ultima_fecha":{
                        "order":"desc",
                        "unmapped_type":"date"
                    }
                    }
                 ],
                    "track_total_hits": True
                }
            if consulta is None:
                return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
            print('la consulta es ',consulta)
            respuesta = client.search(
                body=consulta,
                index=index_name
            )
            listarespuesta=[]
            for hit in respuesta["hits"]["hits"]:
                if autor=="":
                        listarespuesta.append({"titulo_categoria":hit["_source"]["titulo_categoria"],
                        "titulo_video":hit["_source"]["titulo_video"],
                        "relato":hit["_source"]["relato"],
                        "id_video":hit["_source"]["id_video"],
                        "ultima_fecha":hit["_source"]["ultima_fecha"],
                        "autor": "anónimo" if hit["_source"]["autor"] == "usuario_generico" else hit["_source"]["autor"],
                        "document_id":hit["_source"]["document_id"],
                        "espodcast":hit["_source"]["espodcast"],
                        "contenedor_aws":hit["_source"]["contenedor_aws"],
                        "total":respuesta["hits"]["total"]["value"],
                        "paginacion":PAGINACION_RELATOS})
                else:
                    if (hit["_source"]["autor"] == "usuario_generico" and autor=="anónimo"):
                            listarespuesta.append({"titulo_categoria":hit["_source"]["titulo_categoria"],
                            "titulo_video":hit["_source"]["titulo_video"],
                            "relato":hit["_source"]["relato"],
                            "id_video":hit["_source"]["id_video"],
                            "ultima_fecha":hit["_source"]["ultima_fecha"],
                            "autor": "anónimo" if hit["_source"]["autor"] == "usuario_generico" else hit["_source"]["autor"],
                            "document_id":hit["_source"]["document_id"],
                            "espodcast":hit["_source"]["espodcast"],
                            "contenedor_aws":hit["_source"]["contenedor_aws"],
                            "total":respuesta["hits"]["total"]["value"],
                            "paginacion":PAGINACION_RELATOS})
                    if (hit["_source"]["autor"] != "usuario_generico" and autor==hit["_source"]["autor"]):
                            listarespuesta.append({"titulo_categoria":hit["_source"]["titulo_categoria"],
                            "titulo_video":hit["_source"]["titulo_video"],
                            "relato":hit["_source"]["relato"],
                            "id_video":hit["_source"]["id_video"],
                            "ultima_fecha":hit["_source"]["ultima_fecha"],
                            "autor": "anónimo" if hit["_source"]["autor"] == "usuario_generico" else hit["_source"]["autor"],
                            "document_id":hit["_source"]["document_id"],
                            "espodcast":hit["_source"]["espodcast"],
                            "contenedor_aws":hit["_source"]["contenedor_aws"],
                            "total":respuesta["hits"]["total"]["value"],
                            "paginacion":PAGINACION_RELATOS})       
            return Response(listarespuesta,status = status.HTTP_200_OK)
        except Exception as err:
            print('error en búsqueda de relatos',err)
            return Response(status = status.HTTP_400_BAD_REQUEST)


class AddFavoritoUsuarioRelato(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def put(self,request):
        relato_found=None
        try:
            relato=request.data["document_id"]
            relato_found=RelatoVideo.objects.get(document_id=relato)
            favorito=FavoritosUsuarioRelato.objects.filter(id_usuario=request.user,id_relato=relato_found)
            if(relato_found is not None):
                serializer=RelatosFavoritosSerializer(data={"id_usuario":request.user.id,"id_relato":relato_found.id})
                if serializer.is_valid():
                    print('serializador de relato favorito válido')
                    if(len(favorito) == 0):
                        FavoritosUsuarioRelato.objects.create(id_usuario=request.user,id_relato=relato_found)
                        return Response(serializer.data,status = status.HTTP_201_CREATED)
                    else:
                        return Response(status = status.HTTP_404_NOT_FOUND)
                else:
                    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(serializer.data,status = status.HTTP_201_CREATED)
        except ObjectDoesNotExist  as err:
            print('error general ',err)
        except Exception  as err:
            print('error general ',err)
        return Response(status = status.HTTP_400_BAD_REQUEST)
    def delete(self,request):
        relato_found=None
        try:
            relato=request.data["document_id"]
            relato_found=RelatoVideo.objects.get(document_id=relato)
            favorito=FavoritosUsuarioRelato.objects.filter(id_usuario=request.user,id_relato=relato_found)
            if len(favorito)>0:
               if(relato_found is not None):
                    serializer=RelatosFavoritosSerializer(data={"id_usuario":request.user.id,"id_relato":relato_found.id})
                    if serializer.is_valid():
                        x = 0
                        for fav in favorito:
                            fav.delete()
                            x+=1
                        return Response(serializer.data,status = status.HTTP_201_CREATED)
                    else:
                        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist  as err:
            print('error general ',err)
        except Exception  as err:
            print('error general ',err)
        return Response(status = status.HTTP_400_BAD_REQUEST)

class FavoritosRelatoSingleUser(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def get(self,request):
        try:
            salida =Video.objects.all().prefetch_related(Prefetch('relatos_por_video',queryset=RelatoVideo.objects.prefetch_related("favoritos_por_relato"))).order_by('titulo')
            relatos = []
            for vid in salida:
                for rel in vid.relatos_por_video.all():
                    for fav in rel.favoritos_por_relato.all():
                        if fav.id_usuario.username == self.request.user.username and not any(x for x in relatos if x.id == vid.id):
                            relatos.append(vid)
            serializer = RelatosMarcadosFavoritosSerializer(relatos, many=True)
            if(len(relatos)> 0):
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"detail":err.message},status=status.HTTP_400_BAD_REQUEST)

class FavoritosRelatoSingle(APIView):
    permission_classes=[permissions.AllowAny]
    def get(self,request,pk):
        try:
            salida=RelatoVideo.objects.all().prefetch_related('favoritos_por_relato')
            relatos = [i for i in salida if i.document_id == pk]
            serializer = RelatosMarcadosDetalleFavoritosSerializer(relatos, many=True)
            if(len(relatos)> 0):
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"detail":err.message},status=status.HTTP_400_BAD_REQUEST)

class FavoritosRelatoListado(generics.ListAPIView):
    permission_classes=[permissions.IsAuthenticated]
    serializer_class=RelatosMarcadosFavoritosSerializer
    pagination_class = StandardResultsSetPagination
    def get_queryset(self):
        videos = Video.objects.all().prefetch_related(Prefetch('relatos_por_video',queryset=RelatoVideo.objects.prefetch_related("favoritos_por_relato")))
        salida = []
        for vid in videos:
            for rel in vid.relatos_por_video.all():
                for fav in rel.favoritos_por_relato.all():
                    print('el favorito es ',fav.id_relato,fav.id_usuario,rel.document_id)
                    if fav.id_usuario == self.request.user and not any(x for x in salida if x.id == vid.id):
                        salida.append(vid)
        return salida

class AddVisitaRelatoView(APIView):
    permission_classes=[permissions.AllowAny]
    queryset=VisitasRelato.objects.all()
    
    def post(self,request):
        visitas_relato = None
        autor = None
        try:
            id_relato = request.data["document_id"]
            autor = User.objects.get(username="usuario_generico")
            if id_relato !='':
                visitas_relato = VisitasRelato.objects.get(id_relato=RelatoVideo.objects.get(document_id=id_relato),id_usuario=autor)
        except ObjectDoesNotExist as not_exist:
            if(visitas_relato is not None):
                visitas_relato.visitas = visitas_relato.visitas+1
                visitas_relato.save()
            elif autor is not None and visitas_relato is None:
                relato=RelatoVideo.objects.get(document_id=id_relato)
                visitas_relato=VisitasRelato.objects.create(id_relato=relato,id_usuario=autor,visitas=1)
                visitas_relato.save()
            else:
                return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
            return Response(status=status.HTTP_201_CREATED)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"detail":err.message},status=status.HTTP_404_NOT_FOUND)
        if visitas_relato is not None:
            visitas_relato.visitas = visitas_relato.visitas+1
            visitas_relato.save()
            return Response(status=status.HTTP_201_CREATED)
        elif autor is not None and visitas_relato is None:
            relato=RelatoVideo.objects.get(document_id=id_relato)
            visitas_relato=VisitasRelato.objects.create(id_relato=relato,id_usuario=autor,visitas=1)
            visitas_relato.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class AddVisitaRelatoViewAuth(APIView):
    permission_classes=[permissions.IsAuthenticated]
    queryset=VisitasRelato.objects.all()
    
    def post(self,request):
        visitas_relato = None
        autor = None
        try:
            id_relato = request.data["document_id"]
            autor = request.user
            if id_relato !='':
                visitas_relato = VisitasRelato.objects.get(id_relato=RelatoVideo.objects.get(document_id=id_relato),id_usuario=autor)
        except ObjectDoesNotExist as not_exist:
            if(visitas_relato is not None):
                visitas_relato.visitas = visitas_relato.visitas+1
                visitas_relato.save()
            elif autor is not None and visitas_relato is None:
                relato=RelatoVideo.objects.get(document_id=id_relato)
                visitas_relato=VisitasRelato.objects.create(id_relato=relato,id_usuario=autor,visitas=1)
                visitas_relato.save()
            else:
                return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
            return Response(status=status.HTTP_201_CREATED)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"detail":err.message},status=status.HTTP_404_NOT_FOUND)
        if visitas_relato is not None:
            visitas_relato.visitas = visitas_relato.visitas+1
            visitas_relato.save()
            return Response(status=status.HTTP_201_CREATED)
        elif autor is not None and visitas_relato is None:
            relato=RelatoVideo.objects.get(document_id=id_relato)
            visitas_relato=VisitasRelato.objects.create(id_relato=relato,id_usuario=autor,visitas=1)
            visitas_relato.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

class VisitasRelatoList(APIView):
    permission_classes=[permissions.AllowAny]
    def ordenarPorTotalVisitas(self,listado):
        maximo = 0
        for i in listado:
            if(i.get("total_visitas") is not None and i.get('total_visitas') > maximo):
                maximo = i.get('total_visitas')
        return maximo
    def get(self,request):
        relatos=Video.objects.all().prefetch_related(Prefetch("relatos_por_video",queryset=RelatoVideo.objects.annotate(total_visitas=Sum('visitas_por_relato__visitas')).prefetch_related(Prefetch('visitas_por_relato',queryset=VisitasRelato.objects.select_related("id_usuario"))).order_by('-total_visitas'))).order_by('titulo')
        
        serializer=RelatoVideoParaVisitasSerializer(relatos,many=True)
        ordenados = sorted(serializer.data,key=lambda x:-self.ordenarPorTotalVisitas(x["relatos_por_video"]))
        return Response(ordenados)

class AddVisitaEventoView(APIView):
    permission_classes=[permissions.AllowAny]
    queryset=VisitasEvento.objects.all()
    
    def post(self,request):
        visitas_evento = None
        autor = None
        try:
            id_evento = int(request.data["identificador"])
            autor = User.objects.get(username="usuario_generico")
            if id_evento !=0:
                evento=EventoAcervo.objects.get(id=id_evento)
                visitas_evento = VisitasEvento.objects.get(id_evento=evento,id_usuario=autor)
        except ObjectDoesNotExist as not_exist:
            if(visitas_evento is not None):
                visitas_evento.visitas = visitas_evento.visitas+1
                visitas_evento.save()
            elif autor is not None and visitas_evento is None:
                evento=EventoAcervo.objects.get(id=id_evento)
                visitas_evento=VisitasEvento.objects.create(id_evento=evento,id_usuario=autor,visitas=1)
                visitas_evento.save()
            else:
                return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
            return Response(status=status.HTTP_201_CREATED)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"detail":err.message},status=status.HTTP_404_NOT_FOUND)
        try:
            if(visitas_evento is not None):
                visitas_evento.visitas = visitas_evento.visitas+1
                visitas_evento.save()
            elif autor is not None and visitas_evento is None:
                evento=EventoAcervo.objects.get(id=id_evento)
                visitas_evento=VisitasEvento.objects.create(id_evento=evento,id_usuario=autor,visitas=1)
                visitas_evento.save()
            return Response(status=status.HTTP_201_CREATED)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"detail":err.message},status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class AddVisitaEventoViewAuth(APIView):
    permission_classes=[permissions.IsAuthenticated]
    queryset=VisitasEvento.objects.all()
    
    def post(self,request):
        visitas_evento = None
        autor = None
        try:
            id_evento = int(request.data["identificador"])
            autor = request.user
            if id_evento !=0:
                evento=EventoAcervo.objects.get(id=id_evento)
                visitas_evento = VisitasEvento.objects.get(id_evento=evento,id_usuario=autor)
        except ObjectDoesNotExist as not_exist:
            if(visitas_evento is not None):
                visitas_evento.visitas = visitas_evento.visitas+1
                visitas_evento.save()
            elif autor is not None and visitas_evento is None:
                evento=EventoAcervo.objects.get(id=id_evento)
                visitas_evento=VisitasEvento.objects.create(id_evento=evento,id_usuario=autor,visitas=1)
                visitas_evento.save()
            else:
                return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
            return Response(status=status.HTTP_201_CREATED)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"detail":err.message},status=status.HTTP_404_NOT_FOUND)
        try:
            if(visitas_evento is not None):
                visitas_evento.visitas = visitas_evento.visitas+1
                visitas_evento.save()
            elif autor is not None and visitas_evento is None:
                evento=EventoAcervo.objects.get(id=id_evento)
                visitas_evento=VisitasEvento.objects.create(id_evento=evento,id_usuario=autor,visitas=1)
                visitas_evento.save()
            return Response(status=status.HTTP_201_CREATED)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"detail":err.message},status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

class VisitasEventoList(APIView):
    permission_classes=[permissions.AllowAny]
    def ordenarPorTotalVisitas(self,listado):
        maximo = 0
        for i in listado:
            if(i.get("visitas") is not None and i.get('visitas') > maximo):
                maximo = i.get('visitas')
        return maximo
    def get(self,request):
        visitas=EventoAcervo.objects.all().prefetch_related(Prefetch("visitas_por_evento",queryset=VisitasEvento.objects.all().select_related("id_usuario").order_by('-visitas'))).annotate(total_de_visitas=Sum('visitas_por_evento__visitas')).order_by('-total_de_visitas')
        serializer=EventoParaVisitasSerializer(visitas,many=True)
        ordenados = sorted(serializer.data,key=lambda x:-self.ordenarPorTotalVisitas(x["visitas_por_evento"]))
        return Response(ordenados)

class VistasEventosProximosList(APIView):
    permission_classes=[permissions.AllowAny]
    def get(self,request):
        fecha_actual=datetime.datetime.now(pytz.timezone('America/Mexico_City'))
        visitas=EventoAcervo.objects.filter(fechainicio__gte=fecha_actual).order_by('titulo')
        serializer=EventoParaVisitasSerializer(visitas,many=True)
        return Response(serializer.data)

class AddCalificacionVideoView(APIView):
    permission_classes=[permissions.AllowAny]
    queryset=VisitasEvento.objects.all()
    
    def post(self,request):
        calificacion_video = None
        autor = None
        video = None
        calificacion = None
        try:
            id_video = int(request.data["id_video"])
            calificacion = int(request.data["calificacion"])
            autor = User.objects.get(username="usuario_generico")
            if id_video !=0:
                video=Video.objects.get(id=id_video)
        except ObjectDoesNotExist as not_exist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"detail":err.message},status=status.HTTP_404_NOT_FOUND)
        try:
            if autor is not None and video is not None:
                calificacion_video=CalificacionVideo.objects.create(id_video=video,id_usuario=autor,calificacion=calificacion)
                calificacion_video.save()
                return Response(status=status.HTTP_201_CREATED)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"detail":err.message},status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

class AddCalificacionVideoAuthView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    queryset=VisitasEvento.objects.all()
    
    def post(self,request):
        calificacion_video = None
        autor = request.user
        video = None
        calificacion = None
        try:
            id_video = int(request.data["id_video"])
            calificacion = int(request.data["calificacion"])
            if id_video !=0:
                video=Video.objects.get(id=id_video)
                calificacion_video=CalificacionVideo.objects.get(id_video=video,id_usuario=autor)
        except ObjectDoesNotExist as not_exist:
            if autor is not None and video is not None and calificacion_video is None:
                calificacion_video=CalificacionVideo.objects.create(id_video=video,id_usuario=autor,calificacion=calificacion)
                calificacion_video.save()
                return Response(status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"detail":err.message},status=status.HTTP_404_NOT_FOUND)
        try:
            if autor is not None and video is not None and calificacion_video is not None:
                calificacion_video.calificacion=calificacion
                calificacion_video.save()
                return Response(status=status.HTTP_201_CREATED)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as err:
            if not hasattr(err,'message'):
                return Response({"detail":str(err)},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"detail":err.message},status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

class CalificacionVideoList(APIView):
    permission_classes=[permissions.AllowAny]
    def ordenarPorTotalCalificaciones(self,listado):
        maximo = 0
        for i in listado:
            if(i.get("visitas") is not None and i.get('visitas') > maximo):
                maximo = i.get('visitas')
        return maximo
    def get(self,request):
        calificaciones=Video.objects.all().prefetch_related(Prefetch("video_calificacion",queryset=CalificacionVideo.objects.all().select_related("id_usuario").order_by('-calificacion'))).annotate(total_calificacion=Avg('video_calificacion__calificacion')).order_by('-total_calificacion')
        serializer=CalfificacionVideoParaListado(calificaciones,many=True)
        #ordenados = sorted(serializer.data,key=lambda x:-self.ordenarPorTotalVisitas(x["visitas_por_evento"]))
        return Response(serializer.data)

class CalificacionVideoSingle(APIView):
    permission_classes=[permissions.AllowAny]
    def get(self,request,pk):
        calificaciones=Video.objects.filter(id=pk).prefetch_related(Prefetch("video_calificacion",queryset=CalificacionVideo.objects.all().select_related("id_usuario").order_by('-calificacion'))).annotate(total_calificacion=Avg('video_calificacion__calificacion')).order_by('-total_calificacion')
        serializer=CalfificacionVideoParaListado(calificaciones,many=True)
        return Response(serializer.data)

class CalificacionVideoByUser(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def get(self,request,pk):
        usuario=request.user.id
        video=Video.objects.get(id=pk)
        calificacion=Video.objects.filter(id=pk).prefetch_related(Prefetch("video_calificacion",queryset=CalificacionVideo.objects.filter(id_usuario=usuario).select_related("id_usuario")))
        serializer=CalfificacionVideoParaListado(calificacion,many=True)
        return Response(serializer.data)

   


        



