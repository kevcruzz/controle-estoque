from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models import TipoMovimentacao


class CategoriaCriar(SQLModel):
    nome: str


class CategoriaLer(SQLModel):
    id: int
    nome: str


class ProdutoCriar(SQLModel):
    sku: str
    nome: str
    unidade: str = "un"
    estoque_minimo: int = 0
    categoria_id: Optional[int] = None


class ProdutoLer(SQLModel):
    id: int
    sku: str
    nome: str
    unidade: str
    estoque_minimo: int
    saldo: int 
    categoria_id: Optional[int]


class MovimentacaoCriar(SQLModel):
    produto_id: int
    tipo: TipoMovimentacao
    quantidade: int
    motivo: Optional[str] = None


class MovimentacaoLer(SQLModel):
    id: int
    produto_id: int
    tipo: TipoMovimentacao
    quantidade: int
    motivo: Optional[str]
    criado_em: datetime
