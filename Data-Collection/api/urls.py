from django.urls import path
from . import views

urlpatterns = [
    path('login', views.login_view),
    path('logout', views.logout_view),
    path('upload_multiple_image', views.upload_images),
    path('health', views.health_check)
]