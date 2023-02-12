from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('', views.index, name='index'),
    path('logout/', views.logout, name='logout'),
    path('download/', views.download, name='download')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
