from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect # Adicione esta importação

urlpatterns = [
    path('admin/', admin.site.urls),
    path('clientes/', include('gestaoClientes.urls')),
    
    # Rota global de logout
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Redirecionamento da raiz: se acessar http://127.0.0.1:8000/ vai para o login
    path('', lambda request: redirect('login')),
]