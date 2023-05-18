import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import os
from .models import Categorias, Video, CreditosVideo
class UploaderDefault:
    def __init__(self):
        self.total = 0
        self.uploaded = 0
        self.s3 = boto3.client('s3',
                    region_name=settings.AWS_S3_REGION_NAME,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                    )

    def upload_callback(self, size):
        if self.total == 0:
            return
        self.uploaded += size
        print("{} %".format(int(self.uploaded / self.total * 100)))

    def upload(self, bucket, key, file):
        self.total = os.stat(file).st_size      
        print('la ruta del archivo es ',file)
        self.s3.upload_file(file, bucket, key,Callback=self.upload_callback)

    def generate_url(self,bucket, key):
        url = self.s3.generate_presigned_url(ClientMethod = 'put_object',
                                      Params = { 'Bucket': bucket, 'Key': key })
        return url

class EmailerDefault:
    def __init__(self):
        self.sender = 'no-reply@acervo-audiovisual-interneta.org' #'acervoaudiovisualinterneta@gmail.com'
        self.ses = boto3.client('ses',
                    region_name=settings.AWS_S3_REGION_NAME,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                    )
    def send_email_register(self,recipient,link):
        usuariosindominio = recipient.split('@')[0]
        SUBJECT = "Valide su registro en el Acervo AudioVisual Interneta"
        BODY_HTML = """<html>
        <head></head>
        <body style="margin:0 1em">
        <img src="http://52.53.166.12:5000/static/img/logo_nuevo_negro.png" alt="logotipo acervo audiovisual interneta" />
        <br />
        <h1>"""+SUBJECT+"""</h1>
        <p>Por favor no responda a este correo</p>
        <p>Recibimos una solicitud de registro. Para verificar su correo electrónico, puede hacer click en el siguiente link:<p>
        <p>
        <a href=http://acervo-audiovisual-interneta.org/VerificaRegistro?vinculo="""+link+"""&usuario="""+usuariosindominio+""">Verificar mi correo electrónico</a>
        </p>
        <p>El vínculo tiene una vigencia de 24 horas</p><p>¡Saludos desde el equipo del Acervo Audiovisual Interneta!</body></html>"""
        CHARSET = "UTF-8"
        try:
            response = self.ses.send_email(
            Destination = {"ToAddresses":[
                recipient
            ]},
        Message={
            "Body":{
                "Html":{
                    "Charset":CHARSET,
                    "Data":BODY_HTML
                },
                "Text":{
                    "Charset":CHARSET,
                    "Data":""
                }
            },
            "Subject":{
                "Charset":CHARSET,
                "Data":SUBJECT
            }
        },
        Source=self.sender)
        except ClientError as e:
            print("error generando el correo de verificación ",e)
        else:
            print("correo enviado con ID de Mensaje: ",response["MessageId"])
        


