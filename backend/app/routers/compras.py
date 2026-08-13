from datetime import datetime
from typing import Optional
 
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, SQLModel, select
 
from app.database import get_session_tenant
from app.models import (
    Fornecedor,
    PedidoCompra,
    ItemPedidoCompra,
    Produto,
    StatusPedido,
)
from app.security import usuario_atual, exigir_papel
from app.tenant import buscar_do_tenant
 
router = APIRouter(prefix="/compras", tags=["Compras"])
 
 
# ------------------------------------------------------------- schemas
 
 
class FornecedorCriar(SQLModel):
    nome: str
    cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
 
 
class FornecedorLer(SQLModel):
    id: int
    nome: str
    cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    ativo: bool
 
 
class ItemPedidoCriar(SQLModel):
    produto_id: int
    quantidade: int
    valor_unitario: float
 
 
class PedidoCriar(SQLModel):
    numero: str
    fornecedor_id: int
    previsao_entrega: Optional[str] = None
    observacao: Optional[str] = None
    itens: list[ItemPedidoCriar]
 
 
class ItemPedidoLer(SQLModel):
    id: int
    produto_id: int
    quantidade: int
    valor_unitario: float
    valor_total: float
    quantidade_recebida: int
 
 
class PedidoLer(SQLModel):
    id: int
    numero: str
    fornecedor_id: int
    fornecedor_nome: str
    status: StatusPedido
    previsao_entrega: Optional[str] = None
    observacao: Optional[str] = None
    valor_total: float
    criado_em: datetime
    itens: list[ItemPedidoLer] = []
 
 
def montar_pedido(
    session: Session, pedido: PedidoCompra, itens: list[ItemPedidoCompra]
) -> PedidoLer:
    fornecedor = session.get(Fornecedor, pedido.fornecedor_id)
    return PedidoLer(
        id=pedido.id,
        numero=pedido.numero,
        fornecedor_id=pedido.fornecedor_id,
        fornecedor_nome=fornecedor.nome if fornecedor else "-",
        status=pedido.status,
        previsao_entrega=(
            pedido.previsao_entrega.isoformat() if pedido.previsao_entrega else None
        ),
        observacao=pedido.observacao,
        valor_total=pedido.valor_total,
        criado_em=pedido.criado_em,
        itens=[
            ItemPedidoLer(
                id=i.id,
                produto_id=i.produto_id,
                quantidade=i.quantidade,
                valor_unitario=i.valor_unitario,
                valor_total=i.valor_total,
                quantidade_recebida=i.quantidade_recebida,
            )
            for i in itens
        ],
    )
 
 
# --------------------------------------------------------- fornecedores
 
 
@router.post("/fornecedores", response_model=FornecedorLer)
def criar_fornecedor(
    dados: FornecedorCriar,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(exigir_papel("admin", "operador")),
):
    empresa_id = usuario["empresa_id"]
 
    if not dados.nome.strip():
        raise HTTPException(status_code=400, detail="O nome do fornecedor é obrigatório")
 
    existente = session.exec(
        select(Fornecedor)
        .where(Fornecedor.nome == dados.nome.strip())
        .where(Fornecedor.empresa_id == empresa_id)
    ).first()
    if existente is not None:
        raise HTTPException(status_code=400, detail="Já existe um fornecedor com esse nome")
 
    fornecedor = Fornecedor(
        empresa_id=empresa_id,
        nome=dados.nome.strip(),
        cnpj=dados.cnpj,
        email=dados.email,
        telefone=dados.telefone,
    )
    session.add(fornecedor)
    session.commit()
    session.refresh(fornecedor)
    return fornecedor
 
 
@router.get("/fornecedores", response_model=list[FornecedorLer])
def listar_fornecedores(
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(usuario_atual),
):
    return session.exec(
        select(Fornecedor)
        .where(Fornecedor.empresa_id == usuario["empresa_id"])
        .order_by(Fornecedor.nome)
    ).all()
 
 
