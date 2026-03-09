from django.urls import path
from . import views

urlpatterns = [
    path('notify/', views.send_notification),
    path('notifications/<uuid:user_id>/', views.get_user_notifications),
    path('notifications/<int:pk>/read/', views.mark_as_read),
]