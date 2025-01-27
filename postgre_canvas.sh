#!/bin/bash

# Configurações do banco de dados PostgreSQL
DB_NAME="canvas"           # Nome do banco de dados
DB_USER="admin"            # Usuário do banco
DB_PASSWORD="admin"        # Senha do banco
DB_HOST="localhost"        # Host do banco
DB_PORT="5432"             # Porta do PostgreSQL

# Exporta a senha para evitar que seja solicitada
export PGPASSWORD="$DB_PASSWORD"

# Verifica se o banco de dados já existe
DB_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'")

if [ "$DB_EXISTS" != "1" ]; then
  echo "Criando o banco de dados '$DB_NAME'..."
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"
else
  echo "O banco de dados '$DB_NAME' já existe."
fi

# Comando SQL para criar as tabelas
SQL_COMMANDS=$(cat <<EOF
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    message TEXT NOT NULL,
    chat_response TEXT NOT NULL,
    date TIMESTAMP NOT NULL
);
EOF
)

# Cria as tabelas no banco de dados
echo "Criando as tabelas no banco de dados '$DB_NAME'..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$SQL_COMMANDS"

# Confirmação
echo "Banco de dados '$DB_NAME' e tabelas criados com sucesso no PostgreSQL."
