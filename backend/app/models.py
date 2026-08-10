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
 
 
class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa_id: int = Field(foreign_key="empresa.id", index=True)
    email: str = Field(index=True, unique=True)
    senha_hash: str
    papel: str = Field(default="leitor")