"""
Configuracao do Alembic para o KFuture ERP.
 
Dois ajustes em relacao ao arquivo padrao:
 
1. A URL do banco vem do .env (a mesma DATABASE_URL da aplicacao), e nao
   do alembic.ini. Assim a senha do banco nunca vai para o repositorio.
 
2. O target_metadata aponta para os modelos do SQLModel, o que permite
   gerar migrations automaticamente com --autogenerate.
"""
 
import os
import sys
from logging.config import fileConfig
from pathlib import Path
 
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel
 
from alembic import context
 
# Deixa o pacote "app" importavel a partir da pasta backend
sys.path.append(str(Path(__file__).resolve().parents[1]))
 
load_dotenv()
 
# Importar os modelos registra as tabelas no SQLModel.metadata
from app import models  # noqa: E402,F401
 
config = context.config
 
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
 
banco = os.getenv("DATABASE_URL", "sqlite:///estoque.db")
config.set_main_option("sqlalchemy.url", banco)
 
target_metadata = SQLModel.metadata
 
 
def run_migrations_offline() -> None:
    context.configure(
        url=banco,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
 
 
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
 
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Necessario no SQLite: ele nao suporta ALTER TABLE completo,
            # entao o Alembic recria a tabela quando preciso.
            render_as_batch=banco.startswith("sqlite"),
        )
        with context.begin_transaction():
            context.run_migrations()
 
 
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()