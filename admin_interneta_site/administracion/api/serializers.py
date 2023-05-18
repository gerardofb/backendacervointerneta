from rest_framework import serializers
from ..models import Categorias, Video, CreditosVideo, ComentariosVideo,RelatoVideo
from ..models import VerificacionRegistroUsuario, FavoritosUsuarioVideo
from ..models import VisitasVideo,EventoAcervo,FavoritosUsuarioRelato
from ..models import EventoAcervo,VisitasEvento,CalificacionVideo
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from ..utilerias import EmailerDefault
import uuid, datetime, pytz

class LoginSerializer(serializers.Serializer):
    email=serializers.CharField(max_length=255, required=True)
    password=serializers.CharField(required=True)
    def validate(self,data):
        username=data.get('email')
        password=data.get('password')
        if(username and password):
            print('campos llenos en el login')
            user=authenticate(request=self.context.get('request'),username=username,password=password)
            if not user:
                raise serializers.ValidationError({"credenciales":"usuario o contraseña inválido"})
            data["usuario"]=user
            return data
        else:
            raise serializers.ValidationError({"campos_faltantes":"el usuario y la contraseña son obligatorios"})
           

class UsuariosSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['username','first_name','last_name','email']

class CambiarPasswordSerializer(serializers.Serializer):
    password=serializers.CharField(write_only=True,required=True,validators=[validate_password])
    password2=serializers.CharField(write_only=True,required=True)
    guid=serializers.CharField(write_only=True,required=True,max_length=32)
    def validate(self,attrs):
        if(attrs['password']!=attrs['password2']):
            raise serializers.ValidationError({'contraseña':'Las contraseñas no coinciden'})
        return attrs

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    creado = serializers.BooleanField(required=False)
    password=serializers.CharField(write_only=True,required=True,validators=[validate_password])
    password2=serializers.CharField(write_only=True,required=True)
    class Meta:
        model=User
        fields=['username','first_name','last_name','email','password','password2','creado']
        extra_kwargs={
            'first_name':{'required':True},
            'last_name':{'required':True}
        }
    def validate(self,attrs):
        if(attrs['password']!=attrs['password2']):
            raise serializers.ValidationError({'password':'Las contraseñas no coinciden'})
        if(attrs["first_name"]=="" or attrs["last_name"]==""):
            raise serializers.ValidationError({"first_name":"Los campos nombre o apellidos no pueden estar en blanco"})
        attrs.creado = True
        return attrs

    def create(self,validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_active=True
        )
        user.set_password(validated_data['password'])
        user.save()
        guid = uuid.uuid4().hex
        verificacion = VerificacionRegistroUsuario.objects.create(id_usuario=User.objects.get(username=validated_data["username"]),
        link=guid)
        verificacion.save()
        verificacion_update = VerificacionRegistroUsuario.objects.get(link=guid)
        fecha_nueva = verificacion_update.insert_time + datetime.timedelta(days=1)
        verificacion_update.vigencia_time=fecha_nueva
        verificacion_update.save()
        sender = EmailerDefault()
        sender.send_email_register(user.email,guid)
        return user

    
class CreditosVideoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=CreditosVideo
        fields=["id_video","codigo_identificacion", "anio_produccion","contenedor_fotograma_aws",
        "sinopsis","direccion_realizacion","asistentes_realizacion","guion","camara","foto_fija",
        "color","duracion_mins","reparto","testimonios","idioma","musica","performance","edicion",
        "produccion_ejecutiva","produccion"]
class VideosFavoritosSerializer(serializers.ModelSerializer):
    id_usuario=UsuariosSerializer(read_only=True)
    class Meta:
        model=FavoritosUsuarioVideo
        fields=["id_usuario","id_video"]
    def create(self,validated_data):
        favorito=VideosFavoritosSerializer.objects.create(**validated_data)
        return favorito

class RelatoFavoritosVideoSerializer(serializers.ModelSerializer):
    espodcast = serializers.BooleanField(default=False)
    contenedor_aws = serializers.CharField(max_length=4000,required=False)
    relato=serializers.CharField(max_length=6000,required=False)
    id_autor=UsuariosSerializer(read_only=True)
    class Meta:
        model = RelatoVideo
        fields = ["id_autor","id_video","insert_time","update_time","document_id","visitas","relato","espodcast","id_autor","contenedor_aws"]

class VideosMarcadosFavoritosSerializer(serializers.ModelSerializer):
    favoritos_por_video = VideosFavoritosSerializer(many=True,read_only=True)
    relatos_por_video = None#RelatoFavoritosVideoSerializer(many=True,read_only=True)
    class Meta:
        model=Video
        fields = ["id","titulo","contenedor_aws","contenedor_img","id_categoria","visitas","favoritos_por_video","relatos_por_video","activo"]
class VisitasDeVideoSerializer(serializers.ModelSerializer):
    id_usuario=UsuariosSerializer(read_only=True)
    class Meta:
        model=VisitasVideo
        fields=["id_video","visitas","id_usuario"]
