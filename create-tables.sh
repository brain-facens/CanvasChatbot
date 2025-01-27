#!/bin/bash

# Nome do banco de dados
DB_NAME="canvas.db"

# Comando SQL para criar as tabelas
SQL_COMMANDS=$(cat <<EOF
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    message TEXT NOT NULL,
    chat_response TEXT NOT NULL,
    date TEXT NOT NULL
);
EOF
)

# Cria o banco de dados e executa os comandos
sqlite3 "$DB_NAME" <<EOF
$SQL_COMMANDS
EOF

# Confirmação
echo "Tabelas criadas no banco de dados '$DB_NAME'."
