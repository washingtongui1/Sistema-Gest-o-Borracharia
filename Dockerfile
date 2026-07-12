# Usa uma imagem Python oficial baseada em Debian
FROM python:3.13-slim

# Instala dependências do sistema necessárias para o SQL Server e ODBC
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unixodbc \
    unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos de requisitos e instala as libs do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o seu código para dentro do container
COPY . .

# Comando para iniciar o Django (usando o gunicorn)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]