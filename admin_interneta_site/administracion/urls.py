from re import template
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views
from .forms import LoginForm
from django.conf.urls.static import static
from django.conf import settings

urlpatterns =[
    path('iniciarsesion/',views.user_login, name='login'),
    path('cerrarsesion/', views.site_logout, name='logout'),
    path('',views.dashboard, name="admin-dashboard"),
    path('nuevacategoria/<int:num>',views.add_categoria, name='add-categoria'),
    path('categorias/',views.CategoriasView.as_view(),name='list-categorias'),
    path('deletecategoria/<int:num>',views.delete_categoria,name='delete-categoria'),
    path('videos/',views.VideosView.as_view(),name='list-videos'),
    path('nuevovideo/<int:num>',views.nuevo_video,name='new-video'),
    path('addvideo/<int:num>',views.add_video,name='add-video'),
    path('updatevideo/',views.update_video,name='update-video'),
    path('updatefilevideo/',views.update_file_video,name='update-file-video'),
    path('deletevideo/<int:num>',views.delete_video,name='delete-video'),
    path('addcreditosvideo/<int:num>', views.add_creditos_video,name='add-creditos-video'),
    path('updatecreditosvideo/',views.update_creditos_video,name='update-creditos-video')
]