#!/bin/bash
# Instala o driver ODBC e registra no arquivo de configuração
apt-get update
apt-get install -y gnupg2
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
apt-get install -y --allow-unauthenticated msodbcsql18

# Registrar o driver no odbcinst.ini
echo "[ODBC Driver 18 for SQL Server]" > /etc/odbcinst.ini
echo "Description=Microsoft ODBC Driver 18 for SQL Server" >> /etc/odbcinst.ini
echo "Driver=/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.0.so.1.1" >> /etc/odbcinst.ini
echo "UsageCount=1" >> /etc/odbcinst.ini