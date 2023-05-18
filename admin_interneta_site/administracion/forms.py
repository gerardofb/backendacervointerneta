from django import forms
from django.forms import ModelForm
from . import models

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'value':''}))
    password = forms.CharField(widget=forms.PasswordInput)

class CategoriasForm(ModelForm):
    img_file=forms.FileField(label="Agregue una imagen descriptiva")
    def __init__(self, *args, **kwargs):
        super(CategoriasForm, self).__init__(*args, **kwargs)
    class Meta:
        model=models.Categorias
        fields=['titulo','descripcion','no_videos']
        labels={
            'titulo':'Título',
            'descripcion':'Descripción'
        }
        widgets={'no_videos':forms.HiddenInput()}
    def save(self, commit=True):
        return super(CategoriasForm, self).save(commit=commit)

class VideosForm(ModelForm):
    aws_file = forms.FileField(label="Agregue un video")
    img_file = forms.FileField(label="Agregue una imagen de foto fija")
    def __init__(self, *args, **kwargs):
        super(VideosForm, self).__init__(*args, **kwargs)
        self.fields['id_categoria'].empty_label = 'Seleccione una opción...'
    class Meta:
        model=models.Video
        fields=['titulo','id_categoria']
        labels={
            'titulo': 'Título',
            'id_categoria':'Seleccionar categoría',
        }
    def save(self, commit=True):
        return super(VideosForm, self).save(commit=commit)

# class VideosFormSinTitulo(ModelForm):
#     aws_file = forms.FileField(label="Agregue un video")
#     img_file = forms.FileField(label="Agregue una imagen de foto fija")
#     def __init__(self, *args, **kwargs):
#         super(VideosForm, self).__init__(*args, **kwargs)
#         self.fields['id_categoria'].empty_label = 'Seleccione una opción...'
#     class Meta:
#         model=models.Video
#         fields=['titulo','id_categoria']
#         labels={
#             'titulo': 'Título',
#             'id_categoria':'Seleccionar categoría',
#         }
#     def save(self, commit=True):
#         return super(VideosForm, self).save(commit=commit)

class CreditosVideoForm(ModelForm):
    num = forms.HiddenInput()
    def __init__(self, *args, **kwargs):
        super(CreditosVideoForm, self).__init__(*args, **kwargs)
    class Meta:
        model = models.CreditosVideo
        fields = ['codigo_identificacion','anio_produccion','sinopsis','direccion_realizacion',
        'guion','camara','foto_fija','color','duracion_mins',
        'reparto','testimonios','idioma','musica','edicion','produccion','pais']
        labels={
            'codigo_identificacion':'Código Identificación',
            'anio_produccion': 'Año de producción',
            'sinopsis': 'Sinopsis',
            'direccion_realizacion':'Dirección',
            'guion': 'Guión',
            'camara': 'Cámara',
            'foto_fija':'Foto fija',
            'color':'Color o B/N',
            'duracion_mins':'Duración en mins',
            'reparto':'Reparto',
            'testimonios':'Testimonios',
            'idioma':'Idioma',
            'musica':'Música',
            'edicion':'Edición',
            'produccion':'Producción',
            'pais':'País'
        }
        widgets={
            'sinopsis':forms.Textarea(),
            'guion':forms.Textarea(),
            'testimonios':forms.Textarea(),
            'direccion_realizacion':forms.Textarea(),
            'guion':forms.Textarea(),
            'camara':forms.Textarea(),
            'foto_fija':forms.Textarea(),
            'reparto':forms.Textarea(),
            'testimonios':forms.Textarea(),
            'musica':forms.Textarea(),
            'edicion':forms.Textarea(),
            'produccion':forms.Textarea()
        }
        
        
        

