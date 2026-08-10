from typing import Optional
 
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
 
from app.database import get_session_tenant
from app.models import Produto, Categoria, Movimentacao
from app.schemas import ProdutoCriar, ProdutoLer
from app.security import usuario_atual, exigir_papel
from app.tenant import buscar_do_tenant
from app.websocket import gerenciador
 
router = APIRouter(prefix="/produtos", tags=["Produtos"])
 
 
@router.post("/", response_model=ProdutoLer)
async def criar_produto(
    dados: ProdutoCriar,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(exigir_papel("admin")),
):
    empresa_id = usuario["empresa_id"]
 
    if not dados.sku.strip():
        raise HTTPException(status_code=400, detail="O SKU e obrigatorio")
    if not dados.nome.strip():
        raise HTTPException(status_code=400, detail="O nome e obrigatorio")
 
    # SKU duplicado e verificado apenas dentro da propria empresa
    existente = session.exec(
        select(Produto)
        .where(Produto.sku == dados.sku)
        .where(Produto.empresa_id == empresa_id)
    ).first()
    if existente is not None:
        raise HTTPException(status_code=400, detail="Ja existe um produto com esse SKU")
 
    if dados.categoria_id is not None:
        categoria = buscar_do_tenant(session, Categoria, dados.categoria_id, empresa_id)
        if categoria is None:
            raise HTTPException(status_code=404, detail="Categoria nao encontrada")
 
    produto = Produto(
        empresa_id=empresa_id,
        sku=dados.sku,
        nome=dados.nome,
        unidade=dados.unidade,
        estoque_minimo=dados.estoque_minimo,
        controla_lote=dados.controla_lote,
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
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(usuario_atual),
):
    consulta = select(Produto).where(Produto.empresa_id == usuario["empresa_id"])
 
    if nome is not None:
        consulta = consulta.where(Produto.nome.contains(nome))
 
    if categoria_id is not None:
        consulta = consulta.where(Produto.categoria_id == categoria_id)
 
    return session.exec(consulta).all()
 
 
@router.delete("/{produto_id}")
async def deletar_produto(
    produto_id: int,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(exigir_papel("admin")),
):
    empresa_id = usuario["empresa_id"]
 
    produto = buscar_do_tenant(session, Produto, produto_id, empresa_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
 
    movimentacoes = session.exec(
        select(Movimentacao)
        .where(Movimentacao.produto_id == produto_id)
        .where(Movimentacao.empresa_id == empresa_id)
    ).all()
    for mov in movimentacoes:
        session.delete(mov)
 
    session.delete(produto)
    session.commit()
 
    await gerenciador.avisar_todos("estoque_atualizado")
 
    return {"ok": True, "mensagem": "Produto excluido"}