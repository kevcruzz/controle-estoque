from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlmodel import Session, SQLModel, select
 
from app.database import get_session, USA_POSTGRES
from app.models import Empresa, Usuario
from app.security import gerar_hash_senha, usuario_atual, exigir_papel
from app.database import get_session_tenant
 
router = APIRouter(prefix="/empresas", tags=["Empresas"])
 
 
class EmpresaCadastro(SQLModel):
    nome_empresa: str
    cnpj: str | None = None
    email_admin: str
    senha_admin: str
 
 
class EmpresaCriada(SQLModel):
    empresa_id: int
    nome: str
    email_admin: str
 
 
@router.post("/cadastrar", response_model=EmpresaCriada)
def cadastrar_empresa(
    dados: EmpresaCadastro,
    session: Session = Depends(get_session),
):
    """
    Onboarding: cria a empresa (o inquilino) e o primeiro usuario admin dela.
 
    Endpoint publico - e por aqui que uma nova empresa entra no sistema.
    """
    if not dados.nome_empresa.strip():
        raise HTTPException(status_code=400, detail="O nome da empresa e obrigatorio")
    if len(dados.senha_admin) < 8:
        raise HTTPException(
            status_code=400, detail="A senha deve ter ao menos 8 caracteres"
        )
 
    email = dados.email_admin.strip().lower()
    if session.exec(select(Usuario).where(Usuario.email == email)).first():
        raise HTTPException(status_code=400, detail="Este e-mail ja esta em uso")
 
    empresa = Empresa(nome=dados.nome_empresa.strip(), cnpj=dados.cnpj)
    session.add(empresa)
    session.flush()  # garante o id da empresa antes de criar o usuario
 
    # O RLS exige saber de qual empresa e a linha que vamos inserir
    if USA_POSTGRES:
        session.exec(
            text("SELECT set_config('app.empresa_id', :valor, true)").bindparams(
                valor=str(empresa.id)
            )
        )
 
    admin = Usuario(
        empresa_id=empresa.id,
        email=email,
        senha_hash=gerar_hash_senha(dados.senha_admin),
        papel="admin",
    )
    session.add(admin)
    session.commit()
    session.refresh(empresa)
 
    return EmpresaCriada(
        empresa_id=empresa.id, nome=empresa.nome, email_admin=email
    )
 
 
class EmpresaConfig(SQLModel):
    id: int
    nome: str
    cnpj: str | None = None
    exige_lote: bool
 
 
class EmpresaConfigAlterar(SQLModel):
    exige_lote: bool
 
 
@router.get("/minha", response_model=EmpresaConfig)
def minha_empresa(
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(usuario_atual),
):
    empresa = session.get(Empresa, usuario["empresa_id"])
    if empresa is None:
        raise HTTPException(status_code=404, detail="Empresa nao encontrada")
    return EmpresaConfig(
        id=empresa.id,
        nome=empresa.nome,
        cnpj=empresa.cnpj,
        exige_lote=empresa.exige_lote,
    )
 
 
@router.patch("/configuracoes", response_model=EmpresaConfig)
def alterar_configuracoes(
    dados: EmpresaConfigAlterar,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(exigir_papel("admin")),
):
    empresa = session.get(Empresa, usuario["empresa_id"])
    if empresa is None:
        raise HTTPException(status_code=404, detail="Empresa nao encontrada")
 
    empresa.exige_lote = dados.exige_lote
    session.add(empresa)
    session.commit()
    session.refresh(empresa)
 
    return EmpresaConfig(
        id=empresa.id,
        nome=empresa.nome,
        cnpj=empresa.cnpj,
        exige_lote=empresa.exige_lote,
    )