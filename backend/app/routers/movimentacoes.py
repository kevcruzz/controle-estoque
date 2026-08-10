from typing import Optional
 
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, update
 
from app.database import get_session_tenant
from app.models import Movimentacao, Produto, TipoMovimentacao, Empresa
from app.schemas import MovimentacaoCriar, MovimentacaoLer
from app.security import usuario_atual, exigir_papel
from app.tenant import buscar_do_tenant
from app.websocket import gerenciador
 
router = APIRouter(prefix="/movimentacoes", tags=["Movimentacoes"])
 
 
@router.post("/", response_model=MovimentacaoLer)
async def criar_movimentacao(
    dados: MovimentacaoCriar,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(exigir_papel("admin", "operador")),
):
    empresa_id = usuario["empresa_id"]
 
    if dados.quantidade <= 0:
        raise HTTPException(status_code=400, detail="A quantidade deve ser maior que zero")
 
    produto = buscar_do_tenant(session, Produto, dados.produto_id, empresa_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
 
    empresa = session.get(Empresa, empresa_id)
    exige_lote = (empresa is not None and empresa.exige_lote) or produto.controla_lote
    lote = (dados.lote or "").strip() or None
 
    if exige_lote and dados.tipo == TipoMovimentacao.entrada and lote is None:
        raise HTTPException(
            status_code=400,
            detail=f"O produto '{produto.nome}' exige informar o lote na entrada.",
        )
 
    if dados.tipo == TipoMovimentacao.entrada:
        comando = (
            update(Produto)
            .where(Produto.id == dados.produto_id)
            .where(Produto.empresa_id == empresa_id)
            .values(saldo=Produto.saldo + dados.quantidade)
        )
        session.exec(comando)
    else:
        comando = (
            update(Produto)
            .where(Produto.id == dados.produto_id)
            .where(Produto.empresa_id == empresa_id)
            .where(Produto.saldo >= dados.quantidade)
            .values(saldo=Produto.saldo - dados.quantidade)
        )
        resultado = session.exec(comando)
        if resultado.rowcount == 0:
            session.rollback()
            raise HTTPException(
                status_code=400,
                detail="Saldo insuficiente para a saida",
            )
 
    movimentacao = Movimentacao(
        empresa_id=empresa_id,
        produto_id=dados.produto_id,
        tipo=dados.tipo,
        quantidade=dados.quantidade,
        motivo=dados.motivo,
        lote=lote,
    )
    session.add(movimentacao)
 
    session.commit()
    session.refresh(movimentacao)
 
    await gerenciador.avisar_todos("estoque_atualizado")
 
    return movimentacao
 
 
@router.get("/", response_model=list[MovimentacaoLer])
def listar_movimentacoes(
    produto_id: Optional[int] = None,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(usuario_atual),
):
    consulta = (
        select(Movimentacao)
        .where(Movimentacao.empresa_id == usuario["empresa_id"])
        .order_by(Movimentacao.criado_em.desc())
    )
 
    if produto_id is not None:
        consulta = consulta.where(Movimentacao.produto_id == produto_id)
 
    return session.exec(consulta).all()