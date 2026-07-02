from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Produto, Categoria, Movimentacao
from app.schemas import ProdutoCriar, ProdutoLer
from app.security import usuario_atual, exigir_papel
from app.websocket import gerenciador

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.post("/", response_model=ProdutoLer)
async def criar_produto(
    dados: ProdutoCriar,
    session: Session = Depends(get_session),
    usuario: dict = Depends(exigir_papel("admin")),
):
    if not dados.sku.strip():
        raise HTTPException(status_code=400, detail="O SKU é obrigatório")
    if not dados.nome.strip():
        raise HTTPException(status_code=400, detail="O nome é obrigatório")

    existente = session.exec(select(Produto).where(Produto.sku == dados.sku)).first()
    if existente is not None:
        raise HTTPException(status_code=400, detail="Já existe um produto com esse SKU")

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

    await gerenciador.avisar_todos("estoque_atualizado")

    return produto


@router.get("/", response_model=list[ProdutoLer])
def listar_produtos(
    nome: Optional[str] = None,
    categoria_id: Optional[int] = None,
    session: Session = Depends(get_session),
    usuario: dict = Depends(usuario_atual),
):
    consulta = select(Produto)

    if nome is not None:
        consulta = consulta.where(Produto.nome.contains(nome))

    if categoria_id is not None:
        consulta = consulta.where(Produto.categoria_id == categoria_id)

    produtos = session.exec(consulta).all()
    return produtos


@router.delete("/{produto_id}")
async def deletar_produto(
    produto_id: int,
    session: Session = Depends(get_session),
    usuario: dict = Depends(exigir_papel("admin")),
):
    produto = session.get(Produto, produto_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    movimentacoes = session.exec(
        select(Movimentacao).where(Movimentacao.produto_id == produto_id)
    ).all()
    for mov in movimentacoes:
        session.delete(mov)

    session.delete(produto)
    session.commit()

    await gerenciador.avisar_todos("estoque_atualizado")
    
    return {"ok": True, "mensagem": "Produto excluído"}