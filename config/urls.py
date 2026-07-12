# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('clientes/', include('gestaoClientes.urls')), # O "include" aponta para o app
    # Rota global de logout
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]