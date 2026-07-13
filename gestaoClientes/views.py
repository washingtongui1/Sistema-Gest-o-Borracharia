import logging
import os
import time

import pyodbc
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

logger = logging.getLogger(__name__)
pyodbc.pooling = True

_CONNECTION_STRING = None


def _get_connection_string():
    global _CONNECTION_STRING
    if _CONNECTION_STRING is None:
        _CONNECTION_STRING = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={os.getenv('DB_HOST')};"
            f"DATABASE={os.getenv('DB_NAME')};"
            f"UID={os.getenv('DB_USER')};"
            f"PWD={os.getenv('DB_PASSWORD')};"
            "Pooling=True;"
            "Connect Timeout=30;"
        )
    return _CONNECTION_STRING


def _get_db_connection():
    started = time.perf_counter()
    conn = pyodbc.connect(_get_connection_string(), autocommit=False)
    logger.info('Tempo para abrir conexão: %.3fs', time.perf_counter() - started)
    return conn


def _open_connection():
    conn = _get_db_connection()
    cursor = conn.cursor()
    return conn, cursor


def _fetch_one(cursor, query, params=()):
    started = time.perf_counter()
    cursor.execute(query, params)
    columns = [col[0] for col in cursor.description] if cursor.description else []
    row = cursor.fetchone()
    logger.info('Tempo da consulta: %.3fs', time.perf_counter() - started)
    return columns, row


def _fetch_all(cursor, query, params=()):
    started = time.perf_counter()
    cursor.execute(query, params)
    columns = [col[0] for col in cursor.description] if cursor.description else []
    rows = cursor.fetchall()
    logger.info('Tempo da consulta: %.3fs', time.perf_counter() - started)
    return columns, rows


def _execute_non_query(conn, cursor, query, params=(), commit=False):
    started = time.perf_counter()
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
        logger.info('Tempo da consulta: %.3fs', time.perf_counter() - started)
        return True
    except Exception:
        if conn:
            conn.rollback()
        logger.exception('Erro ao executar comando SQL')
        raise


def _close_resources(conn=None, cursor=None):
    if cursor is not None:
        try:
            cursor.close()
        except Exception:
            pass
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def gestaoClientes(request):
    started = time.perf_counter()
    cpf = request.GET.get('cpf')
    cliente, veiculos, error_message = None, [], None
    conn = None
    cursor = None

    if not cpf:
        request.session.pop('id_cliente_autorizado', None)

    if cpf:
        try:
            conn, cursor = _open_connection()
            cols_c, row_c = _fetch_one(
                cursor,
                "SELECT TOP 1 id_cliente, nome, cpf_cnpj, telefone, email FROM [dbo].[Clientes] WHERE cpf_cnpj = ?",
                (cpf,),
            )
            if row_c:
                cliente = dict(zip(cols_c, row_c))
                request.session['id_cliente_autorizado'] = cliente['id_cliente']

                cols_v, rows_v = _fetch_all(
                    cursor,
                    "SELECT id_veiculo, placa, modelo, marca, ano FROM [dbo].[Veiculos] WHERE id_cliente = ?",
                    (cliente['id_cliente'],),
                )
                veiculos = [dict(zip(cols_v, row)) for row in rows_v]
            else:
                error_message = 'Cliente não encontrado.'
                request.session.pop('id_cliente_autorizado', None)
        except Exception as exc:
            logger.exception('Erro na busca')
            error_message = f'Erro na consulta: {exc}'
        finally:
            _close_resources(conn, cursor)

    logger.info('Tempo total da view gestaoClientes: %.3fs', time.perf_counter() - started)
    return render(request, 'gestaoClientes.html', {
        'cliente': cliente,
        'veiculos': veiculos,
        'cpf_digitado': cpf,
        'error_message': error_message,
    })


