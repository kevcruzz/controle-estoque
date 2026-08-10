"""
Adiciona as colunas de controle de lote ao banco de PRODUCAO.
 
Por que este script existe: o create_all() do SQLModel so cria tabelas que
ainda nao existem. Ele NAO adiciona colunas novas a tabelas ja criadas.
Como produto, movimentacao, itemnotafiscal e empresa ja existem no
Postgres, as colunas novas precisam ser adicionadas na mao.
 
Diferente do resetar_banco.py, este script PRESERVA os dados.
 
Uso (PowerShell):
    $env:DATABASE_URL="<External Database URL do Render>"
    python migrar_lote.py
 
Observacao honesta: alterar schema com script proprio funciona, mas nao
escala. Antes do primeiro cliente pagante, o projeto precisa do Alembic,
que versiona cada mudanca de schema e sabe desfazer.
"""
 
import os
 
from sqlalchemy import create_engine, text
 
COLUNAS = [
    ("empresa", "exige_lote", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("produto", "controla_lote", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("movimentacao", "lote", "VARCHAR"),
    ("itemnotafiscal", "lote", "VARCHAR"),
]
 
url = os.getenv("DATABASE_URL")
if not url:
    raise SystemExit("Defina DATABASE_URL antes de rodar.")
if not url.startswith("postgres"):
    raise SystemExit("Este script e para PostgreSQL.")
 
engine = create_engine(url)
 
with engine.begin() as conexao:
    for tabela, coluna, tipo in COLUNAS:
        # IF NOT EXISTS deixa o script seguro para rodar mais de uma vez
        conexao.execute(
            text(f"ALTER TABLE {tabela} ADD COLUMN IF NOT EXISTS {coluna} {tipo}")
        )
        print(f"  ok: {tabela}.{coluna}")
 
    conexao.execute(
        text("CREATE INDEX IF NOT EXISTS ix_movimentacao_lote ON movimentacao (lote)")
    )
    conexao.execute(
        text("CREATE INDEX IF NOT EXISTS ix_itemnotafiscal_lote ON itemnotafiscal (lote)")
    )
    print("  ok: indices de lote")
 
print("\nMigracao concluida. Os dados existentes foram preservados.")