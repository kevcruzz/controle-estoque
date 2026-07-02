from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import Categoria
from app.schemas import CategoriaCriar, CategoriaLer
from app.security import usuario_atual, exigir_papel

router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.post("/", response_model=CategoriaLer)
def criar_categoria(
    dados: CategoriaCriar,
    session: Session = Depends(get_session),
    usuario: dict = Depends(exigir_papel("admin")),
):
    categoria = Categoria(nome=dados.nome)
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return categoria


@router.get("/", response_model=list[CategoriaLer])
def listar_categorias(
    session: Session = Depends(get_session),
    usuario: dict = Depends(usuario_atual),
):
    categorias = session.exec(select(Categoria)).all()
    return categorias