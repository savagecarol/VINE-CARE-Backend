from django.urls import path
from . import views

urlpatterns = [
    path('health/',    views.health_check,    name='health_check'),
    path('send/',      views.send_email,       name='send_email'),
    path('template/',  views.create_template,  name='create_template'),
    path('templates/', views.list_templates,   name='list_templates'),
    path('logs/',      views.notification_logs, name='notification_logs'),
]