@login_required
def cadastrar_usuario(request):
    started = time.perf_counter()
    if request.method == 'POST':
        nome = request.POST.get('nome')
        cpf = request.POST.get('cpf')
        telefone = request.POST.get('telefone')
        email = request.POST.get('email')

        conn = None
        cursor = None
        try:
            conn, cursor = _open_connection()
            _, row = _fetch_one(cursor, 'SELECT COUNT(*) FROM [dbo].[Clientes] WHERE cpf_cnpj = ?', (cpf,))
            existe = row[0] if row else 0

            if existe > 0:
                messages.warning(request, 'Atenção: Este CPF/CNPJ já está cadastrado!')
            else:
                sql = 'INSERT INTO [dbo].[Clientes] (nome, cpf_cnpj, telefone, email) VALUES (?, ?, ?, ?)'
                _execute_non_query(conn, cursor, sql, (nome, cpf, telefone, email), commit=True)
                messages.success(request, 'Cliente cadastrado com sucesso!')
            return redirect('gestao_clientes')
        except Exception as e:
            logger.exception('Erro ao cadastrar cliente')
            messages.error(request, f'Erro ao salvar: {e}')
        finally:
            _close_resources(conn, cursor)

    logger.info('Tempo total da view cadastrar_usuario: %.3fs', time.perf_counter() - started)
    return render(request, 'cadastroClientes.html')


@login_required
def cadastrar_veiculo(request, id_cliente):
    started = time.perf_counter()
    id_autorizado = request.session.get('id_cliente_autorizado')
    if id_autorizado is None or int(id_cliente) != int(id_autorizado):
        messages.error(request, 'Acesso negado.')
        return redirect('gestao_clientes')

    conn = None
    cursor = None
    try:
        conn, cursor = _open_connection()
        cols, rows = _fetch_all(cursor, 'SELECT id_cliente, nome FROM [dbo].[Clientes] WHERE id_cliente = ?', (id_cliente,))
        if not rows:
            messages.error(request, 'Cliente não encontrado.')
            return redirect('gestao_clientes')

        cliente = dict(zip(cols, rows[0]))

        if request.method == 'POST':
            placa = request.POST.get('placa')
            try:
                _, row = _fetch_one(cursor, 'SELECT COUNT(*) FROM [dbo].[Veiculos] WHERE placa = ?', (placa,))
                existe = row[0] if row else 0

                if existe > 0:
                    messages.warning(request, f'Atenção: O veículo com placa {placa} já está cadastrado!')
                else:
                    _execute_non_query(
                        conn,
                        cursor,
                        'INSERT INTO [dbo].[Veiculos] (id_cliente, placa, marca, modelo, ano) VALUES (?, ?, ?, ?, ?)',
                        (id_cliente, placa, request.POST.get('marca'), request.POST.get('modelo'), request.POST.get('ano')),
                        commit=True,
                    )
                    messages.success(request, f'Veículo cadastrado para {cliente["nome"]}!')
                return redirect('gestao_clientes')
            except Exception as e:
                logger.exception('Erro ao salvar veículo')
                messages.error(request, f'Erro ao salvar: {e}')
    finally:
        _close_resources(conn, cursor)

    logger.info('Tempo total da view cadastrar_veiculo: %.3fs', time.perf_counter() - started)
    return render(request, 'cadastroVeiculos.html', {'cliente': cliente})


@login_required
def criar_nova_os(request, id_cliente):
    started = time.perf_counter()
    conn = None
    cursor = None
    try:
        conn, cursor = _open_connection()
        cols_c, row_c = _fetch_one(cursor, 'SELECT nome FROM Clientes WHERE id_cliente = ?', (id_cliente,))
        cliente = {'nome': row_c[0]} if row_c else {'nome': 'Cliente não encontrado'}

        cols_v, rows_v = _fetch_all(cursor, 'SELECT id_veiculo, placa, modelo FROM Veiculos WHERE id_cliente = ?', (id_cliente,))
        veiculos = [dict(zip(cols_v, row)) for row in rows_v]

        cols_f, rows_f = _fetch_all(cursor, 'SELECT id_funcionario, nome_completo FROM Funcionarios')
        funcionarios = [dict(zip(cols_f, row)) for row in rows_f]

        if request.method == 'POST':
            try:
                _execute_non_query(
                    conn,
                    cursor,
                    """
                    INSERT INTO [dbo].[OrdemServico]
                    (id_cliente, id_veiculo, id_funcionario, data_abertura, status_os, valor_total)
                    OUTPUT Inserted.id_os
                    VALUES (?, ?, ?, GETDATE(), 'Em Execução', 0.00)
                    """,
                    (id_cliente, request.POST.get('id_veiculo'), request.POST.get('id_funcionario')),
                    commit=False,
                )
                id_nova_os = cursor.fetchone()[0]
                conn.commit()
                return redirect('adicionar_itens_os', id_os=id_nova_os)
            except Exception as e:
                logger.exception('Erro ao criar OS')
                messages.error(request, f'Erro ao criar OS: {e}')
                conn.rollback()
    finally:
        _close_resources(conn, cursor)

    logger.info('Tempo total da view criar_nova_os: %.3fs', time.perf_counter() - started)
    return render(request, 'criarNovaOs.html', {
        'cliente': cliente,
        'veiculos': veiculos,
        'funcionarios': funcionarios,
    })


