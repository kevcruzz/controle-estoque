from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, update

from app.database import get_session
from app.models import Movimentacao, Produto, TipoMovimentacao
from app.schemas import MovimentacaoCriar, MovimentacaoLer

router = APIRouter(prefix="/movimentacoes", tags=["Movimentações"])


@router.post("/", response_model=MovimentacaoLer)
def criar_movimentacao(dados: MovimentacaoCriar, session: Session = Depends(get_session)):
    # 1. Validações básicas de entrada
    if dados.quantidade <= 0:
        raise HTTPException(status_code=400, detail="A quantidade deve ser maior que zero")

    produto = session.get(Produto, dados.produto_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # 2. Atualizar o saldo de forma ATÔMICA e SEGURA contra concorrência
    if dados.tipo == TipoMovimentacao.entrada:
        comando = (
            update(Produto)
            .where(Produto.id == dados.produto_id)
            .values(saldo=Produto.saldo + dados.quantidade)
        )
        session.exec(comando)
    else:  # saída
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

    # 3. Registrar a movimentação no histórico (ledger)
    movimentacao = Movimentacao(
        produto_id=dados.produto_id,
        tipo=dados.tipo,
        quantidade=dados.quantidade,
        motivo=dados.motivo,
    )
    session.add(movimentacao)

    # 4. Confirmar tudo de uma vez (saldo + movimentação na mesma transação)
    session.commit()
    session.refresh(movimentacao)
    return movimentacao


@router.get("/", response_model=list[MovimentacaoLer])
def listar_movimentacoes(
    produto_id: Optional[int] = None,
    session: Session = Depends(get_session),
):
    consulta = select(Movimentacao).order_by(Movimentacao.criado_em.desc())

    if produto_id is not None:
        consulta = consulta.where(Movimentacao.produto_id == produto_id)

    movimentacoes = session.exec(consulta).all()
    return movimentacoes