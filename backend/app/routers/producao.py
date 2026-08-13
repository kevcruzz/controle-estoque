from datetime import datetime
from typing import Optional
 
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, SQLModel, select, update
 
from app.database import get_session_tenant
from app.models import (
    FichaTecnica,
    ItemFichaTecnica,
    OrdemProducao,
    ConsumoOrdem,
    Produto,
    Movimentacao,
    TipoMovimentacao,
    ItemNotaFiscal,
    NotaFiscal,
    StatusOrdem,
)
from app.security import usuario_atual, exigir_papel
from app.tenant import buscar_do_tenant
from app.websocket import gerenciador
 
router = APIRouter(prefix="/producao", tags=["Producao"])
 
 
# ------------------------------------------------------------- schemas
 
 
class ItemFichaCriar(SQLModel):
    insumo_id: int
    quantidade: float
 
 
class FichaCriar(SQLModel):
    produto_id: int
    descricao: Optional[str] = None
    itens: list[ItemFichaCriar]
 
 
class ItemFichaLer(SQLModel):
    id: int
    insumo_id: int
    insumo_nome: str
    quantidade: float
 
 
class FichaLer(SQLModel):
    id: int
    produto_id: int
    produto_nome: str
    descricao: Optional[str] = None
    ativa: bool
    itens: list[ItemFichaLer] = []
 
 
class OrdemCriar(SQLModel):
    numero: str
    produto_id: int
    quantidade: int
    observacao: Optional[str] = None
 
 
class ConsumoLer(SQLModel):
    insumo_id: int
    insumo_nome: str
    quantidade: int
    custo_unitario: float
 
 
class OrdemLer(SQLModel):
    id: int
    numero: str
    produto_id: int
    produto_nome: str
    quantidade: int
    status: StatusOrdem
    observacao: Optional[str] = None
    custo_insumos: float
    criado_em: datetime
    consumos: list[ConsumoLer] = []
 
 
def nome_produto(session: Session, produto_id: int) -> str:
    produto = session.get(Produto, produto_id)
    return produto.nome if produto else "-"
 
 
def montar_ficha(session: Session, ficha: FichaTecnica, itens) -> FichaLer:
    return FichaLer(
        id=ficha.id,
        produto_id=ficha.produto_id,
        produto_nome=nome_produto(session, ficha.produto_id),
        descricao=ficha.descricao,
        ativa=ficha.ativa,
        itens=[
            ItemFichaLer(
                id=i.id,
                insumo_id=i.insumo_id,
                insumo_nome=nome_produto(session, i.insumo_id),
                quantidade=i.quantidade,
            )
            for i in itens
        ],
    )
 
 
def custo_conhecido(session: Session, produto_id: int, empresa_id: int) -> float:
    """
    Ultimo preco de compra do produto, tirado das notas fiscais.
 
    Se o item nunca apareceu numa nota, o custo e desconhecido e retorna 0.
    O custo total da ordem sinaliza isso para quem le.
    """
    item = session.exec(
        select(ItemNotaFiscal)
        .join(NotaFiscal, NotaFiscal.id == ItemNotaFiscal.nota_fiscal_id)
        .where(ItemNotaFiscal.produto_id == produto_id)
        .where(ItemNotaFiscal.empresa_id == empresa_id)
        .order_by(NotaFiscal.criado_em.desc())
    ).first()
    return item.valor_unitario if item else 0.0
 
 
