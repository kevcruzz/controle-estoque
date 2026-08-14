import { useState } from "react";
import { Cartao, Vazio } from "./Indicadores";
 
const ROTULO_STATUS = {
  rascunho: "Rascunho",
  aprovado: "Aprovado",
  recebido: "Recebido",
  cancelado: "Cancelado",
};
 
function moeda(valor) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
 
function Compras({
  fornecedores,
  pedidos,
  produtos,
  ehAdmin,
  aoCriarFornecedor,
  aoCriarPedido,
  aoAprovar,
  aoCancelar,
  erro,
  sucesso,
  erroSecao,
  sucessoSecao,
}) {
  const [nomeForn, setNomeForn] = useState("");
  const [cnpjForn, setCnpjForn] = useState("");
  const [emailForn, setEmailForn] = useState("");
 
  const [numero, setNumero] = useState("");
  const [fornecedorId, setFornecedorId] = useState("");
  const [previsao, setPrevisao] = useState("");
  const [itens, setItens] = useState([
    { produto_id: "", quantidade: 0, valor_unitario: 0 },
  ]);
 
  const total = itens.reduce(
    (soma, i) => soma + Number(i.quantidade) * Number(i.valor_unitario),
    0
  );
 
  const emAberto = pedidos.filter((p) => p.status === "rascunho").length;
  const aprovados = pedidos.filter((p) => p.status === "aprovado").length;
  const valorAberto = pedidos
    .filter((p) => p.status === "rascunho" || p.status === "aprovado")
    .reduce((s, p) => s + p.valor_total, 0);
 
  function atualizarItem(indice, campo, valor) {
    setItens(itens.map((it, i) => (i === indice ? { ...it, [campo]: valor } : it)));
  }
 
  const [avisoForn, setAvisoForn] = useState("");
  const [avisoPedido, setAvisoPedido] = useState("");
 
  function enviarPedido() {
    setAvisoPedido("");
 
    if (!numero.trim()) return setAvisoPedido("Informe o número do pedido.");
    if (!fornecedorId) return setAvisoPedido("Selecione o fornecedor.");
    for (const item of itens) {
      if (!item.produto_id) return setAvisoPedido("Selecione o produto de cada item.");
      if (Number(item.quantidade) <= 0)
        return setAvisoPedido("A quantidade de cada item deve ser maior que zero.");
    }
 
    aoCriarPedido(
      {
        numero,
        fornecedor_id: Number(fornecedorId),
        previsao_entrega: previsao || null,
        itens: itens.map((i) => ({
          produto_id: Number(i.produto_id),
          quantidade: Number(i.quantidade),
          valor_unitario: Number(i.valor_unitario),
        })),
      },
      () => {
        setNumero("");
        setFornecedorId("");
        setPrevisao("");
        setItens([{ produto_id: "", quantidade: 0, valor_unitario: 0 }]);
      }
    );
  }
 
  return (
    <>
      <div className="cartoes">
        <Cartao rotulo="Fornecedores" valor={fornecedores.length} />
        <Cartao rotulo="Pedidos em rascunho" valor={emAberto} />
        <Cartao
          rotulo="Aguardando entrega"
          valor={aprovados}
          tom={aprovados > 0 ? "destaque" : "neutro"}
        />
        <Cartao
          rotulo="Valor comprometido"
          valor={moeda(valorAberto)}
          detalhe="pedidos não recebidos"
        />
      </div>
 
      <section className="secao">
        <h2>Cadastrar Fornecedor</h2>
        <div className="formulario">
          <div className="campo">
            <label>Nome</label>
            <input
              value={nomeForn}
              onChange={(e) => setNomeForn(e.target.value)}
              placeholder="Ex: Autopeças Silva"
            />
          </div>
          <div className="campo">
            <label>CNPJ</label>
            <input
              value={cnpjForn}
              onChange={(e) => setCnpjForn(e.target.value)}
              placeholder="opcional"
            />
          </div>
          <div className="campo">
            <label>E-mail</label>
            <input
              value={emailForn}
              onChange={(e) => setEmailForn(e.target.value)}
              placeholder="opcional"
            />
          </div>
        </div>
        <button
          className="botao"
          onClick={() => {
            if (!nomeForn.trim()) {
              setAvisoForn("Informe o nome do fornecedor.");
              return;
            }
            setAvisoForn("");
            aoCriarFornecedor(
              { nome: nomeForn, cnpj: cnpjForn || null, email: emailForn || null },
              () => {
                setNomeForn("");
                setCnpjForn("");
                setEmailForn("");
              }
            );
          }}
        >
          Cadastrar
        </button>
 
        {avisoForn && <p className="erro">{avisoForn}</p>}
        {erroSecao === "fornecedor" && erro && <p className="erro">{erro}</p>}
        {sucessoSecao === "fornecedor" && sucesso && (
          <p className="sucesso">{sucesso}</p>
        )}
 
        {fornecedores.length > 0 && (
          <table className="tabela" style={{ marginTop: 22 }}>
            <thead>
              <tr>
                <th>Nome</th>
                <th>CNPJ</th>
                <th>E-mail</th>
              </tr>
            </thead>
            <tbody>
              {fornecedores.map((f) => (
                <tr key={f.id}>
                  <td>{f.nome}</td>
                  <td>{f.cnpj || "—"}</td>
                  <td>{f.email || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
 
      <section className="secao">
        <h2>Novo Pedido de Compra</h2>
 
        {fornecedores.length === 0 ? (
          <Vazio mensagem="Cadastre um fornecedor antes de abrir um pedido." />
        ) : (
          <>
            <div className="formulario">
              <div className="campo">
                <label>Número do pedido</label>
                <input
                  value={numero}
                  onChange={(e) => setNumero(e.target.value)}
                  placeholder="Ex: PC-001"
                />
              </div>
              <div className="campo">
                <label>Fornecedor</label>
                <select
                  value={fornecedorId}
                  onChange={(e) => setFornecedorId(e.target.value)}
                >
                  <option value="">Selecione...</option>
                  {fornecedores.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.nome}
                    </option>
                  ))}
                </select>
              </div>
              <div className="campo">
                <label>Previsão de entrega</label>
                <input
                  type="date"
                  value={previsao}
                  onChange={(e) => setPrevisao(e.target.value)}
                />
              </div>
            </div>
 
            <h3>Itens do pedido</h3>
            <table className="tabela">
              <thead>
                <tr>
                  <th>Produto</th>
                  <th>Quantidade</th>
                  <th>Valor unitário (R$)</th>
                  <th>Total (R$)</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {itens.map((item, indice) => (
                  <tr key={indice}>
                    <td>
                      <select
                        value={item.produto_id}
                        onChange={(e) =>
                          atualizarItem(indice, "produto_id", e.target.value)
                        }
                      >
                        <option value="">Selecione...</option>
                        {produtos.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.nome}
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
                      {(
                        Number(item.quantidade) * Number(item.valor_unitario)
                      ).toFixed(2)}
                    </td>
                    <td>
                      {itens.length > 1 && (
                        <button
                          className="botao-excluir"
                          onClick={() =>
                            setItens(itens.filter((_, i) => i !== indice))
                          }
                        >
                          Remover
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
 
            <button
              className="botao"
              onClick={() =>
                setItens([
                  ...itens,
                  { produto_id: "", quantidade: 0, valor_unitario: 0 },
                ])
              }
            >
              + Adicionar item
            </button>
 
            <p className="total-nota">
              Total do pedido: <strong>{moeda(total)}</strong>
            </p>
 
            <button className="botao" onClick={enviarPedido}>
              Criar Pedido
            </button>
          </>
        )}
 
        {avisoPedido && <p className="erro">{avisoPedido}</p>}
        {erroSecao === "pedido" && erro && <p className="erro">{erro}</p>}
        {sucessoSecao === "pedido" && sucesso && (
          <p className="sucesso">{sucesso}</p>
        )}
      </section>
 
      <section className="secao">
        <h2>Pedidos</h2>
        {pedidos.length === 0 ? (
          <Vazio mensagem="Nenhum pedido criado ainda." />
        ) : (
          <table className="tabela">
            <thead>
              <tr>
                <th>Número</th>
                <th>Fornecedor</th>
                <th>Previsão</th>
                <th>Itens</th>
                <th>Valor (R$)</th>
                <th>Situação</th>
                {ehAdmin && <th>Ações</th>}
              </tr>
            </thead>
            <tbody>
              {pedidos.map((p) => (
                <tr key={p.id}>
                  <td>{p.numero}</td>
                  <td>{p.fornecedor_nome}</td>
                  <td>
                    {p.previsao_entrega
                      ? new Date(p.previsao_entrega + "T00:00").toLocaleDateString(
                          "pt-BR"
                        )
                      : "—"}
                  </td>
                  <td>{p.itens.length}</td>
                  <td>{p.valor_total.toFixed(2)}</td>
                  <td>
                    <span className={`badge badge-${p.status}`}>
                      {ROTULO_STATUS[p.status]}
                    </span>
                  </td>
                  {ehAdmin && (
                    <td>
                      {p.status === "rascunho" && (
                        <>
                          <button className="botao" onClick={() => aoAprovar(p.id)}>
                            Aprovar
                          </button>
                          <button
                            className="botao-excluir"
                            onClick={() => aoCancelar(p.id)}
                          >
                            Cancelar
                          </button>
                        </>
                      )}
                      {p.status === "aprovado" && (
                        <button
                          className="botao-excluir"
                          onClick={() => aoCancelar(p.id)}
                        >
                          Cancelar
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="nota-rodape">
          Aprovar um pedido não altera o estoque. A mercadoria entra quando
          chega, pelo lançamento da nota fiscal no módulo Financeiro.
        </p>
      </section>
    </>
  );
}
 
export default Compras;