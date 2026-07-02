from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# ATENÇÃO: em produção, esta chave deve vir de uma variável de ambiente!
CHAVE_SECRETA = "troque-esta-chave-por-uma-bem-secreta-e-aleatoria"
ALGORITMO = "HS256"
EXPIRA_MINUTOS = 60 * 8  # 8 horas

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), hash_armazenado.encode("utf-8"))


def criar_token(email: str, papel: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=EXPIRA_MINUTOS)
    payload = {"sub": email, "papel": papel, "exp": expira}
    return jwt.encode(payload, CHAVE_SECRETA, algorithm=ALGORITMO)


def usuario_atual(token: str = Depends(oauth2_scheme)) -> dict:
    excecao = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, CHAVE_SECRETA, algorithms=[ALGORITMO])
    except jwt.PyJWTError:
        raise excecao
    email = payload.get("sub")
    if email is None:
        raise excecao
    return {"email": email, "papel": payload.get("papel")}


def exigir_papel(*papeis_permitidos: str):
    def verificador(usuario: dict = Depends(usuario_atual)) -> dict:
        if usuario["papel"] not in papeis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para esta ação",
            )
        return usuario
    return verificador