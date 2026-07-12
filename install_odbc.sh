#!/bin/bash
# Instala dependências básicas
apt-get update
apt-get install -y curl gnupg2 unixodbc-dev

# Baixa e instala o pacote .deb oficial da Microsoft
curl -O https://download.microsoft.com/download/3/5/5/355d7943-6608-467a-85d0-2384c3116898/msodbcsql18_18.3.3.1-1_amd64.deb
apt-get install -y ./msodbcsql18_18.3.3.1-1_amd64.deb

# CRIAÇÃO MANUAL DO REGISTRO DO DRIVER (O truque definitivo)
# Apaga qualquer registro antigo e força o novo
rm -f /etc/odbcinst.ini
echo "[ODBC Driver 18 for SQL Server]" > /etc/odbcinst.ini
echo "Description=Microsoft ODBC Driver 18 for SQL Server" >> /etc/odbcinst.ini
echo "Driver=/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.0.so.1.1" >> /etc/odbcinst.ini
echo "UsageCount=1" >> /etc/odbcinst.ini