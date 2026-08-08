"""
Apaga TODAS as tabelas do banco apontado por DATABASE_URL.
 
Use apenas nesta migracao para multi-tenant, enquanto o banco so tem
dados de teste. A partir do momento em que existirem clientes reais,
NUNCA mais rode isto: o caminho passa a ser migracao com Alembic.
 
Uso:
    # Windows PowerShell
    $env:DATABASE_URL="<External Database URL do Render>"
    python resetar_banco.py
"""
 
import os
 
from sqlalchemy import create_engine, text
 
url = os.getenv("DATABASE_URL")
 
if not url:
    raise SystemExit("Defina DATABASE_URL antes de rodar.")
 
destino = url.split("@")[-1].split("/")[0] if "@" in url else url
print(f"Banco alvo: {destino}")
confirmacao = input("Isto APAGA todas as tabelas. Digite APAGAR para confirmar: ")
 
if confirmacao.strip() != "APAGAR":
    raise SystemExit("Cancelado.")
 
engine = create_engine(url)
 
with engine.begin() as conexao:
    if url.startswith("postgres"):
        # Recria o schema publico inteiro: some tudo de uma vez
        conexao.execute(text("DROP SCHEMA public CASCADE"))
        conexao.execute(text("CREATE SCHEMA public"))
    else:
        raise SystemExit("Este script e para PostgreSQL.")
 
print("Tabelas removidas. Suba a aplicacao: o create_all recria tudo ja no")
print("formato multi-tenant, com a Empresa Demonstracao e o admin padrao.")