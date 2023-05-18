from celery import shared_task
from .utilerias import UploaderDefault
import logging
from .models import Video
from django.core.files.storage import FileSystemStorage


logger = logging.getLogger(__name__)

@shared_task
def upload_to_bucket_task(bucket,key,file, cleaned_file):
    uploader = UploaderDefault()
    fss = FileSystemStorage()
    logger.warning('invocación de tarea asíncrona upload_to_bucket_task')
    respuesta = uploader.upload(bucket, key,file)
    fss.delete(cleaned_file)
    logger.warning('fin de tarea asíncrona upload_to_bucket_task')

@shared_task
def upload_to_bucket_task_save(bucket,key,file, cleaned_file, id_modelo, url_prefirmado):
    uploader = UploaderDefault()
    fss = FileSystemStorage()
    logger.warning('invocación de tarea asíncrona upload_to_bucket_task')
    respuesta = uploader.upload(bucket, key,file)
    fss.delete(cleaned_file)
    if(id_modelo):
        video = Video.objects.get(id=id_modelo)
        video.contenedor_aws = url_prefirmado
        video.save()
    logger.warning('fin de tarea asíncrona upload_to_bucket_task')
