from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, update

from app.database import get_session
from app.models import Movimentacao, Produto, TipoMovimentacao
from app.schemas import MovimentacaoCriar, MovimentacaoLer
from app.security import usuario_atual, exigir_papel
from app.websocket import gerenciador

router = APIRouter(prefix="/movimentacoes", tags=["Movimentações"])


@router.post("/", response_model=MovimentacaoLer)
async def criar_movimentacao (
    dados: MovimentacaoCriar,
    session: Session = Depends(get_session),
    usuario: dict = Depends(exigir_papel("admin", "operador")),
):
    if dados.quantidade <= 0:
        raise HTTPException(status_code=400, detail="A quantidade deve ser maior que zero")

    produto = session.get(Produto, dados.produto_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    if dados.tipo == TipoMovimentacao.entrada:
        comando = (
            update(Produto)
            .where(Produto.id == dados.produto_id)
            .values(saldo=Produto.saldo + dados.quantidade)
        )
        session.exec(comando)
    else:
        comando = (
            update(Produto)
            .where(Produto.id == dados.produto_id)
            .where(Produto.saldo >= dados.quantidade)
            .values(saldo=Produto.saldo - dados.quantidade)
        )
        resultado = session.exec(comando)
        if resultado.rowcount == 0:
            session.rollback()
            raise HTTPException(
                status_code=400,
                detail="Saldo insuficiente para a saída",
            )

    movimentacao = Movimentacao(
        produto_id=dados.produto_id,
        tipo=dados.tipo,
        quantidade=dados.quantidade,
        motivo=dados.motivo,
    )
    session.add(movimentacao)

    session.commit()
    session.refresh(movimentacao)

    await gerenciador.avisar_todos("estoque_atualizado")
    
    return movimentacao


@router.get("/", response_model=list[MovimentacaoLer])
def listar_movimentacoes(
    produto_id: Optional[int] = None,
    session: Session = Depends(get_session),
    usuario: dict = Depends(usuario_atual),
):
    consulta = select(Movimentacao).order_by(Movimentacao.criado_em.desc())

    if produto_id is not None:
        consulta = consulta.where(Movimentacao.produto_id == produto_id)

    movimentacoes = session.exec(consulta).all()
    return movimentacoes