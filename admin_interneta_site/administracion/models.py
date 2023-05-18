from email.policy import default
from enum import unique
from hashlib import blake2b
from django.db import models
from s3direct.fields import S3DirectField
from django.conf import settings
from django.contrib.auth.models import User


# Create your models here.
class Categorias(models.Model):
    titulo = models.CharField(max_length=500)
    descripcion = models.TextField()
    contenedor_img = models.CharField(max_length=2500, null=True,blank=True)
    no_videos = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    class Meta:
        indexes = [
            models.Index(fields=['titulo'], name='idx_categoria_titulo')
        ]
    def __str__(self):
        return self.titulo        


class Video(models.Model):
    titulo = models.CharField(max_length= 500,unique=True)
    contenedor_aws = models.CharField(max_length=4000,null=True,blank=True)
    contenedor_img = models.CharField(max_length=2500, null=True,blank=True)
    id_categoria = models.ForeignKey(Categorias, related_name="videos_por_categoria", on_delete = models.CASCADE)
    visitas = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    class Meta:
        indexes = [
            models.Index(fields=['titulo'], name='idx_video_titulo')
        ]

        

class ColeccionesVideos(models.Model):
    coleccion = models.CharField(max_length = 500)

class GenerosVideos(models.Model):
    descripcion = models.CharField(max_length = 500)

class EnlaceExternoVideo(models.Model):
    enlace = models.TextField(max_length=2500)

class EstadosRepublica(models.Model):
    estado = models.CharField(max_length=255)

class CalidadVideo(models.Model):
    titulo_calidad = models.CharField(max_length=255)
    formato_estandarizado = models.CharField(max_length=255)
    dimensiones = models.CharField(max_length=255)
    resolucion = models.CharField(max_length=255)
    codec_video = models.CharField(max_length= 255, null=True)
    codec_audio = models.CharField(max_length = 255, null=True)
    resolucion_max = models.CharField(max_length = 255, null=True)
    calidad_constante = models.PositiveSmallIntegerField(null=True)
    fps = models.PositiveSmallIntegerField(null=True)
    bit_rate_audio = models.PositiveIntegerField(null=True)
    mix_audio = models.CharField(max_length=255,null=True)
    id_video = models.ForeignKey(Video, on_delete=models.CASCADE)
    class Meta:
        indexes =[
            models.Index(fields=['titulo_calidad'], name='idx_calidadvideo_titulo'),
            models.Index(fields=['dimensiones'], name='idx_calidadvideo_dimensiones'),
            models.Index(fields=['resolucion'],name='idx_calidadvideo_resolucion')
        ]

class CreditosVideo(models.Model):
    id_video = models.ForeignKey(Video, on_delete=models.CASCADE,related_name="creditos_por_video",null=True)
    codigo_identificacion = models.CharField(max_length=255)
    anio_produccion = models.PositiveSmallIntegerField(null=True)
    contenedor_fotograma_aws = models.CharField(max_length=255,null=True)
    sinopsis = models.CharField(max_length=4000)
    direccion_realizacion = models.CharField(max_length=255)
    asistentes_realizacion = models.CharField(max_length = 500, null=True)
    guion = models.CharField(max_length = 500)
    camara = models.CharField(max_length = 500, null=True)
    foto_fija = models.CharField(max_length = 500, null = True)
    color = models.BooleanField()
    duracion_mins = models.PositiveSmallIntegerField()
    reparto = models.CharField(max_length = 1000, null= True)
    testimonios = models.CharField(max_length=4000,null = True)
    idioma = models.CharField(max_length = 255, null=True)
    musica = models.CharField(max_length = 500, null = True)
    performance = models.CharField(max_length= 500, null =True)
    edicion = models.CharField(max_length =500)
    produccion_ejecutiva = models.CharField(max_length = 500)
    produccion = models.CharField(max_length = 500, null = True)
    pais = models.CharField(max_length = 100, null = True)
    class Meta:
        indexes = [
            models.Index(fields=['codigo_identificacion'], name='idx_codigo_ident_creditos'),
            models.Index(fields=['direccion_realizacion'],name="idx_direccion_creditos"),
            models.Index(fields=['guion'],name="idx_guion_creditos"),
            models.Index(fields=['camara'],name="idx_camara_creditos"),
            models.Index(fields=['musica'],name="idx_musica_creditos"),
            models.Index(fields=['edicion'],name='idx_edicion_creditos'),
            models.Index(fields=['produccion_ejecutiva'],name="idx_produccion_ej_creditos"),
        ]

class CreditosAdicionalesVideo(models.Model):
    idVideo = models.ForeignKey(Video, on_delete=models.CASCADE)
    distribuidor = models.CharField(max_length = 500, null = True)
    id_coleccion = models.ForeignKey(ColeccionesVideos, null=True, on_delete=models.SET_NULL)
    id_genero = models.ForeignKey(GenerosVideos, null = True, on_delete = models.SET_NULL)
    id_enlace_externo = models.ForeignKey(EnlaceExternoVideo, null = True, on_delete = models.SET_NULL)
    id_estado_republica = models.ForeignKey(EstadosRepublica, null = True, on_delete = models.SET_NULL)
    locaciones = models.CharField(max_length=4000,null=True)
    coproduccion = models.CharField(max_length = 500, null = True)
    formato_master = models.CharField(max_length = 500, null = True)
    formato_videograbacion = models.CharField(max_length = 255, null = True)
    formatos_disponibles = models.CharField(max_length = 255, null = True)
    estado_conservacion = models.CharField(max_length = 255, null = True)
    tema = models.CharField(max_length=4000,null = True)
    areas_contexto = models.CharField(max_length=4000,null = True)
    class Meta:
        indexes=[
            models.Index(fields=['formatos_disponibles'],name='idx_formatos_creditos'),
        ]