@login_required
def adicionar_itens_os(request, id_os):
    started = time.perf_counter()
    conn = None
    cursor = None
    try:
        conn, cursor = _open_connection()

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

                    _execute_non_query(
                        conn,
                        cursor,
                        'INSERT INTO [dbo].[ItensOrdemServico] (id_os, id_produto, quantidade, valor_unitario) VALUES (?, ?, ?, ?)',
                        (id_os, produtos[i], qtds[i], valor_unitario),
                        commit=False,
                    )

            _execute_non_query(
                conn,
                cursor,
                'UPDATE [dbo].[OrdemServico] SET valor_total = ?, observacoes = ? WHERE id_os = ?',
                (valor_total_calculado, observacoes, id_os),
                commit=False,
            )
            conn.commit()
            return redirect('gestao_clientes')

        cols, rows = _fetch_all(cursor, 'SELECT id_produto, nome_produto, preco_venda FROM [dbo].[Produtos]')
        produtos_disponiveis = [tuple(row) for row in rows]
    except Exception as e:
        logger.exception('Erro ao processar itens da OS')
        messages.error(request, f'Erro ao salvar: {e}')
        if conn:
            conn.rollback()
    finally:
        _close_resources(conn, cursor)

    logger.info('Tempo total da view adicionar_itens_os: %.3fs', time.perf_counter() - started)
    if request.method == 'POST':
        return redirect('gestao_clientes')

    return render(request, 'adicionarItens.html', {
        'id_os': id_os,
        'produtos_disponiveis': produtos_disponiveis,
    })


@login_required
def cancelar_os(request, id_os):
    started = time.perf_counter()
    conn = None
    cursor = None
    try:
        conn, cursor = _open_connection()
        _execute_non_query(conn, cursor, "UPDATE [dbo].[OrdemServico] SET status_os = 'Cancelada' WHERE id_os = ?", (id_os,), commit=True)
    except Exception as e:
        logger.exception('Erro ao cancelar a OS')
    finally:
        _close_resources(conn, cursor)

    logger.info('Tempo total da view cancelar_os: %.3fs', time.perf_counter() - started)
    return redirect('gestao_clientes')


@login_required
def listar_ordem_servico(request):
    started = time.perf_counter()
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
        conn, cursor = _open_connection()
        cols, rows = _fetch_all(cursor, query)
        ordens = [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        logger.exception('Erro ao buscar ordens de serviço')
        ordens = []
        messages.error(request, f'Erro ao carregar ordens: {e}')
    finally:
        _close_resources(conn, cursor)

    logger.info('Tempo total da view listar_ordem_servico: %.3fs', time.perf_counter() - started)
    return render(request, 'listarOrdemServico.html', {'ordens': ordens})


@login_required
def estoque_geral(request):
    return render(request, 'estoque.html')


@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('gestao_clientes')

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
    started = time.perf_counter()
    if request.method == 'POST':
        conn = None
        cursor = None
        try:
            conn, cursor = _open_connection()
            _execute_non_query(conn, cursor, "UPDATE [dbo].[OrdemServico] SET status_os = 'Concluída' WHERE id_os = ?", (id_os,), commit=True)
            messages.success(request, f'Ordem de Serviço {id_os} finalizada com sucesso!')
        except Exception as e:
            logger.exception('Erro ao finalizar a OS')
            messages.error(request, f'Erro ao finalizar a OS: {e}')
        finally:
            _close_resources(conn, cursor)

        logger.info('Tempo total da view finalizar_os_view: %.3fs', time.perf_counter() - started)
        return redirect('listar_ordem_servico')

    logger.info('Tempo total da view finalizar_os_view: %.3fs', time.perf_counter() - started)
    return redirect('listar_ordem_servico')