class VideoSerializer(serializers.ModelSerializer):
    creditos_por_video = CreditosVideoSerializer(many=True,read_only=True)
    favoritos_por_video = VideosFavoritosSerializer(many=True,read_only=True)
    visitas_por_video=VisitasDeVideoSerializer(many=True,read_only=True)
    total_visitas=serializers.IntegerField(required=False)
    total_favoritos=serializers.IntegerField(required=False)
    total_comentarios=serializers.IntegerField(required=False)
    class Meta:
        model=Video
        fields = ["id","titulo","contenedor_aws","contenedor_img","id_categoria","visitas","total_visitas","creditos_por_video","favoritos_por_video","visitas_por_video","total_favoritos","total_comentarios","activo"]
class VideoShortSerializer(serializers.ModelSerializer):
    class Meta:
        model=Video
        fields = ["id","titulo","contenedor_aws","contenedor_img","id_categoria","visitas"]
class CategoriasSerializer(serializers.ModelSerializer):
    videos_por_categoria = VideoSerializer(many=True,read_only=True)
    class Meta:
        model=Categorias
        fields=["id","titulo","descripcion","contenedor_img","no_videos","videos_por_categoria"]

class IndexedComentariosVideoSerializer(serializers.Serializer):
    titulo_categoria=serializers.CharField(max_length=500)
    titulo_video=serializers.CharField(max_length=500)
    comentario=serializers.CharField(max_length=2000)

class ComentariosVideoSerializer(serializers.ModelSerializer):
    indexed_fields=IndexedComentariosVideoSerializer()
    class Meta:
        model=ComentariosVideo
        fields = ["id_autor","id_video","insert_time","update_time","document_id","indexed_fields"]
        read_only_fields=["indexed_fields"]
    def create(self, validated_data):
        index_data = validated_data.pop('indexed_fields')
        comentario = ComentariosVideo.objects.create(**validated_data)
        return comentario

class IndexedAnswerComentariosSerializer(serializers.Serializer):
    comentario=serializers.CharField(max_length=2000)

class AnswerComentariosSerializer(serializers.Serializer):
    indexed_fields=IndexedAnswerComentariosSerializer()
    class Meta:
        model=ComentariosVideo
        fields = ["id_autor","insert_time","update_time","document_id","parent_document_id","indexed_fields"]
        read_only_fields=["indexed_fields"]
    def create(self, validated_data):
        index_data = validated_data.pop('indexed_fields')
        comentario = ComentariosVideo.objects.create(**validated_data)
        return comentario
class ComentariosVideoResponseSerializer(serializers.Serializer):
    titulo_categoria = serializers.CharField(max_length=500)
    titulo_video = serializers.CharField(max_length=500)
    comentario = serializers.CharField(max_length=2000)
    id_video = serializers.IntegerField()
    ultima_fecha = serializers.DateTimeField()
    autor = serializers.CharField(max_length=150)
    paginacion = serializers.IntegerField()
    total = serializers.IntegerField()

class IndexedRelatosVideoSerializer(serializers.Serializer):
    titulo_categoria=serializers.CharField(max_length=500,required=False)
    titulo_video=serializers.CharField(max_length=500,required=False)
    titulo_relato = serializers.CharField(max_length=255,required=False)
    
class RelatoVideoSerializer(serializers.ModelSerializer):
    indexed_fields = IndexedRelatosVideoSerializer(required=False)
    espodcast = serializers.BooleanField(default=False)
    contenedor_aws = serializers.CharField(max_length=4000,required=False)
    filefield=serializers.FileField(required=False, allow_null=True)
    relato=serializers.CharField(max_length=6000,required=False)
    total_visitas=serializers.IntegerField(required=False)
    class Meta:
        model = RelatoVideo
        fields = ["id","id_autor","id_video","insert_time","update_time","document_id","visitas","indexed_fields","relato","espodcast","contenedor_aws","filefield","total_visitas"]
        read_only_fields=["indexed_fields"]
    def create(self, validated_data):
        index_data = validated_data.pop('indexed_fields')
        print('voy a crear el serializador del relato')
        comentario = RelatoVideoSerializer.objects.create(**validated_data)
#         return comentario

class RelatosVideoResponseSerializer(serializers.Serializer):
    titulo_categoria = serializers.CharField(max_length=500)
    titulo_video = serializers.CharField(max_length=500)
    relato = serializers.CharField(max_length=8000)
    id_video = serializers.IntegerField()
    ultima_fecha = serializers.DateTimeField()
    autor = serializers.CharField(max_length=150)
    paginacion = serializers.IntegerField()
    total = serializers.IntegerField()

class VideosFavoritosSerializer(serializers.ModelSerializer):
    class Meta:
        model=FavoritosUsuarioVideo
        fields=["id_usuario","id_video"]
    def create(self,validated_data):
        favorito=VideosFavoritosSerializer.objects.create(**validated_data)
        return favorito

