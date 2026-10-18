from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('api/chat/', views.gemini_chat_api, name='gemini_chat_api'),
    path('serviceworker.js', views.serviceworker_view, name='serviceworker'),
]