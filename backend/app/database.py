import os
 
from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy import text
from sqlmodel import SQLModel, create_engine, Session
 
from app.security import usuario_atual
 
load_dotenv()
 
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///estoque.db")
 
engine = create_engine(DATABASE_URL, echo=False)
 
USA_POSTGRES = DATABASE_URL.startswith("postgres")
 
# Tabelas que guardam dados de cliente e precisam de isolamento por empresa.
#
# "usuario" fica FORA da lista de proposito: o login precisa ler essa tabela
# antes de saber a qual empresa a pessoa pertence. Com RLS ativo ali, nenhum
# login funcionaria. Os dados de usuario seguem protegidos pelo filtro de
# empresa na aplicacao.
TABELAS_TENANT = [
    "categoria",
    "produto",
    "movimentacao",
    "notafiscal",
    "itemnotafiscal",
]
 
# Tabelas onde o RLS precisa ficar desligado. A lista existe para DESFAZER
# uma configuracao anterior que tenha ligado o RLS nelas por engano.
TABELAS_SEM_RLS = ["usuario"]
 
 
def criar_tabelas():
    SQLModel.metadata.create_all(engine)
 
 
def aplicar_rls():
    """
    Ativa Row-Level Security no PostgreSQL.
 
    O banco passa a filtrar por empresa sozinho: mesmo que uma query da
    aplicacao esqueca o WHERE empresa_id, o Postgres nao devolve linhas
    de outra empresa.
 
    FORCE e obrigatorio: sem ele, o dono do banco (que e como a aplicacao
    conecta no Render) ignora as policies silenciosamente.
 
    Em SQLite nao ha RLS - por isso o filtro na aplicacao tambem existe.
    """
    if not USA_POSTGRES:
        return
 
    try:
        _configurar_rls()
    except Exception as erro:
        # O RLS e uma camada extra: o filtro por empresa na aplicacao continua
        # protegendo os dados. Falhar aqui nao deve impedir a aplicacao de subir.
        print(f"[AVISO] Nao foi possivel aplicar o RLS: {erro}")
 
 
def _configurar_rls():
    with engine.begin() as conexao:
        for tabela in TABELAS_SEM_RLS:
            conexao.execute(text(f"DROP POLICY IF EXISTS isolamento_empresa ON {tabela}"))
            conexao.execute(text(f"ALTER TABLE {tabela} NO FORCE ROW LEVEL SECURITY"))
            conexao.execute(text(f"ALTER TABLE {tabela} DISABLE ROW LEVEL SECURITY"))
 
        for tabela in TABELAS_TENANT:
            conexao.execute(text(f"ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY"))
            conexao.execute(text(f"ALTER TABLE {tabela} FORCE ROW LEVEL SECURITY"))
            conexao.execute(text(f"DROP POLICY IF EXISTS isolamento_empresa ON {tabela}"))
            conexao.execute(
                text(
                    f"""
                    CREATE POLICY isolamento_empresa ON {tabela}
                    USING (
                        empresa_id = NULLIF(
                            current_setting('app.empresa_id', true), ''
                        )::int
                    )
                    WITH CHECK (
                        empresa_id = NULLIF(
                            current_setting('app.empresa_id', true), ''
                        )::int
                    )
                    """
                )
            )
 
 
def get_session():
    """Sessao sem tenant. Usada apenas em login e cadastro de empresa."""
    with Session(engine) as session:
        yield session
 
 
def get_session_tenant(usuario: dict = Depends(usuario_atual)):
    """
    Sessao ja amarrada a empresa do usuario logado.
 
    Declara ao Postgres qual empresa esta falando; as policies de RLS
    usam esse valor. set_config com parametro evita SQL injection, e o
    terceiro argumento (true) limita o efeito a transacao atual.
    """
    with Session(engine) as session:
        if USA_POSTGRES:
            session.exec(
                text("SELECT set_config('app.empresa_id', :valor, true)").bindparams(
                    valor=str(usuario["empresa_id"])
                )
            )
        yield session