# --------------------------------------------------------------- pedidos
 
 
@router.post("/pedidos", response_model=PedidoLer)
def criar_pedido(
    dados: PedidoCriar,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(exigir_papel("admin", "operador")),
):
    empresa_id = usuario["empresa_id"]
 
    if not dados.numero.strip():
        raise HTTPException(status_code=400, detail="O número do pedido é obrigatório")
    if not dados.itens:
        raise HTTPException(status_code=400, detail="O pedido precisa de pelo menos um item")
 
    fornecedor = buscar_do_tenant(session, Fornecedor, dados.fornecedor_id, empresa_id)
    if fornecedor is None:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
 
    faltando = []
    for item in dados.itens:
        if item.quantidade <= 0:
            raise HTTPException(
                status_code=400, detail="A quantidade de cada item deve ser maior que zero"
            )
        if buscar_do_tenant(session, Produto, item.produto_id, empresa_id) is None:
            faltando.append(item.produto_id)
 
    if faltando:
        raise HTTPException(
            status_code=400,
            detail=f"Produtos não cadastrados (ids: {faltando}).",
        )
 
    previsao = None
    if dados.previsao_entrega:
        try:
            previsao = datetime.fromisoformat(dados.previsao_entrega).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Data de previsão inválida")
 
    pedido = PedidoCompra(
        empresa_id=empresa_id,
        numero=dados.numero.strip(),
        fornecedor_id=dados.fornecedor_id,
        previsao_entrega=previsao,
        observacao=dados.observacao,
        status=StatusPedido.rascunho,
    )
    session.add(pedido)
    session.flush()
 
    total = 0.0
    criados = []
    for item in dados.itens:
        subtotal = item.quantidade * item.valor_unitario
        total += subtotal
        registro = ItemPedidoCompra(
            empresa_id=empresa_id,
            pedido_id=pedido.id,
            produto_id=item.produto_id,
            quantidade=item.quantidade,
            valor_unitario=item.valor_unitario,
            valor_total=subtotal,
        )
        session.add(registro)
        criados.append(registro)
 
    pedido.valor_total = total
    session.add(pedido)
    session.commit()
    session.refresh(pedido)
    for registro in criados:
        session.refresh(registro)
 
    return montar_pedido(session, pedido, criados)
 
 
@router.get("/pedidos", response_model=list[PedidoLer])
def listar_pedidos(
    status: Optional[StatusPedido] = None,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(usuario_atual),
):
    empresa_id = usuario["empresa_id"]
    consulta = (
        select(PedidoCompra)
        .where(PedidoCompra.empresa_id == empresa_id)
        .order_by(PedidoCompra.criado_em.desc())
    )
    if status is not None:
        consulta = consulta.where(PedidoCompra.status == status)
 
    resposta = []
    for pedido in session.exec(consulta).all():
        itens = session.exec(
            select(ItemPedidoCompra)
            .where(ItemPedidoCompra.pedido_id == pedido.id)
            .where(ItemPedidoCompra.empresa_id == empresa_id)
        ).all()
        resposta.append(montar_pedido(session, pedido, itens))
    return resposta
 
 
@router.patch("/pedidos/{pedido_id}/aprovar", response_model=PedidoLer)
def aprovar_pedido(
    pedido_id: int,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(exigir_papel("admin")),
):
    """
    Aprova o pedido. Apenas admin aprova: e o ponto de controle de gasto.
 
    Aprovar NAO mexe no estoque. A mercadoria so entra quando chega, pelo
    lancamento da nota fiscal.
    """
    empresa_id = usuario["empresa_id"]
    pedido = buscar_do_tenant(session, PedidoCompra, pedido_id, empresa_id)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
 
    if pedido.status != StatusPedido.rascunho:
        raise HTTPException(
            status_code=400,
            detail=f"Só é possível aprovar um pedido em rascunho (atual: {pedido.status.value})",
        )
 
    pedido.status = StatusPedido.aprovado
    pedido.aprovado_em = datetime.utcnow()
    session.add(pedido)
    session.commit()
    session.refresh(pedido)
 
    itens = session.exec(
        select(ItemPedidoCompra)
        .where(ItemPedidoCompra.pedido_id == pedido_id)
        .where(ItemPedidoCompra.empresa_id == empresa_id)
    ).all()
    return montar_pedido(session, pedido, itens)
 
 
@router.patch("/pedidos/{pedido_id}/cancelar", response_model=PedidoLer)
def cancelar_pedido(
    pedido_id: int,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(exigir_papel("admin")),
):
    empresa_id = usuario["empresa_id"]
    pedido = buscar_do_tenant(session, PedidoCompra, pedido_id, empresa_id)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
 
    if pedido.status == StatusPedido.recebido:
        raise HTTPException(
            status_code=400, detail="Um pedido já recebido não pode ser cancelado"
        )
 
    pedido.status = StatusPedido.cancelado
    session.add(pedido)
    session.commit()
    session.refresh(pedido)
 
    itens = session.exec(
        select(ItemPedidoCompra)
        .where(ItemPedidoCompra.pedido_id == pedido_id)
        .where(ItemPedidoCompra.empresa_id == empresa_id)
    ).all()
    return montar_pedido(session, pedido, itens)