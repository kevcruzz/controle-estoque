from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, SQLModel, select

from app.database import get_session
from app.models import Usuario
from app.security import verificar_senha, criar_token, usuario_atual

router = APIRouter(prefix="/auth", tags=["Autenticação"])


class TokenResposta(SQLModel):
    access_token: str
    token_type: str = "bearer"
    papel: str


@router.post("/login", response_model=TokenResposta)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    usuario = session.exec(
        select(Usuario).where(Usuario.email == form_data.username)
    ).first()

    if usuario is None or not verificar_senha(form_data.password, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")

    token = criar_token(usuario.email, usuario.papel)
    return TokenResposta(access_token=token, papel=usuario.papel)


@router.get("/me")
def quem_sou_eu(usuario: dict = Depends(usuario_atual)):
    return usuario