# ---------------------------------------------------------- ficha tecnica
 
 
@router.post("/fichas", response_model=FichaLer)
def criar_ficha(
    dados: FichaCriar,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(exigir_papel("admin")),
):
    empresa_id = usuario["empresa_id"]
 
    produto = buscar_do_tenant(session, Produto, dados.produto_id, empresa_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
 
    if not dados.itens:
        raise HTTPException(status_code=400, detail="A ficha precisa de pelo menos um insumo")
 
    existente = session.exec(
        select(FichaTecnica)
        .where(FichaTecnica.produto_id == dados.produto_id)
        .where(FichaTecnica.empresa_id == empresa_id)
    ).first()
    if existente is not None:
        raise HTTPException(
            status_code=400, detail="Este produto já possui ficha técnica"
        )
 
    for item in dados.itens:
        if item.quantidade <= 0:
            raise HTTPException(
                status_code=400, detail="A quantidade de cada insumo deve ser maior que zero"
            )
        if item.insumo_id == dados.produto_id:
            raise HTTPException(
                status_code=400,
                detail="Um produto não pode ser insumo de si mesmo",
            )
        if buscar_do_tenant(session, Produto, item.insumo_id, empresa_id) is None:
            raise HTTPException(
                status_code=400, detail=f"Insumo não cadastrado (id {item.insumo_id})"
            )
 
    ficha = FichaTecnica(
        empresa_id=empresa_id,
        produto_id=dados.produto_id,
        descricao=dados.descricao,
    )
    session.add(ficha)
    session.flush()
 
    criados = []
    for item in dados.itens:
        registro = ItemFichaTecnica(
            empresa_id=empresa_id,
            ficha_id=ficha.id,
            insumo_id=item.insumo_id,
            quantidade=item.quantidade,
        )
        session.add(registro)
        criados.append(registro)
 
    session.commit()
    session.refresh(ficha)
    for registro in criados:
        session.refresh(registro)
 
    return montar_ficha(session, ficha, criados)
 
 
@router.get("/fichas", response_model=list[FichaLer])
def listar_fichas(
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(usuario_atual),
):
    empresa_id = usuario["empresa_id"]
    resposta = []
    for ficha in session.exec(
        select(FichaTecnica).where(FichaTecnica.empresa_id == empresa_id)
    ).all():
        itens = session.exec(
            select(ItemFichaTecnica)
            .where(ItemFichaTecnica.ficha_id == ficha.id)
            .where(ItemFichaTecnica.empresa_id == empresa_id)
        ).all()
        resposta.append(montar_ficha(session, ficha, itens))
    return resposta
 
 
# ------------------------------------------------------ ordens de producao
 
 
@router.post("/ordens", response_model=OrdemLer)
def criar_ordem(
    dados: OrdemCriar,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(exigir_papel("admin", "operador")),
):
    empresa_id = usuario["empresa_id"]
 
    if dados.quantidade <= 0:
        raise HTTPException(status_code=400, detail="A quantidade deve ser maior que zero")
 
    produto = buscar_do_tenant(session, Produto, dados.produto_id, empresa_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
 
    ficha = session.exec(
        select(FichaTecnica)
        .where(FichaTecnica.produto_id == dados.produto_id)
        .where(FichaTecnica.empresa_id == empresa_id)
    ).first()
    if ficha is None:
        raise HTTPException(
            status_code=400,
            detail=f"O produto '{produto.nome}' não possui ficha técnica. Cadastre-a antes de abrir a ordem.",
        )
 
    ordem = OrdemProducao(
        empresa_id=empresa_id,
        numero=dados.numero.strip(),
        produto_id=dados.produto_id,
        quantidade=dados.quantidade,
        observacao=dados.observacao,
        status=StatusOrdem.planejada,
    )
    session.add(ordem)
    session.commit()
    session.refresh(ordem)
 
    return OrdemLer(
        id=ordem.id,
        numero=ordem.numero,
        produto_id=ordem.produto_id,
        produto_nome=produto.nome,
        quantidade=ordem.quantidade,
        status=ordem.status,
        observacao=ordem.observacao,
        custo_insumos=ordem.custo_insumos,
        criado_em=ordem.criado_em,
    )
 
 
@router.post("/ordens/{ordem_id}/concluir", response_model=OrdemLer)
async def concluir_ordem(
    ordem_id: int,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(exigir_papel("admin", "operador")),
):
    """
    Conclui a ordem: baixa os insumos e da entrada no produto acabado.
 
    Tudo acontece numa transacao: ou o estoque inteiro e ajustado, ou nada e.
    Se faltar qualquer insumo, a ordem nao e concluida.
    """
    empresa_id = usuario["empresa_id"]
 
    ordem = buscar_do_tenant(session, OrdemProducao, ordem_id, empresa_id)
    if ordem is None:
        raise HTTPException(status_code=404, detail="Ordem não encontrada")
 
    if ordem.status == StatusOrdem.concluida:
        raise HTTPException(status_code=400, detail="Esta ordem já foi concluída")
    if ordem.status == StatusOrdem.cancelada:
        raise HTTPException(status_code=400, detail="Esta ordem foi cancelada")
 
    ficha = session.exec(
        select(FichaTecnica)
        .where(FichaTecnica.produto_id == ordem.produto_id)
        .where(FichaTecnica.empresa_id == empresa_id)
    ).first()
    if ficha is None:
        raise HTTPException(status_code=400, detail="Ficha técnica não encontrada")
 
    itens_ficha = session.exec(
        select(ItemFichaTecnica)
        .where(ItemFichaTecnica.ficha_id == ficha.id)
        .where(ItemFichaTecnica.empresa_id == empresa_id)
    ).all()
 
    # 1) Confere se ha saldo de TODOS os insumos antes de baixar qualquer um
    necessario = []
    faltantes = []
    for item in itens_ficha:
        insumo = buscar_do_tenant(session, Produto, item.insumo_id, empresa_id)
        if insumo is None:
            raise HTTPException(
                status_code=400, detail=f"Insumo id {item.insumo_id} não encontrado"
            )
 
        # Arredonda para cima: nao da para consumir fracao de unidade
        quantidade = int(-(-item.quantidade * ordem.quantidade // 1))
        necessario.append((insumo, quantidade))
 
        if insumo.saldo < quantidade:
            faltantes.append(
                f"{insumo.nome} (precisa {quantidade}, tem {insumo.saldo})"
            )
 
    if faltantes:
        raise HTTPException(
            status_code=400,
            detail="Estoque insuficiente para produzir: " + "; ".join(faltantes),
        )
 
    # 2) Baixa os insumos e registra o consumo
    custo_total = 0.0
    for insumo, quantidade in necessario:
        session.exec(
            update(Produto)
            .where(Produto.id == insumo.id)
            .where(Produto.empresa_id == empresa_id)
            .values(saldo=Produto.saldo - quantidade)
        )
        session.add(
            Movimentacao(
                empresa_id=empresa_id,
                produto_id=insumo.id,
                tipo=TipoMovimentacao.saida,
                quantidade=quantidade,
                motivo=f"Consumo pela OP {ordem.numero}",
            )
        )
 
        custo_unitario = custo_conhecido(session, insumo.id, empresa_id)
        custo_total += custo_unitario * quantidade
 
        session.add(
            ConsumoOrdem(
                empresa_id=empresa_id,
                ordem_id=ordem.id,
                insumo_id=insumo.id,
                quantidade=quantidade,
                custo_unitario=custo_unitario,
            )
        )
 
    # 3) Da entrada no produto acabado
    session.exec(
        update(Produto)
        .where(Produto.id == ordem.produto_id)
        .where(Produto.empresa_id == empresa_id)
        .values(saldo=Produto.saldo + ordem.quantidade)
    )
    session.add(
        Movimentacao(
            empresa_id=empresa_id,
            produto_id=ordem.produto_id,
            tipo=TipoMovimentacao.entrada,
            quantidade=ordem.quantidade,
            motivo=f"Produção pela OP {ordem.numero}",
        )
    )
 
    ordem.status = StatusOrdem.concluida
    ordem.concluida_em = datetime.utcnow()
    ordem.custo_insumos = custo_total
    session.add(ordem)
 
    session.commit()
    session.refresh(ordem)
 
    await gerenciador.avisar_todos("estoque_atualizado")
 
    consumos = session.exec(
        select(ConsumoOrdem)
        .where(ConsumoOrdem.ordem_id == ordem.id)
        .where(ConsumoOrdem.empresa_id == empresa_id)
    ).all()
 
    return OrdemLer(
        id=ordem.id,
        numero=ordem.numero,
        produto_id=ordem.produto_id,
        produto_nome=nome_produto(session, ordem.produto_id),
        quantidade=ordem.quantidade,
        status=ordem.status,
        observacao=ordem.observacao,
        custo_insumos=ordem.custo_insumos,
        criado_em=ordem.criado_em,
        consumos=[
            ConsumoLer(
                insumo_id=c.insumo_id,
                insumo_nome=nome_produto(session, c.insumo_id),
                quantidade=c.quantidade,
                custo_unitario=c.custo_unitario,
            )
            for c in consumos
        ],
    )
 
 
@router.get("/ordens", response_model=list[OrdemLer])
def listar_ordens(
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(usuario_atual),
):
    empresa_id = usuario["empresa_id"]
    resposta = []
    for ordem in session.exec(
        select(OrdemProducao)
        .where(OrdemProducao.empresa_id == empresa_id)
        .order_by(OrdemProducao.criado_em.desc())
    ).all():
        consumos = session.exec(
            select(ConsumoOrdem)
            .where(ConsumoOrdem.ordem_id == ordem.id)
            .where(ConsumoOrdem.empresa_id == empresa_id)
        ).all()
        resposta.append(
            OrdemLer(
                id=ordem.id,
                numero=ordem.numero,
                produto_id=ordem.produto_id,
                produto_nome=nome_produto(session, ordem.produto_id),
                quantidade=ordem.quantidade,
                status=ordem.status,
                observacao=ordem.observacao,
                custo_insumos=ordem.custo_insumos,
                criado_em=ordem.criado_em,
                consumos=[
                    ConsumoLer(
                        insumo_id=c.insumo_id,
                        insumo_nome=nome_produto(session, c.insumo_id),
                        quantidade=c.quantidade,
                        custo_unitario=c.custo_unitario,
                    )
                    for c in consumos
                ],
            )
        )
    return resposta