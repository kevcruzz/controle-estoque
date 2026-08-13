import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
 
load_dotenv()
 
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlmodel import Session, select
 
from app.database import criar_tabelas, aplicar_rls, engine, USA_POSTGRES
from app import models
from app.models import Usuario, Empresa
from app.security import gerar_hash_senha
from app.routers import (
    categorias,
    produtos,
    movimentacoes,
    auth,
    notas_fiscais,
    empresas,
    compras,
    producao,
)
from app.websocket import gerenciador
 
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    criar_tabelas()
    aplicar_rls()
 
    # Empresa e admin de demonstracao, apenas se o banco estiver vazio
    with Session(engine) as session:
        if session.exec(select(Empresa)).first() is None:
            demo = Empresa(nome="Empresa Demonstracao")
            session.add(demo)
            session.flush()
 
            if USA_POSTGRES:
                session.exec(
                    text("SELECT set_config('app.empresa_id', :valor, true)").bindparams(
                        valor=str(demo.id)
                    )
                )
 
            session.add(
                Usuario(
                    empresa_id=demo.id,
                    email="admin@estoque.com",
                    senha_hash=gerar_hash_senha("admin123"),
                    papel="admin",
                )
            )
            session.commit()
    yield
 
 
app = FastAPI(title="KFuture ERP", lifespan=lifespan)
 
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
app.include_router(empresas.router)
app.include_router(compras.router)
app.include_router(producao.router)
 
 
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