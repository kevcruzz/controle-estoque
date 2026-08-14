import { useState } from "react";
import { Cartao, Vazio } from "./Indicadores";
 
const ROTULO_STATUS = {
  planejada: "Planejada",
  em_producao: "Em produção",
  concluida: "Concluída",
  cancelada: "Cancelada",
};
 
function moeda(valor) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
 
function Producao({
  fichas,
  ordens,
  produtos,
  ehAdmin,
  aoCriarFicha,
  aoCriarOrdem,
  aoConcluir,
  erro,
  sucesso,
}) {
  const [produtoFicha, setProdutoFicha] = useState("");
  const [descricaoFicha, setDescricaoFicha] = useState("");
  const [insumos, setInsumos] = useState([{ insumo_id: "", quantidade: 1 }]);
 
  const [aviso, setAviso] = useState("");
  const [numeroOrdem, setNumeroOrdem] = useState("");
  const [produtoOrdem, setProdutoOrdem] = useState("");
  const [qtdOrdem, setQtdOrdem] = useState(0);
 
  const planejadas = ordens.filter((o) => o.status === "planejada").length;
  const concluidas = ordens.filter((o) => o.status === "concluida");
  const custoTotal = concluidas.reduce((s, o) => s + o.custo_insumos, 0);
  const unidadesProduzidas = concluidas.reduce((s, o) => s + o.quantidade, 0);
 
  // Só produtos com ficha técnica podem virar ordem de produção
  const comFicha = produtos.filter((p) =>
    fichas.some((f) => f.produto_id === p.id)
  );
 
  function atualizarInsumo(indice, campo, valor) {
    setInsumos(
      insumos.map((it, i) => (i === indice ? { ...it, [campo]: valor } : it))
    );
  }
 
  return (
    <>
      <div className="cartoes">
        <Cartao rotulo="Fichas técnicas" valor={fichas.length} />
        <Cartao rotulo="Ordens planejadas" valor={planejadas} />
        <Cartao rotulo="Unidades produzidas" valor={unidadesProduzidas} />
        <Cartao
          rotulo="Custo de produção"
          valor={moeda(custoTotal)}
          tom="destaque"
          detalhe="insumos consumidos"
        />
      </div>
 
      <section className="secao">
        <h2>Ficha Técnica</h2>
        <p className="ajuda-texto">
          A ficha define o que é preciso para fabricar <strong>uma</strong>{" "}
          unidade do produto. Ao concluir uma ordem, o sistema multiplica pela
          quantidade produzida e baixa os insumos do estoque.
        </p>
 
        <div className="formulario">
          <div className="campo">
            <label>Produto final</label>
            <select
              value={produtoFicha}
              onChange={(e) => setProdutoFicha(e.target.value)}
            >
              <option value="">Selecione...</option>
              {produtos.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nome}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label>Descrição</label>
            <input
              value={descricaoFicha}
              onChange={(e) => setDescricaoFicha(e.target.value)}
              placeholder="opcional"
            />
          </div>
        </div>
 
        <h3>Insumos por unidade</h3>
 
        {produtos.length < 2 && (
          <p className="painel-vazio">
            Só há {produtos.length} produto cadastrado. Para montar uma ficha
            técnica é preciso ter o produto final e ao menos um insumo —
            cadastre os insumos no módulo Estoque.
          </p>
        )}
 
        <table className="tabela">
          <thead>
            <tr>
              <th>Insumo</th>
              <th>Quantidade</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {insumos.map((item, indice) => (
              <tr key={indice}>
                <td>
                  <select
                    value={item.insumo_id}
                    onChange={(e) =>
                      atualizarInsumo(indice, "insumo_id", e.target.value)
                    }
                  >
                    <option value="">
                      {produtos.filter(
                        (p) => String(p.id) !== String(produtoFicha)
                      ).length === 0
                        ? "Nenhum insumo disponível"
                        : "Selecione..."}
                    </option>
                    {produtos
                      .filter((p) => String(p.id) !== String(produtoFicha))
                      .map((p) => (
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
                    step="0.01"
                    value={item.quantidade}
                    onChange={(e) =>
                      atualizarInsumo(indice, "quantidade", e.target.value)
                    }
                  />
                </td>
                <td>
                  {insumos.length > 1 && (
                    <button
                      className="botao-excluir"
                      onClick={() =>
                        setInsumos(insumos.filter((_, i) => i !== indice))
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
          onClick={() => setInsumos([...insumos, { insumo_id: "", quantidade: 1 }])}
        >
          + Adicionar insumo
        </button>
 
        <button
          className="botao"
          onClick={() => {
            if (!produtoFicha) return setAviso("Selecione o produto final.");
            for (const i of insumos) {
              if (!i.insumo_id) return setAviso("Selecione todos os insumos.");
              if (Number(i.quantidade) <= 0)
                return setAviso("A quantidade de cada insumo deve ser maior que zero.");
            }
            setAviso("");
            aoCriarFicha(
              {
                produto_id: Number(produtoFicha),
                descricao: descricaoFicha || null,
                itens: insumos.map((i) => ({
                  insumo_id: Number(i.insumo_id),
                  quantidade: Number(i.quantidade),
                })),
              },
              () => {
                setProdutoFicha("");
                setDescricaoFicha("");
                setInsumos([{ insumo_id: "", quantidade: 1 }]);
              }
            );
          }}
        >
          Salvar Ficha
        </button>
 
        {fichas.length > 0 && (
          <table className="tabela" style={{ marginTop: 24 }}>
            <thead>
              <tr>
                <th>Produto</th>
                <th>Composição (por unidade)</th>
              </tr>
            </thead>
            <tbody>
              {fichas.map((f) => (
                <tr key={f.id}>
                  <td>{f.produto_nome}</td>
                  <td>
                    {f.itens
                      .map((i) => `${i.quantidade}x ${i.insumo_nome}`)
                      .join("  +  ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
 
      <section className="secao">
        <h2>Ordem de Produção</h2>
 
        {comFicha.length === 0 ? (
          <Vazio mensagem="Cadastre uma ficha técnica antes de abrir uma ordem de produção." />
        ) : (
          <>
            <div className="formulario">
              <div className="campo">
                <label>Número da ordem</label>
                <input
                  value={numeroOrdem}
                  onChange={(e) => setNumeroOrdem(e.target.value)}
                  placeholder="Ex: OP-001"
                />
              </div>
              <div className="campo">
                <label>Produto</label>
                <select
                  value={produtoOrdem}
                  onChange={(e) => setProdutoOrdem(e.target.value)}
                >
                  <option value="">Selecione...</option>
                  {comFicha.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nome}
                    </option>
                  ))}
                </select>
              </div>
              <div className="campo">
                <label>Quantidade a produzir</label>
                <input
                  type="number"
                  min="0"
                  value={qtdOrdem}
                  onChange={(e) => setQtdOrdem(e.target.value)}
                />
              </div>
            </div>
 
            <button
              className="botao"
              onClick={() => {
                if (!numeroOrdem.trim()) return setAviso("Informe o número da ordem.");
                if (!produtoOrdem) return setAviso("Selecione o produto.");
                if (Number(qtdOrdem) <= 0)
                  return setAviso("A quantidade deve ser maior que zero.");
                setAviso("");
                aoCriarOrdem(
                  {
                    numero: numeroOrdem,
                    produto_id: Number(produtoOrdem),
                    quantidade: Number(qtdOrdem),
                  },
                  () => {
                    setNumeroOrdem("");
                    setProdutoOrdem("");
                    setQtdOrdem(0);
                  }
                );
              }}
            >
              Abrir Ordem
            </button>
          </>
        )}
 
        {aviso && <p className="erro">{aviso}</p>}
        {erro && <p className="erro">{erro}</p>}
        {sucesso && <p className="sucesso">{sucesso}</p>}
      </section>
 
      <section className="secao">
        <h2>Ordens</h2>
        {ordens.length === 0 ? (
          <Vazio mensagem="Nenhuma ordem aberta ainda." />
        ) : (
          <table className="tabela">
            <thead>
              <tr>
                <th>Número</th>
                <th>Produto</th>
                <th>Qtd.</th>
                <th>Situação</th>
                <th>Custo insumos</th>
                <th>Consumo</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {ordens.map((o) => (
                <tr key={o.id}>
                  <td>{o.numero}</td>
                  <td>{o.produto_nome}</td>
                  <td>{o.quantidade}</td>
                  <td>
                    <span className={`badge badge-${o.status}`}>
                      {ROTULO_STATUS[o.status]}
                    </span>
                  </td>
                  <td>
                    {o.status === "concluida" ? moeda(o.custo_insumos) : "—"}
                  </td>
                  <td>
                    {o.consumos.length > 0
                      ? o.consumos
                          .map((c) => `${c.quantidade}x ${c.insumo_nome}`)
                          .join(", ")
                      : "—"}
                  </td>
                  <td>
                    {o.status === "planejada" && (
                      <button className="botao" onClick={() => aoConcluir(o.id)}>
                        Concluir
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="nota-rodape">
          Concluir uma ordem baixa os insumos e dá entrada no produto acabado.
          Se faltar qualquer insumo, nada é movimentado.
        </p>
      </section>
    </>
  );
}
 
export default Producao;