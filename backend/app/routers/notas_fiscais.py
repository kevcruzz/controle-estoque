from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, update

from app.database import get_session_tenant
from app.models import (
    NotaFiscal,
    ItemNotaFiscal,
    Produto,
    Movimentacao,
    TipoMovimentacao,
    Empresa,
)
from app.schemas import NotaFiscalCriar, NotaFiscalLer, ItemNotaFiscalLer
from app.security import usuario_atual, exigir_papel
from app.tenant import buscar_do_tenant
from app.websocket import gerenciador

router = APIRouter(prefix="/notas-fiscais", tags=["Notas Fiscais"])


def montar_resposta(nota: NotaFiscal, itens: list[ItemNotaFiscal]) -> NotaFiscalLer:
    return NotaFiscalLer(
        id=nota.id,
        numero=nota.numero,
        fornecedor=nota.fornecedor,
        data_emissao=nota.data_emissao,
        valor_total=nota.valor_total,
        criado_em=nota.criado_em,
        itens=[
            ItemNotaFiscalLer(
                id=i.id,
                produto_id=i.produto_id,
                quantidade=i.quantidade,
                valor_unitario=i.valor_unitario,
                valor_total=i.valor_total,
                lote=i.lote,
            )
            for i in itens
        ],
    )


@router.post("/", response_model=NotaFiscalLer)
async def lancar_nota_fiscal(
    dados: NotaFiscalCriar,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(exigir_papel("admin", "operador")),
):
    empresa_id = usuario["empresa_id"]

    if not dados.numero.strip():
        raise HTTPException(status_code=400, detail="O número da nota é obrigatório")
    if not dados.fornecedor.strip():
        raise HTTPException(status_code=400, detail="O fornecedor é obrigatório")
    if not dados.itens:
        raise HTTPException(status_code=400, detail="A nota precisa de pelo menos um item")

    empresa = session.get(Empresa, empresa_id)
    empresa_exige_lote = empresa is not None and empresa.exige_lote

    # Valida TODOS os itens antes de gravar qualquer coisa (ou tudo, ou nada)
    faltando = []
    sem_lote = []
    for item in dados.itens:
        if item.quantidade <= 0:
            raise HTTPException(
                status_code=400,
                detail="A quantidade de cada item deve ser maior que zero",
            )
        if item.valor_unitario < 0:
            raise HTTPException(
                status_code=400,
                detail="O valor unitário não pode ser negativo",
            )

        produto = buscar_do_tenant(session, Produto, item.produto_id, empresa_id)
        if produto is None:
            faltando.append(item.produto_id)
            continue

        # O lote e cobrado quando a empresa exige em geral, ou quando aquele
        # produto especifico trabalha com lote.
        precisa_lote = empresa_exige_lote or produto.controla_lote
        if precisa_lote and not (item.lote or "").strip():
            sem_lote.append(produto.nome)

    if faltando:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Produtos não cadastrados (ids: {faltando}). "
                "Cadastre-os antes de lançar a nota."
            ),
        )

    if sem_lote:
        raise HTTPException(
            status_code=400,
            detail=("Informe o lote destes itens: " + ", ".join(sem_lote)),
        )

    nota = NotaFiscal(
        empresa_id=empresa_id,
        numero=dados.numero,
        fornecedor=dados.fornecedor,
        data_emissao=dados.data_emissao,
        valor_total=0.0,
    )
    session.add(nota)
    session.flush()

    total_nota = 0.0
    itens_criados = []
    for item in dados.itens:
        total_item = item.quantidade * item.valor_unitario
        total_nota += total_item

        registro = ItemNotaFiscal(
            empresa_id=empresa_id,
            nota_fiscal_id=nota.id,
            produto_id=item.produto_id,
            quantidade=item.quantidade,
            valor_unitario=item.valor_unitario,
            valor_total=total_item,
            lote=(item.lote or "").strip() or None,
        )
        session.add(registro)
        itens_criados.append(registro)

        # Soma a quantidade comprada ao saldo do produto
        session.exec(
            update(Produto)
            .where(Produto.id == item.produto_id)
            .where(Produto.empresa_id == empresa_id)
            .values(saldo=Produto.saldo + item.quantidade)
        )

        # Registra a entrada no ledger de movimentações
        session.add(
            Movimentacao(
                empresa_id=empresa_id,
                produto_id=item.produto_id,
                tipo=TipoMovimentacao.entrada,
                quantidade=item.quantidade,
                motivo=f"Entrada por NF {dados.numero}",
                lote=(item.lote or "").strip() or None,
            )
        )

    nota.valor_total = total_nota
    session.add(nota)

    session.commit()
    session.refresh(nota)
    for registro in itens_criados:
        session.refresh(registro)

    await gerenciador.avisar_todos("estoque_atualizado")

    return montar_resposta(nota, itens_criados)


@router.get("/", response_model=list[NotaFiscalLer])
def listar_notas(
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(usuario_atual),
):
    notas = session.exec(
        select(NotaFiscal)
        .where(NotaFiscal.empresa_id == usuario["empresa_id"])
        .order_by(NotaFiscal.criado_em.desc())
    ).all()

    resposta = []
    for nota in notas:
        itens = session.exec(
            select(ItemNotaFiscal)
            .where(ItemNotaFiscal.nota_fiscal_id == nota.id)
            .where(ItemNotaFiscal.empresa_id == usuario["empresa_id"])
        ).all()
        resposta.append(montar_resposta(nota, itens))
    return resposta


@router.get("/{nota_id}", response_model=NotaFiscalLer)
def obter_nota(
    nota_id: int,
    session: Session = Depends(get_session_tenant),
    usuario: dict = Depends(usuario_atual),
):
    nota = buscar_do_tenant(session, NotaFiscal, nota_id, usuario["empresa_id"])
    if nota is None:
        raise HTTPException(status_code=404, detail="Nota fiscal não encontrada")

    itens = session.exec(
        select(ItemNotaFiscal)
        .where(ItemNotaFiscal.nota_fiscal_id == nota_id)
        .where(ItemNotaFiscal.empresa_id == usuario["empresa_id"])
    ).all()
    return montar_resposta(nota, itens)