class ComentariosVideo(models.Model):
    id_autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True,null=True)
    id_video = models.ForeignKey(Video, on_delete=models.CASCADE,related_name="comentarios_por_video")
    insert_time = models.DateTimeField(auto_now_add=True,blank=True)
    update_time = models.DateTimeField(null=True)
    document_id = models.CharField(max_length=128)
    parent_document_id = models.CharField(max_length=128,null=True,blank=True)
    activo = models.BooleanField(default=True)
    class Meta:
        indexes=[
            models.Index(fields=['id_video','document_id'],name='idx_video_comentarios')
        ]
class RelatoVideo(models.Model):
    id_autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True,null=True)
    id_video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="relatos_por_video")
    insert_time = models.DateTimeField(auto_now_add=True,blank=True)
    update_time = models.DateTimeField(null=True)
    document_id = models.CharField(max_length=128,default='',unique=True)
    visitas = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    class Meta:
        indexes=[
            models.Index(fields=['id_video','document_id'],name='idx_relato_comentarios')
        ]

class VerificacionRegistroUsuario(models.Model):
    id_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    link = models.CharField(max_length=32,unique=True)
    insert_time = models.DateTimeField(auto_now_add=True)
    vigencia_time = models.DateTimeField(blank=True,null=True)
    utilizado = models.BooleanField(default=False)
    is_reset = models.BooleanField(default=False)
    class Meta:
        indexes=[
            models.Index(fields=["id_usuario"],name="idx_verifica_registro_usuario"),
        ]

class FavoritosUsuarioVideo(models.Model):
    id_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    id_video = models.ForeignKey(Video, on_delete=models.CASCADE,related_name="favoritos_por_video")
    class Meta:
        indexes=[
            models.Index(fields=["id_usuario","id_video"],name="idx_favoritos_video_usuario")
        ]
class FavoritosUsuarioRelato(models.Model):
    id_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name="usuario_por_favorito_relato")
    id_relato = models.ForeignKey(RelatoVideo,on_delete=models.CASCADE,related_name="favoritos_por_relato")
    class Meta:
        indexes=[
            models.Index(fields=["id_usuario","id_relato"],name="idx_favoritos_relato_usuario")
        ]

class ListaReproduccionUsuario(models.Model):
    id_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=255)
    no_videos = models.PositiveIntegerField(default=0)
    class Meta:
        indexes=[
            models.Index(fields=["id_usuario"],name="idx_lista_reprod_usuario")
        ]

class ListaReproduccionUsuarioVideos(models.Model):
    id_lista_reprod=models.ForeignKey(ListaReproduccionUsuario,on_delete=models.CASCADE)
    id_video=models.ForeignKey(Video,on_delete=models.CASCADE)
    class Meta:
        indexes=[
            models.Index(fields=["id_lista_reprod"],name="idx_lista_reprod_video")
        ]
class VisitasVideo(models.Model):
    id_usuario=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,blank=True,null=True,related_name="usuario_por_visita")
    id_video=models.ForeignKey(Video,on_delete=models.CASCADE,related_name="visitas_por_video")
    visitas=models.PositiveIntegerField(default=0)
    class Meta:
        indexes=[
            models.Index(fields=["id_usuario","id_video"],name="idx_visitas_usuario_video")
        ]
class VisitasRelato(models.Model):
    id_usuario=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,blank=True,null=True,related_name="usuario_por_vista_relato")
    id_relato=models.ForeignKey(RelatoVideo,on_delete=models.CASCADE,related_name="visitas_por_relato")
    visitas=models.PositiveIntegerField(default=0)
    class Meta:
        indexes=[
            models.Index(fields=["id_usuario","id_relato"],name="idx_visitas_relato")
        ]

class EventoAcervo(models.Model):
    id_usuario = id_usuario=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="usuario_evento")
    descripcion = models.CharField(max_length=4000)
    titulo = models.CharField(max_length=500)
    duracion = models.PositiveIntegerField(default=0)
    fechainicio = models.DateTimeField()
    fechafin = models.DateTimeField()
    contenedor_img = models.CharField(max_length=2500, null=True,blank=True)
    class Meta:
        indexes=[
            models.Index(fields=["id_usuario"],name="idx_eventos_acervo_usuario"),
            models.Index(fields=["titulo"],name="idx_eventos_acervo_titulo"),
            models.Index(fields=["fechainicio","fechafin"],name="idx_eventos_acervo_fechas")
        ]

class VisitasEvento(models.Model):
    id_usuario=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,blank=True,null=True,related_name="usuario_por_visitas_evento")
    id_evento=models.ForeignKey(EventoAcervo,on_delete=models.CASCADE,related_name="visitas_por_evento")
    visitas=models.PositiveIntegerField(default=0)
    class Meta:
        indexes=[
            models.Index(fields=["id_usuario","id_evento"],name="idx_visitas_evento")
        ]

class CalificacionVideo(models.Model):
    id_video=models.ForeignKey(Video,on_delete=models.CASCADE, related_name="video_calificacion")
    id_usuario=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE, related_name="usuario_calificacion_video")
    calificacion=models.PositiveIntegerField(default=0)
    class Meta:
        indexes=[
            models.Index(fields=["id_video","id_usuario"],name="idx_calificacion_video")
        ]



        




