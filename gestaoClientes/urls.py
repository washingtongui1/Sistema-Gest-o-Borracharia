# busca_cliente/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Rota de Login: A porta de entrada para o sistema.
    # Deve ser a primeira para garantir que o acesso seja verificado logo no início.
    path('login/', views.login_view, name='login'),

    # Rotas de Gestão: Acesso ao Dashboard, clientes e estoque.
    path('gestaoClientes/', views.gestaoClientes, name='gestao_clientes'),
    path('estoque/', views.estoque_geral, name='estoque_geral'),
    
    # Rotas de Cadastro: Operações de inclusão no banco de dados.
    path('cadastrar-cliente/', views.cadastrar_usuario, name='cadastrar_cliente'),
    path('cadastrar-veiculo/<int:id_cliente>/', views.cadastrar_veiculo, name='cadastrar_veiculo'),
    
    # Rotas de Ordem de Serviço: Fluxo principal de trabalho.
    path('criar-os/<int:id_cliente>/', views.criar_nova_os, name='criar_nova_os'),
    path('adicionar-itens/<int:id_os>/', views.adicionar_itens_os, name='adicionar_itens_os'),
    path('cancelar-os/<int:id_os>/', views.cancelar_os, name='cancelar_os'),
    path('listar-ordem-servico/', views.listar_ordem_servico, name='listar_ordem_servico'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('finalizar-os/<int:id_os>/', views.finalizar_os_view, name='finalizar_os'),
]