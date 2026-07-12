import os
import logging
import pyodbc
from dotenv import load_dotenv
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

# --- Conexão ---
def _get_db_connection():
    load_dotenv()
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={os.getenv('DB_HOST')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')}"
    )
    return pyodbc.connect(conn_str)

# --- Execução Segura ---
def _executar_sql(query, params=()):
    conn = _get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return columns, rows
    finally:
        try: cursor.close() 
        except: pass
        try: conn.close() 
        except: pass

# --- Views ---

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def gestaoClientes(request):
    cpf = request.GET.get('cpf')
    cliente, veiculos, error_message = None, [], None

    if not cpf:
        request.session.pop('id_cliente_autorizado', None)
    
    if cpf:
        try:
            cols_c, rows_c = _executar_sql(
                "SELECT TOP 1 id_cliente, nome, cpf_cnpj, telefone, email FROM [dbo].[Clientes] WHERE cpf_cnpj = ?", 
                (cpf,)
            )
            if rows_c:
                cliente = dict(zip(cols_c, rows_c[0]))
                request.session['id_cliente_autorizado'] = cliente['id_cliente']
                
                cols_v, rows_v = _executar_sql(
                    "SELECT * FROM [dbo].[Veiculos] WHERE id_cliente = ?", 
                    (cliente['id_cliente'],)
                )
                veiculos = [dict(zip(cols_v, row)) for row in rows_v]
            else:
                error_message = "Cliente não encontrado."
                request.session.pop('id_cliente_autorizado', None)
        except Exception as exc:
            logger.exception('Erro na busca')
            error_message = f'Erro na consulta: {exc}'

    return render(request, 'gestaoClientes.html', {
        'cliente': cliente, 
        'veiculos': veiculos, 
        'cpf_digitado': cpf, 
        'error_message': error_message
    })

