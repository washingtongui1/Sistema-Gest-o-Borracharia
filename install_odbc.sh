#!/bin/bash
# Instala o driver e configura automaticamente
apt-get update
apt-get install -y gnupg2 curl unixodbc-dev

# Adiciona o repositório da Microsoft
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update

# Instala o driver
ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Força a criação do link do odbcinst.ini usando o comando oficial do driver
odbcinst -i -d -f /opt/microsoft/msodbcsql18/etc/odbcinst.ini