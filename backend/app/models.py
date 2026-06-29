from datetime import datetime
from enum import Enum
from typing import Optional 

from sqlmodel import SQLModel, Field

class Categoria(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True)


class Produto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(index=True, unique=True)
    nome: str = Field(index=True)
    unidade: str = Field(index=True)
    estoque_minimo: int = Field(default=0)
    saldo: int = Field(default=0)
    categoria_id: Optional[int] = Field(default=None, foreign_key="categoria.id")


class TipoMovimentacao(str, Enum):
    entrada = "entrada"
    saida = "saida"


class Movimentacao(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    produto_id: int = Field(foreign_key="produto.id", index=True)
    tipo : TipoMovimentacao 
    quantidade: int
    motivo: Optional[str] = Field(default=None)
    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    