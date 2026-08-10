import { API, WS_URL } from "./config";
import { useState, useEffect } from "react";
import "./App.css";
import Login from "./Login";
import Sidebar from "./Sidebar";
import {
  IndicadoresGerais,
  IndicadoresEstoque,
  IndicadoresFinanceiro,
  ModuloPendente,
} from "./Indicadores";
 
function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [papel, setPapel] = useState(localStorage.getItem("papel"));
 
  const [produtos, setProdutos] = useState([]);
  const [sku, setSku] = useState("");
  const [nome, setNome] = useState("");
  const [unidade, setUnidade] = useState("un");
  const [estoqueMinimo, setEstoqueMinimo] = useState(0);
  const [controlaLote, setControlaLote] = useState(false);
  const [erro, setErro] = useState("");
 
  const [movProdutoId, setMovProdutoId] = useState("");
  const [movTipo, setMovTipo] = useState("entrada");
  const [movQuantidade, setMovQuantidade] = useState(0);
  const [movMotivo, setMovMotivo] = useState("");
  const [movLote, setMovLote] = useState("");
  const [erroMov, setErroMov] = useState("");
 
  // Estados da Nota Fiscal
  const [nfNumero, setNfNumero] = useState("");
  const [nfFornecedor, setNfFornecedor] = useState("");
  const [nfData, setNfData] = useState("");
  const [nfItens, setNfItens] = useState([
    { produto_id: "", quantidade: 0, valor_unitario: 0, lote: "" },
  ]);
  const [erroNf, setErroNf] = useState("");
  const [sucessoNf, setSucessoNf] = useState("");
  const [notas, setNotas] = useState([]);
 
  const [modulo, setModulo] = useState("kpi");
  const [movimentacoes, setMovimentacoes] = useState([]);
  const [menuAberto, setMenuAberto] = useState(false);
  const [empresa, setEmpresa] = useState(null);
 
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
      .then(lerLista)
      .then(setProdutos)
      .catch(() => setProdutos([]));
  }
 
  // Toda resposta de lista passa por aqui. Se a API falhar ou devolver algo
  // que nao seja uma lista, o estado vira [] em vez de quebrar a tela.
  function lerLista(resposta) {
    if (resposta.status === 401) {
      sair();
      return [];
    }
    if (!resposta.ok) {
      return [];
    }
    return resposta.json().then((dados) => (Array.isArray(dados) ? dados : []));
  }
 
  function carregarNotas() {
    fetch(`${API}/notas-fiscais/`, { headers: authHeaders() })
      .then(lerLista)
      .then(setNotas)
      .catch(() => setNotas([]));
  }
 
  function carregarMovimentacoes() {
    fetch(`${API}/movimentacoes/`, { headers: authHeaders() })
      .then(lerLista)
      .then(setMovimentacoes)
      .catch(() => setMovimentacoes([]));
  }
 
  function carregarEmpresa() {
    fetch(`${API}/empresas/minha`, { headers: authHeaders() })
      .then((resposta) => (resposta.ok ? resposta.json() : null))
      .then((dados) => setEmpresa(dados))
      .catch(() => setEmpresa(null));
  }
 
  function alterarExigeLote(valor) {
    fetch(`${API}/empresas/configuracoes`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ exige_lote: valor }),
    })
      .then((resposta) => (resposta.ok ? resposta.json() : null))
      .then((dados) => dados && setEmpresa(dados));
  }
 
  // Diz se o lote deve ser cobrado para um produto: vale a preferencia da
  // empresa ou a marcacao do proprio produto.
  function exigeLote(produtoId) {
    const produto = produtos.find((p) => String(p.id) === String(produtoId));
    return Boolean(empresa?.exige_lote || produto?.controla_lote);
  }
 
  function carregarTudo() {
    carregarProdutos();
    carregarNotas();
    carregarMovimentacoes();
    carregarEmpresa();
  }
 
  useEffect(() => {
    if (token) {
      carregarTudo();
    }
  }, [token]);
 
 
  useEffect(() => {
    if (!token) return;
 
    const ws = new WebSocket(WS_URL);
 
    ws.onmessage = (evento) => {
      if (evento.data === "estoque_atualizado") {
        carregarTudo();
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
        controla_lote: controlaLote,
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
        setControlaLote(false);
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
        lote: movLote,
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
        setMovLote("");
        carregarProdutos();
      })
      .catch((e) => setErroMov(e.message));
  }
 
  function adicionarItem() {
    setNfItens([...nfItens, { produto_id: "", quantidade: 0, valor_unitario: 0, lote: "" }]);
  }
 
  function removerItem(indice) {
    setNfItens(nfItens.filter((_, i) => i !== indice));
  }
 
  function atualizarItem(indice, campo, valor) {
    const novos = nfItens.map((item, i) =>
      i === indice ? { ...item, [campo]: valor } : item
    );
    setNfItens(novos);
  }
 
  function lancarNota() {
    setErroNf("");
    setSucessoNf("");
 
    if (!nfNumero.trim() || !nfFornecedor.trim()) {
      setErroNf("Preencha o número e o fornecedor da nota");
      return;
    }
 
    for (const item of nfItens) {
      if (!item.produto_id) {
        setErroNf("Selecione o produto em todos os itens");
        return;
      }
      if (Number(item.quantidade) <= 0) {
        setErroNf("A quantidade de cada item deve ser maior que zero");
        return;
      }
      if (exigeLote(item.produto_id) && !(item.lote || "").trim()) {
        setErroNf("Informe o lote dos itens que exigem controle de lote");
        return;
      }
    }
 
    const corpo = {
      numero: nfNumero,
      fornecedor: nfFornecedor,
      data_emissao: nfData || null,
      itens: nfItens.map((item) => ({
        produto_id: Number(item.produto_id),
        quantidade: Number(item.quantidade),
        valor_unitario: Number(item.valor_unitario),
        lote: item.lote || null,
      })),
    };
 
    fetch(`${API}/notas-fiscais/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(corpo),
    })
      .then(async (resposta) => {
        if (!resposta.ok) {
          const dados = await resposta.json();
          throw new Error(dados.detail || "Erro ao lançar a nota");
        }
        return resposta.json();
      })
      .then((nota) => {
        setSucessoNf(
          `Nota ${nota.numero} lançada! Total R$ ${nota.valor_total.toFixed(
            2
          )} — estoque atualizado.`
        );
        setNfNumero("");
        setNfFornecedor("");
        setNfData("");
        setNfItens([{ produto_id: "", quantidade: 0, valor_unitario: 0, lote: "" }]);
        carregarProdutos();
        carregarNotas();
      })
      .catch((e) => setErroNf(e.message));
  }
 
  const totalNota = nfItens.reduce(
    (soma, item) =>
      soma + Number(item.quantidade) * Number(item.valor_unitario),
    0
  );
 
  if (!token) {
    return <Login aoEntrar={aoEntrar} />;
  }
 
  const ehAdmin = papel === "admin";
  const podeMovimentar = papel === "admin" || papel === "operador";
 
  return (
    <div className="layout">
      {menuAberto && (
        <div className="menu-fundo" onClick={() => setMenuAberto(false)} />
      )}
 
      <Sidebar
        moduloAtivo={modulo}
        aoTrocar={setModulo}
        papel={papel}
        aoSair={sair}
        aberta={menuAberto}
        aoFechar={() => setMenuAberto(false)}
      />
 
      <main className="conteudo">
        <div className="conteudo-topo">
          <button
            className="botao-menu"
            onClick={() => setMenuAberto(!menuAberto)}
            aria-label="Abrir menu"
          >
            ☰
          </button>
          <h1>{TITULOS[modulo]}</h1>
        </div>
 
        {modulo === "kpi" && (
          <IndicadoresGerais
            produtos={produtos}
            notas={notas}
            movimentacoes={movimentacoes}
          />
        )}
 
        {modulo === "estoque" && (
          <>
            <IndicadoresEstoque produtos={produtos} />
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
              <div className="campo campo-marcavel">
                <label>
                  <input
                    type="checkbox"
                    checked={controlaLote}
                    onChange={(e) => setControlaLote(e.target.checked)}
                  />
                  Controlar lote deste item
                </label>
                <small>
                  Quando marcado, o lote passa a ser obrigatório nas entradas
                  deste produto.
                </small>
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
              <div className="campo">
                <label>
                  Lote{" "}
                  {exigeLote(movProdutoId) ? (
                    <span className="obrigatorio">obrigatório</span>
                  ) : (
                    <span className="opcional">opcional</span>
                  )}
                </label>
                <input
                  value={movLote}
                  onChange={(e) => setMovLote(e.target.value)}
                  placeholder="Ex: L2026-A"
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
                <th>Lote</th>
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
                      {produto.controla_lote ? (
                        <span className="badge badge-lote">controlado</span>
                      ) : (
                        "—"
                      )}
                    </td>
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
          </>
        )}
 
        {modulo === "financeiro" && (
          <>
            <IndicadoresFinanceiro notas={notas} />
          {podeMovimentar && (
                  <section className="secao">
                    <h2>Lançar Nota Fiscal</h2>
                    <div className="formulario">
                      <div className="campo">
                        <label>Número da NF</label>
                        <input
                          value={nfNumero}
                          onChange={(e) => setNfNumero(e.target.value)}
                          placeholder="Ex: 12345"
                        />
                      </div>
                      <div className="campo">
                        <label>Fornecedor</label>
                        <input
                          value={nfFornecedor}
                          onChange={(e) => setNfFornecedor(e.target.value)}
                          placeholder="Ex: Autopeças Silva"
                        />
                      </div>
                      <div className="campo">
                        <label>Data de emissão</label>
                        <input
                          type="date"
                          value={nfData}
                          onChange={(e) => setNfData(e.target.value)}
                        />
                      </div>
                    </div>
 
                    <h3>Itens da nota</h3>
                    <table className="tabela">
                      <thead>
                        <tr>
                          <th>Produto</th>
                          <th>Quantidade</th>
                          <th>Valor unitário (R$)</th>
                          <th>Lote</th>
                          <th>Total do item (R$)</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {nfItens.map((item, indice) => (
                          <tr key={indice}>
                            <td>
                              <select
                                value={item.produto_id}
                                onChange={(e) =>
                                  atualizarItem(indice, "produto_id", e.target.value)
                                }
                              >
                                <option value="">Selecione...</option>
                                {produtos.map((produto) => (
                                  <option key={produto.id} value={produto.id}>
                                    {produto.nome}
                                  </option>
                                ))}
                              </select>
                            </td>
                            <td>
                              <input
                                type="number"
                                min="0"
                                value={item.quantidade}
                                onChange={(e) =>
                                  atualizarItem(indice, "quantidade", e.target.value)
                                }
                              />
                            </td>
                            <td>
                              <input
                                type="number"
                                min="0"
                                step="0.01"
                                value={item.valor_unitario}
                                onChange={(e) =>
                                  atualizarItem(indice, "valor_unitario", e.target.value)
                                }
                              />
                            </td>
                            <td>
                              <input
                                value={item.lote || ""}
                                onChange={(e) =>
                                  atualizarItem(indice, "lote", e.target.value)
                                }
                                placeholder={
                                  exigeLote(item.produto_id)
                                    ? "obrigatório"
                                    : "opcional"
                                }
                                className={
                                  exigeLote(item.produto_id) &&
                                  !(item.lote || "").trim()
                                    ? "campo-pendente"
                                    : ""
                                }
                              />
                            </td>
                            <td>
                              {(
                                Number(item.quantidade) * Number(item.valor_unitario)
                              ).toFixed(2)}
                            </td>
                            <td>
                              {nfItens.length > 1 && (
                                <button
                                  className="botao-excluir"
                                  onClick={() => removerItem(indice)}
                                >
                                  Remover
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
 
                    <button className="botao" onClick={adicionarItem}>
                      + Adicionar item
                    </button>
 
                    <p className="total-nota">
                      Total da nota: <strong>R$ {totalNota.toFixed(2)}</strong>
                    </p>
 
                    <button className="botao" onClick={lancarNota}>
                      Lançar Nota Fiscal
                    </button>
 
                    {erroNf && <p className="erro">{erroNf}</p>}
                    {sucessoNf && <p className="sucesso">{sucessoNf}</p>}
                  </section>
                )}
          <section className="secao">
                  <h2>Notas Fiscais Lançadas</h2>
                  {notas.length === 0 ? (
                    <p>Nenhuma nota lançada ainda.</p>
                  ) : (
                    <table className="tabela">
                      <thead>
                        <tr>
                          <th>Número</th>
                          <th>Fornecedor</th>
                          <th>Emissão</th>
                          <th>Itens</th>
                          <th>Valor total (R$)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {notas.map((nota) => (
                          <tr key={nota.id}>
                            <td>{nota.numero}</td>
                            <td>{nota.fornecedor}</td>
                            <td>{nota.data_emissao || "-"}</td>
                            <td>{nota.itens.length}</td>
                            <td>{nota.valor_total.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </section>
          </>
        )}
 
        {modulo === "compras" && (
          <ModuloPendente
            nome="Compras"
            descricao="Ainda não existe backend para este módulo. Hoje as entradas de mercadoria são registradas pelo módulo Financeiro, ao lançar a nota fiscal."
            planejado={[
              "Cadastro de fornecedores",
              "Pedido de compra e aprovação",
              "Cotação entre fornecedores",
              "Recebimento vinculado ao pedido",
              "Prazo de entrega e atrasos",
              "Histórico de preços por item",
            ]}
          />
        )}
 
        {modulo === "producao" && (
          <ModuloPendente
            nome="Produção"
            descricao="Ainda não existe backend para este módulo."
            planejado={[
              "Ficha técnica (lista de materiais)",
              "Ordem de produção",
              "Baixa automática de insumos",
              "Apontamento de produção",
              "Perdas e refugo",
              "Custo por ordem",
            ]}
          />
        )}
 
        {modulo === "configuracoes" && (
          <section className="secao">
            <h2>Configurações</h2>
            <h3>Empresa</h3>
            <p className="ajuda-texto">
              {empresa ? `${empresa.nome}${empresa.cnpj ? ` · CNPJ ${empresa.cnpj}` : ""}` : "Carregando..."}
            </p>
 
            <h3>Controle de lote</h3>
            <div className="campo campo-marcavel">
              <label>
                <input
                  type="checkbox"
                  checked={Boolean(empresa?.exige_lote)}
                  disabled={!ehAdmin}
                  onChange={(e) => alterarExigeLote(e.target.checked)}
                />
                Exigir lote em todas as entradas
              </label>
              <small>
                Quando ligado, toda entrada de mercadoria pede o lote. Deixe
                desligado para cobrar o lote apenas nos produtos marcados
                individualmente no cadastro.
              </small>
            </div>
 
            <h3>Em construção</h3>
            <p className="ajuda-texto">
              Gestão de usuários e papéis, e demais preferências do sistema.
            </p>
          </section>
        )}
 
        {modulo === "ajuda" && (
          <section className="secao">
            <h2>Ajuda</h2>
            <h3>Como lançar uma nota fiscal</h3>
            <p className="ajuda-texto">
              Vá em Financeiro, preencha número, fornecedor e data, e adicione
              um item para cada produto da nota. O total é calculado
              automaticamente e o estoque é somado ao lançar.
            </p>
            <h3>Produto não aparece na lista</h3>
            <p className="ajuda-texto">
              Só é possível lançar nota de produtos já cadastrados. Cadastre o
              produto no módulo Estoque antes de lançar a nota.
            </p>
            <h3>Papéis de acesso</h3>
            <p className="ajuda-texto">
              Admin cadastra e exclui produtos. Operador movimenta estoque e
              lança notas. Leitor apenas consulta.
            </p>
          </section>
        )}
      </main>
    </div>
  );
}
 
const TITULOS = {
  kpi: "Visão geral",
  estoque: "Estoque",
  financeiro: "Financeiro",
  compras: "Compras",
  producao: "Produção",
  configuracoes: "Configurações",
  ajuda: "Ajuda",
};
 
export default App;