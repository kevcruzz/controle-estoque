from fastapi import WebSocket


class GerenciadorConexoes:
    def __init__(self):
        self.conexoes: list[WebSocket] = []

    async def conectar(self, websocket: WebSocket):
        await websocket.accept()
        self.conexoes.append(websocket)

    def desconectar(self, websocket: WebSocket):
        if websocket in self.conexoes:
            self.conexoes.remove(websocket)

    async def avisar_todos(self, mensagem: str):
        desconectados = []
        for conexao in self.conexoes:
            try:
                await conexao.send_text(mensagem)
            except Exception:
                desconectados.append(conexao)
        for conexao in desconectados:
            self.desconectar(conexao)


gerenciador = GerenciadorConexoes()

