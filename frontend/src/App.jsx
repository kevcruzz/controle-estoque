import { useState, useEffect } from "react";
import "./App.css";
import Login from "./Login";
import Graficos from "./Graficos";

const API = "http://127.0.0.1:8000";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [papel, setPapel] = useState(localStorage.getItem("papel"));

  const [produtos, setProdutos] = useState([]);
  const [sku, setSku] = useState("");
  const [nome, setNome] = useState("");
  const [unidade, setUnidade] = useState("un");
  const [estoqueMinimo, setEstoqueMinimo] = useState(0);
  const [erro, setErro] = useState("");

  const [movProdutoId, setMovProdutoId] = useState("");
  const [movTipo, setMovTipo] = useState("entrada");
  const [movQuantidade, setMovQuantidade] = useState(0);
  const [movMotivo, setMovMotivo] = useState("");
  const [erroMov, setErroMov] = useState("");

  // Cabeçalho de autenticação, reaproveitado em todas as requisições
  function authHeaders() {
    return { Authorization: `Bearer ${localStorage.getItem("token")}` };
  }

  function aoEntrar(papelUsuario) {
    setToken(localStorage.getItem("token"));
    setPapel(papelUsuario);
  }

  function sair() {
    localStorage.removeItem("token");
    localStorage.removeItem("papel");
    setToken(null);
    setPapel(null);
  }

  function carregarProdutos() {
    fetch(`${API}/produtos/`, { headers: authHeaders() })
      .then((resposta) => {
        if (resposta.status === 401) {
          sair();
          return [];
        }
        return resposta.json();
      })
      .then((dados) => setProdutos(dados));
  }

  useEffect(() => {
    if (token) {
      carregarProdutos();
    }
  }, [token]);


  useEffect(() => {
    if (!token) return;

    const ws = new WebSocket("ws://127.0.0.1:8000/ws");

    ws.onmessage = (evento) => {
      if (evento.data === "estoque_atualizado") {
        carregarProdutos();
      }
    };

    return () => ws.close();
  }, [token]);

  function cadastrarProduto() {
    setErro("");

    fetch(`${API}/produtos/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({
        sku: sku,
        nome: nome,
        unidade: unidade,
        estoque_minimo: Number(estoqueMinimo),
      }),
    })
      .then(async (resposta) => {
        if (!resposta.ok) {
          const dados = await resposta.json();
          throw new Error(dados.detail || "Erro ao cadastrar");
        }
        return resposta.json();
      })
      .then(() => {
        setSku("");
        setNome("");
        setUnidade("un");
        setEstoqueMinimo(0);
        carregarProdutos();
      })
      .catch((e) => setErro(e.message));
  }

  function excluirProduto(id) {
    fetch(`${API}/produtos/${id}`, {
      method: "DELETE",
      headers: authHeaders(),
    })
      .then(() => carregarProdutos())
      .catch((e) => setErro(e.message));
  }

  function registrarMovimentacao() {
    setErroMov("");

    if (!movProdutoId) {
      setErroMov("Selecione um produto");
      return;
    }

    fetch(`${API}/movimentacoes/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({
        produto_id: Number(movProdutoId),
        tipo: movTipo,
        quantidade: Number(movQuantidade),
        motivo: movMotivo,
      }),
    })
      .then(async (resposta) => {
        if (!resposta.ok) {
          const dados = await resposta.json();
          throw new Error(dados.detail || "Erro na movimentação");
        }
        return resposta.json();
      })
      .then(() => {
        setMovQuantidade(0);
        setMovMotivo("");
        carregarProdutos();
      })
      .catch((e) => setErroMov(e.message));
  }

  if (!token) {
    return <Login aoEntrar={aoEntrar} />;
  }

  const ehAdmin = papel === "admin";
  const podeMovimentar = papel === "admin" || papel === "operador";

  return (
    <div className="container">
      <div className="topo">
        <header className="cabecalho">
          <h1>Controle de Estoque</h1>
          <p>Sistema de gerenciamento de produtos</p>
        </header>
        <div className="usuario-info">
          <span>Papel: {papel}</span>
          <button className="botao-sair" onClick={sair}>
            Sair
          </button>
        </div>
      </div>

      <section className="secao">
        <h2>Dashboard</h2>
        <Graficos produtos={produtos} />
      </section>

      {ehAdmin && (
        <section className="secao">
          <h2>Cadastrar Produto</h2>
          <div className="formulario">
            <div className="campo">
              <label>SKU</label>
              <input
                value={sku}
                onChange={(e) => setSku(e.target.value)}
                placeholder="Ex: PF-003"
              />
            </div>
            <div className="campo">
              <label>Nome</label>
              <input
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                placeholder="Ex: Filtro de Óleo"
              />
            </div>
            <div className="campo">
              <label>Unidade</label>
              <input
                value={unidade}
                onChange={(e) => setUnidade(e.target.value)}
              />
            </div>
            <div className="campo">
              <label>Estoque mínimo</label>
              <input
                type="number"
                value={estoqueMinimo}
                onChange={(e) => setEstoqueMinimo(e.target.value)}
              />
            </div>
          </div>
          <button className="botao" onClick={cadastrarProduto}>
            Cadastrar
          </button>
          {erro && <p className="erro">{erro}</p>}
        </section>
      )}

      {podeMovimentar && (
        <section className="secao">
          <h2>Movimentar Estoque</h2>
          <div className="formulario">
            <div className="campo">
              <label>Produto</label>
              <select
                value={movProdutoId}
                onChange={(e) => setMovProdutoId(e.target.value)}
              >
                <option value="">Selecione...</option>
                {produtos.map((produto) => (
                  <option key={produto.id} value={produto.id}>
                    {produto.nome}
                  </option>
                ))}
              </select>
            </div>
            <div className="campo">
              <label>Tipo</label>
              <select
                value={movTipo}
                onChange={(e) => setMovTipo(e.target.value)}
              >
                <option value="entrada">Entrada</option>
                <option value="saida">Saída</option>
              </select>
            </div>
            <div className="campo">
              <label>Quantidade</label>
              <input
                type="number"
                value={movQuantidade}
                onChange={(e) => setMovQuantidade(e.target.value)}
              />
            </div>
            <div className="campo">
              <label>Motivo</label>
              <input
                value={movMotivo}
                onChange={(e) => setMovMotivo(e.target.value)}
                placeholder="Ex: Compra, Venda..."
              />
            </div>
          </div>
          <button className="botao" onClick={registrarMovimentacao}>
            Registrar
          </button>
          {erroMov && <p className="erro">{erroMov}</p>}
        </section>
      )}

      <section className="secao">
        <h2>Produtos</h2>
        <table className="tabela">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Nome</th>
              <th>Unidade</th>
              <th>Saldo</th>
              <th>Situação</th>
              {ehAdmin && <th>Ações</th>}
            </tr>
          </thead>
          <tbody>
            {produtos.map((produto) => (
              <tr key={produto.id}>
                <td>{produto.sku}</td>
                <td>{produto.nome}</td>
                <td>{produto.unidade}</td>
                <td>{produto.saldo}</td>
                <td>
                  <span
                    className={
                      produto.saldo > produto.estoque_minimo
                        ? "badge badge-ok"
                        : "badge badge-baixo"
                    }
                  >
                    {produto.saldo > produto.estoque_minimo ? "OK" : "Baixo"}
                  </span>
                </td>
                {ehAdmin && (
                  <td>
                    <button
                      className="botao-excluir"
                      onClick={() => excluirProduto(produto.id)}
                    >
                      Excluir
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

export default App;

