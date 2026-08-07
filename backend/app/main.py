
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
 
load_dotenv()
 
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
 
from app.database import criar_tabelas, engine
from app import models
from app.models import Usuario
from app.security import gerar_hash_senha
from app.routers import categorias, produtos, movimentacoes, auth, notas_fiscais
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
 
origens = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
app.include_router(auth.router)
app.include_router(categorias.router)
app.include_router(produtos.router)
app.include_router(movimentacoes.router)
app.include_router(notas_fiscais.router)
 
 
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