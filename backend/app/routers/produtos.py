from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Produto, Categoria
from app.schemas import ProdutoCriar, ProdutoLer

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.post("/", response_model=ProdutoLer)
def criar_produto(dados: ProdutoCriar, session: Session = Depends(get_session)):
    if dados.categoria_id is not None:
        categoria = session.get(Categoria, dados.categoria_id)
        if categoria is None:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    produto = Produto(
        sku=dados.sku,
        nome=dados.nome,
        unidade=dados.unidade,
        estoque_minimo=dados.estoque_minimo,
        categoria_id=dados.categoria_id,
    )
    session.add(produto)
    session.commit()
    session.refresh(produto)
    return produto


@router.get("/", response_model=list[ProdutoLer])
def listar_produtos(
    nome: Optional[str] = None,
    categoria_id: Optional[int] = None,
    session: Session = Depends(get_session),
):
    consulta = select(Produto)

    if nome is not None:
        consulta = consulta.where(Produto.nome.contains(nome))

    if categoria_id is not None:
        consulta = consulta.where(Produto.categoria_id == categoria_id)

    produtos = session.exec(consulta).all()
    return produtos