class EventosAcervoSerializer(serializers.ModelSerializer):
    filefield=serializers.FileField(required=False, allow_null=True)
    class Meta:
        model=EventoAcervo
        fields=["titulo","descripcion","duracion","fechainicio","fechafin","contenedor_img","filefield"]

class EventosResponseSerializer(serializers.ModelSerializer):
    filefield=serializers.FileField(required=False, allow_null=True)
    id_usuario=UsuariosSerializer()
    class Meta:
        model=EventoAcervo
        fields=["id","id_usuario","titulo","descripcion","duracion","fechainicio","fechafin","contenedor_img","filefield"]


class RelatoyVideoFavoritoSerializer(serializers.ModelSerializer):
    id_autor=UsuariosSerializer()
    id_relato=RelatoVideoSerializer()
    class Meta:
        model = RelatoVideo
        fields = ["id_autor","id_relato"]
    def create(self, validated_data):
        relato = RelatoyVideoFavoritoSerializer.objects.create(**validated_data)
        return relato

class RelatosFavoritosSerializer(serializers.ModelSerializer):
    class Meta:
        model=FavoritosUsuarioRelato
        fields=["id_usuario","id_relato"]
    def create(self,validated_data):
        favorito=RelatosFavoritosSerializer.objects.create(**validated_data)
        return favorito

class RelatosFavoritosRespuestaSerializer(serializers.ModelSerializer):
    id_usuario=UsuariosSerializer()
    class Meta:
        model=FavoritosUsuarioRelato
        fields=["id_usuario","id_relato"]
    def create(self,validated_data):
        favorito=RelatosFavoritosRespuestaSerializer.objects.create(**validated_data)
        return favorito

class RelatoVideoParaFavoritosSerializer(serializers.ModelSerializer):
    id_autor=UsuariosSerializer()
    favoritos_por_relato=RelatosFavoritosRespuestaSerializer(many=True)
    total_visitas=serializers.IntegerField(required=False)
    class Meta:
        model = RelatoVideo
        fields = ["id_autor","id","insert_time","update_time","document_id","visitas","favoritos_por_relato","total_visitas"]
    def create(self, validated_data):
        comentario = RelatoVideoParaFavoritosSerializer.objects.create(**validated_data)
        return comentario

class RelatosMarcadosFavoritosSerializer(serializers.ModelSerializer):
    favoritos_por_relato=RelatosFavoritosSerializer(many=True,read_only=True)
    relatos_por_video=RelatoVideoParaFavoritosSerializer(many=True,read_only=True)
    class Meta:
        model=Video
        fields = ["id","favoritos_por_relato","relatos_por_video","titulo","id_categoria","contenedor_img"]

class RelatosMarcadosDetalleFavoritosSerializer(serializers.ModelSerializer):
    favoritos_por_relato=RelatosFavoritosSerializer(many=True,read_only=True)
    id_autor=UsuariosSerializer()
    
    class Meta:
        model = RelatoVideo
        fields = ["id_autor","id","insert_time","update_time","document_id","visitas","favoritos_por_relato"]

class RelatoVideoParaVisitasSerializer(serializers.ModelSerializer):
    relatos_por_video=RelatoVideoParaFavoritosSerializer(many=True,read_only=True)
    class Meta:
        model = Video
        fields = ["id","titulo","id_categoria","relatos_por_video"]
    def create(self, validated_data):
        relato = RelatoVideoParaVisitasSerializer.objects.create(**validated_data)
        return relato

class EventoVisitaDetalleSerializer(serializers.ModelSerializer):
    id_usuario=UsuariosSerializer()
    class Meta:
        model = VisitasEvento
        fields = ["id_usuario","visitas"]
    def create(self, validated_data):
        visita = EventoVisitaDetalleSerializer.objects.create(**validated_data)
        return visita
class EventoParaVisitasSerializer(serializers.ModelSerializer):
    visitas_por_evento=EventoVisitaDetalleSerializer(many=True,read_only=True)
    total_de_visitas=serializers.IntegerField(required=False)
    class Meta:
        model = EventoAcervo
        fields = ["id","titulo","descripcion","visitas_por_evento","duracion","fechainicio","fechafin","total_de_visitas","contenedor_img"]
    def create(self, validated_data):
        evento = EventoParaVisitasSerializer.objects.create(**validated_data)
        return evento

class CalificacionVideoSerializer(serializers.ModelSerializer):
    id_usuario=UsuariosSerializer()
    class Meta:
        model=CalificacionVideo
        fields=["id","id_video","id_usuario","calificacion"]

class CalfificacionVideoParaListado(serializers.ModelSerializer):
    video_calificacion=CalificacionVideoSerializer(many=True)
    total_calificacion=serializers.FloatField(default=0)
    class Meta:
        model=Video
        fields = ["id","titulo","id_categoria","contenedor_aws","contenedor_img","video_calificacion","total_calificacion"]