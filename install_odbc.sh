#!/bin/bash
# Instala o driver ODBC de forma simplificada
apt-get update
apt-get install -y gnupg2
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
# O --allow-unauthenticated permite instalar mesmo com erro de chave
apt-get install -y --allow-unauthenticated msodbcsql18