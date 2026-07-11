# busca_cliente/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # O prefixo 'clientes/' já foi definido no arquivo raiz, então aqui vai só o resto:
    path('gestaoClientes/', views.gestaoClientes, name='gestao_clientes'),
    path('estoque/', views.estoque_geral, name='estoque_geral'), # Adicione esta linha
    path('cadastrar-cliente/', views.cadastrar_usuario, name='cadastrar_cliente'),
]