@login_required
def cadastrar_usuario(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        cpf = request.POST.get('cpf')
        telefone = request.POST.get('telefone')
        email = request.POST.get('email')

        try:
            conn = _get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM [dbo].[Clientes] WHERE cpf_cnpj = ?", (cpf,))
            existe = cursor.fetchone()[0]

            if existe > 0:
                messages.warning(request, 'Atenção: Este CPF/CNPJ já está cadastrado!')
            else:
                sql = "INSERT INTO [dbo].[Clientes] (nome, cpf_cnpj, telefone, email) VALUES (?, ?, ?, ?)"
                cursor.execute(sql, (nome, cpf, telefone, email))
                conn.commit()
                messages.success(request, 'Cliente cadastrado com sucesso!')
            cursor.close()
            conn.close()
            return redirect('gestao_clientes')
        except Exception as e:
            logger.exception('Erro ao cadastrar cliente')
            messages.error(request, f'Erro ao salvar: {e}')

    return render(request, 'cadastroClientes.html')

@login_required
def cadastrar_veiculo(request, id_cliente):
    id_autorizado = request.session.get('id_cliente_autorizado')
    if id_autorizado is None or int(id_cliente) != int(id_autorizado):
        messages.error(request, "Acesso negado.")
        return redirect('gestao_clientes')

    cols, rows = _executar_sql("SELECT id_cliente, nome FROM [dbo].[Clientes] WHERE id_cliente = ?", (id_cliente,))
    if not rows:
        messages.error(request, "Cliente não encontrado.")
        return redirect('gestao_clientes')
    
    cliente = dict(zip(cols, rows[0]))

    if request.method == 'POST':
        placa = request.POST.get('placa')
        try:
            conn = _get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM [dbo].[Veiculos] WHERE placa = ?", (placa,))
            existe = cursor.fetchone()[0]

            if existe > 0:
                messages.warning(request, f"Atenção: O veículo com placa {placa} já está cadastrado!")
            else:
                cursor.execute(
                    "INSERT INTO [dbo].[Veiculos] (id_cliente, placa, marca, modelo, ano) VALUES (?, ?, ?, ?, ?)",
                    (id_cliente, placa, request.POST.get('marca'), request.POST.get('modelo'), request.POST.get('ano'))
                )
                conn.commit()
                messages.success(request, f"Veículo cadastrado para {cliente['nome']}!")
            cursor.close()
            conn.close()
            return redirect('gestao_clientes')
        except Exception as e:
            messages.error(request, f"Erro ao salvar: {e}")

    return render(request, 'cadastroVeiculos.html', {'cliente': cliente})

@login_required
def criar_nova_os(request, id_cliente):
    cols_c, rows_c = _executar_sql("SELECT nome FROM Clientes WHERE id_cliente = ?", (id_cliente,))
    cliente = {'nome': rows_c[0][0]} if rows_c else {'nome': 'Cliente não encontrado'}

    cols_v, rows_v = _executar_sql("SELECT id_veiculo, placa, modelo FROM Veiculos WHERE id_cliente = ?", (id_cliente,))
    veiculos = [dict(zip(cols_v, row)) for row in rows_v]

    cols_f, rows_f = _executar_sql("SELECT id_funcionario, nome_completo FROM Funcionarios")
    funcionarios = [dict(zip(cols_f, row)) for row in rows_f]

    if request.method == 'POST':
        conn = _get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO [dbo].[OrdemServico] 
                (id_cliente, id_veiculo, id_funcionario, data_abertura, status_os, valor_total)
                OUTPUT Inserted.id_os
                VALUES (?, ?, ?, GETDATE(), 'Em Execução', 0.00)
            """, (id_cliente, request.POST.get('id_veiculo'), request.POST.get('id_funcionario')))
            
            id_nova_os = cursor.fetchone()[0]
            conn.commit()
            return redirect('adicionar_itens_os', id_os=id_nova_os)
        except Exception as e:
            logger.exception('Erro ao criar OS')
            messages.error(request, f"Erro ao criar OS: {e}")
        finally:
            conn.close()

    return render(request, 'criarNovaOs.html', {
        'cliente': cliente,
        'veiculos': veiculos,
        'funcionarios': funcionarios
    })

@login_required
def adicionar_itens_os(request, id_os):
    conn = _get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        produtos = request.POST.getlist('produto[]')
        qtds = request.POST.getlist('qtd[]')
        valores = request.POST.getlist('valor[]')
        observacoes = request.POST.get('observacoes')
        
        valor_total_calculado = 0.0

        for i in range(len(produtos)):
            if produtos[i]:
                valor_unitario = float(valores[i])
                quantidade = int(qtds[i])
                valor_total_calculado += (valor_unitario * quantidade)

                cursor.execute("""
                    INSERT INTO [dbo].[ItensOrdemServico] (id_os, id_produto, quantidade, valor_unitario)
                    VALUES (?, ?, ?, ?)
                """, (id_os, produtos[i], qtds[i], valor_unitario))
        
        cursor.execute("""
            UPDATE [dbo].[OrdemServico] 
            SET valor_total = ?, observacoes = ? 
            WHERE id_os = ?
        """, (valor_total_calculado, observacoes, id_os))
        
        conn.commit()
        cursor.close()
        conn.close()
        return redirect('gestao_clientes')
    else:
        cursor.execute("SELECT id_produto, nome_produto, preco_venda FROM [dbo].[Produtos]")
        produtos_disponiveis = cursor.fetchall()
        cursor.close()
        conn.close()
        return render(request, 'adicionarItens.html', {
            'id_os': id_os,
            'produtos_disponiveis': produtos_disponiveis
        })

@login_required
def cancelar_os(request, id_os):
    conn = None
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE [dbo].[OrdemServico] SET status_os = 'Cancelada' WHERE id_os = ?", (id_os,))
        conn.commit()
    except Exception as e:
        print(f"Erro ao cancelar a OS: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()
    return redirect('gestao_clientes')

@login_required
def listar_ordem_servico(request):
    query = """
        SELECT 
            o.id_os, 
            o.data_abertura, 
            o.status_os, 
            o.valor_total, 
            c.nome AS cliente_nome, 
            v.placa AS veiculo_placa, 
            v.modelo AS veiculo_modelo
        FROM [dbo].[OrdemServico] o
        INNER JOIN [dbo].[Veiculos] v ON o.id_veiculo = v.id_veiculo
        INNER JOIN [dbo].[Clientes] c ON o.id_cliente = c.id_cliente
        ORDER BY o.data_abertura DESC
    """
    try:
        cols, rows = _executar_sql(query)
        ordens = [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        logger.exception('Erro ao buscar ordens de serviço')
        ordens = []
        messages.error(request, f"Erro ao carregar ordens: {e}")

    return render(request, 'listarOrdemServico.html', {'ordens': ordens})

@login_required
def estoque_geral(request):
    return render(request, 'estoque.html')

@login_required
def dashboard_view(request):
    # Por enquanto, apenas renderiza uma página de dashboard
    return render(request, 'dashboard.html')

def login_view(request):
    # --- Adicione estas duas linhas abaixo ---
    if request.user.is_authenticated:
        return redirect('gestao_clientes')
    # -----------------------------------------

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('gestao_clientes')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def finalizar_os_view(request, id_os):
    if request.method == 'POST':
        conn = None
        try:
            conn = _get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE [dbo].[OrdemServico] SET status_os = 'Concluída' WHERE id_os = ?", (id_os,))
            conn.commit()
            messages.success(request, f"Ordem de Serviço {id_os} finalizada com sucesso!")
        except Exception as e:
            logger.exception('Erro ao finalizar a OS')
            messages.error(request, f"Erro ao finalizar a OS: {e}")
        finally:
            if conn:
                try: cursor.close()
                except: pass
                try: conn.close()
                except: pass
        
        return redirect('listar_ordem_servico')