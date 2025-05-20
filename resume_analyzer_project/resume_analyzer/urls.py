from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_resume, name='upload_resume'),
    path('resume/<int:pk>/', views.resume_detail, name='resume_detail'),
    path('resume/<int:pk>/chat/', views.chat_message, name='chat_message'),
    path('resume/<int:pk>/delete/', views.delete_resume, name='delete_resume'),
]
