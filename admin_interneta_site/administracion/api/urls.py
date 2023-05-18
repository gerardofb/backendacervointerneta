from django.urls import path
from . import views
from rest_framework_simplejwt.views import(
    TokenObtainPairView,
    TokenRefreshView
)


app_name="administracion"

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('userprofile/',views.UserProfileView.as_view(),name="user-profile"),
    path('register/',views.RegisterUser.as_view(),name="registrar-user"),
    path('sendpasswordreset/',views.SendChangePwdLink.as_view(),name="send-resetpassword"),
    path('validateregister/',views.ValidateRegister.as_view(),name="validate-registro"),
    path("loginuser/",views.LoginView.as_view(),name="login-user"),
    path("passwordreset/",views.ResetPassword.as_view(),name="resetpassword"),
    path('categorias/', views.CategoriasListView.as_view(), name="lista-api-categorias"),
    path('videos/<int:pk>', views.VideosListView.as_view(), name="lista-api-videos"),
    path('videos/', views.AllVideosListView.as_view(), name="lista-api-allvideos"),
    path('videos/<query>', views.VideosFindView.as_view(),name='lista-api-findvideos'),
    path('shortlistvideos/',views.VideosShortListView.as_view(),name='lista-api-shortvideos'),
    path('video/<int:id>', views.VideoView.as_view(), name="detalle-api-video"),
    path('creditosvideo/<int:pk>', views.CreditosVideoView.as_view(), name="detalle-api-creditosvideo"),
    path('categoria/<int:id>', views.CategoriaView.as_view(), name="detalle-api-categoria"),
    path('commentvideo/', views.CommentByVideo.as_view(), name="comment-video"),
    path('commentvideoauth/', views.CommentByVideoAuth.as_view(), name="comment-video-auth"),
    path("answercommentauth/",views.AnswerCommentByVideoAuth.as_view(),name="answer-comment-auth"),
    path('searchcomment/',views.SearchComment.as_view(),name="search-comment"),
    path('searchanswercomment/',views.SearchAnswerComment.as_view(),name="search-answer-comment"),
    path("singlecomment/",views.SearchSingleComment.as_view(),name="single-comment"),
    path("relatevideo/",views.RelatoByVideo.as_view(),name="relate-video"),
    path("relatevideoauth/",views.RelatoByVideoAuth.as_view(),name="relate-video-auth"),
    path("relatetextvideoauth/",views.RelatoTextualByVideoAuth.as_view(),name="relate-text-video-auth"),
    path('searchrelato/',views.SearchRelato.as_view(),name="search-relato"),
    path('singlerelato/',views.SearchSingleRelato.as_view(),name="single-relato"),
    path('severalrelatos/',views.SearchBySeveralRelatos.as_view(),name="several-relatos-by-term"),
    path('cuentarelatos/',views.CountRelatos.as_view(),name="count-relatos"),
    path('users/<query>',views.UsersFindView.as_view(),name='list-api-findusers'),
    path('addfavoritevideo/',views.AddFavoritoUsuarioVideo.as_view(),name="add-favorite-video"),
    path('listfavoritevideos/',views.FavoritosUsuarioVideoListado.as_view(),name="list-favorite-videos"),
    path('detailfavoritesvideo/<int:pk>',views.FavoritosUsuarioVideoSingle.as_view(),name="detail-favorites-video"),
    path('detailfavoritesvideobyuser/',views.FavoritosVideoSingleUser.as_view(),name="detail-favorites-video-user"),
    path('addvisitvideo/',views.AddVisitaVideoView.as_view(),name="add-visit-view"),
    path('addvisitvideoauth/',views.AddVisitaVideoViewAuth.as_view(),name="add-visit-view-auth"),
    path("vistasporvideo/<int:pk>",views.VisitasVideoDetail.as_view(),name="get-visit-video"),
    path("vistasporvideo/",views.VisitasVideoList.as_view(),name="get-all-visit-video"),
    path("addeventousuario/",views.EventoByUser.as_view(),name="add-event-user"),
    path("eventosuser/<int:pk>",views.EventosPorMes.as_view(),name="list-user-events"),
    path("addfavoriterelato/",views.AddFavoritoUsuarioRelato.as_view(),name="add-favorite-relato"),
    path('detailfavoritesrelato/<pk>',views.FavoritosRelatoSingle.as_view(),name="detail-favorites-relatos"),
    path('listfavoriterelatos/',views.FavoritosRelatoListado.as_view(),name="list-favorite-relatos"),
    path("addvisitrelato/",views.AddVisitaRelatoView.as_view(),name="add-visita-relato"),
    path("addvisitrelatoauth/",views.AddVisitaRelatoViewAuth.as_view(),name="add-visita-relato-auth"),
    path("visitasderelato/",views.VisitasRelatoList.as_view(),name="get-all-visit-relato"),
    path("detailfavoritesrelatobyuser/",views.FavoritosRelatoSingleUser.as_view(),name="detail-favorites-relato-user"),
    path("addvisitevento/",views.AddVisitaEventoView.as_view(),name="add-visita-evento"),
    path("addvisiteventoauth/",views.AddVisitaEventoViewAuth.as_view(),name="add-visita-evento-auth"),
    path("visitasdeevento/",views.VisitasEventoList.as_view(),name="get-all-visit-evento"),
    path("visitasproximoseventos/",views.VistasEventosProximosList.as_view(),name="get-all-next-eventos"),
    path("calificarvideo/",views.AddCalificacionVideoView.as_view(),name="add-calificacion-video"),
    path("calificarvideoauth/",views.AddCalificacionVideoAuthView.as_view(),name="add-calificacion-video-auth"),
    path("listarcalificacionesvideos/",views.CalificacionVideoList.as_view(),name="get-all-calificaciones-videos"),
    path("calificacionbyvideo/<int:pk>",views.CalificacionVideoSingle.as_view(),name="get-calificacion-by-video"),
    path("singleclaificacionvideoauth/<int:pk>",views.CalificacionVideoByUser.as_view(),name="get-single-calificacion-video")

]