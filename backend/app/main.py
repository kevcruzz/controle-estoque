from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.database import criar_tabelas, engine
from app import models
from app.models import Usuario
from app.security import gerar_hash_senha
from app.routers import categorias, produtos, movimentacoes, auth
from app.websocket import gerenciador


@asynccontextmanager
async def lifespan(app: FastAPI):
    criar_tabelas()
    # Cria um usuário admin inicial, se ainda não houver nenhum usuário
    with Session(engine) as session:
        existe = session.exec(select(Usuario)).first()
        if existe is None:
            admin = Usuario(
                email="admin@estoque.com",
                senha_hash=gerar_hash_senha("admin123"),
                papel="admin",
            )
            session.add(admin)
            session.commit()
    yield


app = FastAPI(title="Controle de Estoque", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categorias.router)
app.include_router(produtos.router)
app.include_router(movimentacoes.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await gerenciador.conectar(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        gerenciador.desconectar(websocket)