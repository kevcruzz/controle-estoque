from datetime import datetime, date
from enum import Enum
from typing import Optional
 
from sqlmodel import SQLModel, Field, UniqueConstraint
 
 
class Empresa(SQLModel, table=True):
    """O inquilino (tenant). Cada empresa enxerga apenas os proprios dados."""
 
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True)
    cnpj: Optional[str] = Field(default=None, index=True)
    ativa: bool = Field(default=True)
    # Preferencia da empresa: cobrar lote em toda entrada de mercadoria
    exige_lote: bool = Field(default=False)
    criado_em: datetime = Field(default_factory=datetime.utcnow)
 
 
class Categoria(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("empresa_id", "nome", name="uq_categoria_empresa_nome"),
    )
 
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa_id: int = Field(foreign_key="empresa.id", index=True)
    nome: str = Field(index=True)
 
 
class Produto(SQLModel, table=True):
    # SKU e unico DENTRO da empresa, nao globalmente
    __table_args__ = (
        UniqueConstraint("empresa_id", "sku", name="uq_produto_empresa_sku"),
    )
 
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa_id: int = Field(foreign_key="empresa.id", index=True)
    sku: str = Field(index=True)
    nome: str = Field(index=True)
    unidade: str = Field(default="un")
    estoque_minimo: int = Field(default=0)
    saldo: int = Field(default=0)
    # Marca que ESTE item trabalha com lote, mesmo que a empresa nao exija
    # em geral. O lote em si nao mora aqui: um produto pode ter varios
    # lotes em estoque ao mesmo tempo.
    controla_lote: bool = Field(default=False)
    categoria_id: Optional[int] = Field(default=None, foreign_key="categoria.id")
 
 
class TipoMovimentacao(str, Enum):
    entrada = "entrada"
    saida = "saida"
 
 
class Movimentacao(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa_id: int = Field(foreign_key="empresa.id", index=True)
    produto_id: int = Field(foreign_key="produto.id", index=True)
    tipo: TipoMovimentacao
    quantidade: int
    motivo: Optional[str] = Field(default=None)
    lote: Optional[str] = Field(default=None, index=True)
    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
 
 
class NotaFiscal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa_id: int = Field(foreign_key="empresa.id", index=True)
    numero: str = Field(index=True)
    fornecedor: str
    data_emissao: Optional[date] = Field(default=None)
    valor_total: float = Field(default=0.0)
    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
 
 
class ItemNotaFiscal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa_id: int = Field(foreign_key="empresa.id", index=True)
    nota_fiscal_id: int = Field(foreign_key="notafiscal.id", index=True)
    produto_id: int = Field(foreign_key="produto.id", index=True)
    quantidade: int
    valor_unitario: float
    valor_total: float
    lote: Optional[str] = Field(default=None, index=True)
 
 
# ---------------------------------------------------------------- COMPRAS
 
 
class StatusPedido(str, Enum):
    rascunho = "rascunho"
    aprovado = "aprovado"
    recebido = "recebido"
    cancelado = "cancelado"
 
 
class Fornecedor(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("empresa_id", "nome", name="uq_fornecedor_empresa_nome"),
    )
 
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa_id: int = Field(foreign_key="empresa.id", index=True)
    nome: str = Field(index=True)
    cnpj: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    telefone: Optional[str] = Field(default=None)
    ativo: bool = Field(default=True)
    criado_em: datetime = Field(default_factory=datetime.utcnow)
 
 
class PedidoCompra(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa_id: int = Field(foreign_key="empresa.id", index=True)
    numero: str = Field(index=True)
    fornecedor_id: int = Field(foreign_key="fornecedor.id", index=True)
    status: StatusPedido = Field(default=StatusPedido.rascunho, index=True)
    previsao_entrega: Optional[date] = Field(default=None)
    observacao: Optional[str] = Field(default=None)
    valor_total: float = Field(default=0.0)
    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    aprovado_em: Optional[datetime] = Field(default=None)
    recebido_em: Optional[datetime] = Field(default=None)
 
 
class ItemPedidoCompra(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa_id: int = Field(foreign_key="empresa.id", index=True)
    pedido_id: int = Field(foreign_key="pedidocompra.id", index=True)
    produto_id: int = Field(foreign_key="produto.id", index=True)
    quantidade: int
    valor_unitario: float
    valor_total: float
    # Quanto ja chegou. Permite recebimento parcial.
    quantidade_recebida: int = Field(default=0)
 
 
# --------------------------------------------------------------- PRODUCAO
 
 
class StatusOrdem(str, Enum):
    planejada = "planejada"
    em_producao = "em_producao"
    concluida = "concluida"
    cancelada = "cancelada"
 
 
class FichaTecnica(SQLModel, table=True):
    """Receita de um produto: o que e preciso para fabricar 1 unidade."""
 
    __table_args__ = (
        UniqueConstraint("empresa_id", "produto_id", name="uq_ficha_empresa_produto"),
    )
 
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa_id: int = Field(foreign_key="empresa.id", index=True)
    produto_id: int = Field(foreign_key="produto.id", index=True)
    descricao: Optional[str] = Field(default=None)
    ativa: bool = Field(default=True)
    criado_em: datetime = Field(default_factory=datetime.utcnow)
 
 
class ItemFichaTecnica(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa_id: int = Field(foreign_key="empresa.id", index=True)
    ficha_id: int = Field(foreign_key="fichatecnica.id", index=True)
    insumo_id: int = Field(foreign_key="produto.id", index=True)
    # Quantidade do insumo para UMA unidade do produto final.
    # E float porque receita costuma ter fracao (0.5 kg, 1.25 L).
    quantidade: float
 
 
class OrdemProducao(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa_id: int = Field(foreign_key="empresa.id", index=True)
    numero: str = Field(index=True)
    produto_id: int = Field(foreign_key="produto.id", index=True)
    quantidade: int
    status: StatusOrdem = Field(default=StatusOrdem.planejada, index=True)
    observacao: Optional[str] = Field(default=None)
    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    iniciada_em: Optional[datetime] = Field(default=None)
    concluida_em: Optional[datetime] = Field(default=None)
    # Guarda o custo dos insumos no momento em que a ordem foi iniciada
    custo_insumos: float = Field(default=0.0)
 
 
class ConsumoOrdem(SQLModel, table=True):
    """Registra o que cada ordem realmente consumiu, para custeio e auditoria."""
 
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa_id: int = Field(foreign_key="empresa.id", index=True)
    ordem_id: int = Field(foreign_key="ordemproducao.id", index=True)
    insumo_id: int = Field(foreign_key="produto.id", index=True)
    quantidade: int
    custo_unitario: float = Field(default=0.0)
 
 
class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa_id: int = Field(foreign_key="empresa.id", index=True)
    email: str = Field(index=True, unique=True)
    senha_hash: str
    papel: str = Field(default="leitor")