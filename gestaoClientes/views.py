import os
import logging
import pyodbc
from dotenv import load_dotenv
from django.shortcuts import render, redirect
from django.contrib import messages

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

def gestaoClientes(request):
    cpf = request.GET.get('cpf')
    cliente, veiculos, error_message = None, [], None

    if cpf:
        try:
            cols_c, rows_c = _executar_sql(
                "SELECT TOP 1 id_cliente, nome, cpf_cnpj, telefone, email FROM [dbo].[Clientes] WHERE cpf_cnpj = ?", 
                (cpf,)
            )
            if rows_c:
                cliente = dict(zip(cols_c, rows_c[0]))
                cols_v, rows_v = _executar_sql(
                    "SELECT * FROM [dbo].[Veiculos] WHERE id_cliente = ?", 
                    (cliente['id_cliente'],)
                )
                veiculos = [dict(zip(cols_v, row)) for row in rows_v]
            else:
                error_message = "Cliente não encontrado."
        except Exception as exc:
            logger.exception('Erro na busca')
            error_message = f'Erro na consulta: {exc}'

    return render(request, 'gestaoClientes.html', {
        'cliente': cliente, 'veiculos': veiculos, 'cpf_digitado': cpf, 'error_message': error_message
    })

def estoque_geral(request):
    # Função mantida para evitar erro de inicialização do Django
    pass 

def cadastrar_usuario(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        cpf = request.POST.get('cpf')
        telefone = request.POST.get('telefone')
        email = request.POST.get('email')

        try:
            conn = _get_db_connection()
            cursor = conn.cursor()

            # 1. VERIFICAÇÃO: O cliente já existe?
            cursor.execute("SELECT COUNT(*) FROM [dbo].[Clientes] WHERE cpf_cnpj = ?", (cpf,))
            existe = cursor.fetchone()[0]

            if existe > 0:
                messages.warning(request, 'Atenção: Este CPF/CNPJ já está cadastrado!')
            else:
                # 2. SE NÃO EXISTIR, FAZ O INSERT
                sql = "INSERT INTO [dbo].[Clientes] (nome, cpf_cnpj, telefone, email) VALUES (?, ?, ?, ?)"
                cursor.execute(sql, (nome, cpf, telefone, email))
                conn.commit()
                messages.success(request, 'Cliente cadastrado com sucesso!')

            cursor.close()
            conn.close()
            return redirect('gestao_clientes') # Ajuste se necessário
        
        except Exception as e:
            logger.exception('Erro ao cadastrar cliente')
            messages.error(request, f'Erro ao salvar: {e}')

    return render(request, 'cadastroClientes.html')