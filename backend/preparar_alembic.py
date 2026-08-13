"""
Prepara o banco de PRODUCAO para o Alembic.
 
O problema: seu banco ja tem as tabelas (empresa, produto, notafiscal...),
criadas pelo create_all. Se voce simplesmente rodar 'alembic upgrade head',
o Alembic vai tentar CRIAR essas tabelas de novo e quebrar.
 
A solucao e o "stamp": dizer ao Alembic "considere a migration inicial como
ja aplicada, ela representa o que ja existe". A partir dai as proximas
migrations rodam normalmente.
 
Rode este script UMA VEZ, e so no banco que ja existia.
 
Uso (PowerShell, na pasta backend):
    $env:DATABASE_URL="<External Database URL do Render>"
    python preparar_alembic.py
"""
 
import os
import subprocess
import sys
 
url = os.getenv("DATABASE_URL")
if not url:
    raise SystemExit("Defina DATABASE_URL antes de rodar.")
 
destino = url.split("@")[-1].split("/")[0] if "@" in url else url
print(f"Banco alvo: {destino}\n")
 
print("1. Marcando a migration inicial como aplicada (stamp)...")
resultado = subprocess.run(
    [sys.executable, "-m", "alembic", "stamp", "b64f3f26e783"],
    capture_output=True,
    text=True,
)
print(resultado.stdout or resultado.stderr)
 
if resultado.returncode != 0:
    raise SystemExit("Falha no stamp. Verifique a DATABASE_URL e tente de novo.")
 
print("2. Aplicando as migrations pendentes (compras e producao)...")
resultado = subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    capture_output=True,
    text=True,
)
print(resultado.stdout or resultado.stderr)
 
if resultado.returncode != 0:
    raise SystemExit("Falha no upgrade.")
 
print("\nPronto. Daqui em diante, toda mudanca de schema segue o fluxo:")
print("  1. altera os modelos em app/models.py")
print("  2. alembic revision --autogenerate -m 'descricao'")
print("  3. alembic upgrade head")
print("\nNao e mais preciso escrever script de migracao na mao.")