import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";
 
const EIXO = { stroke: "#8e86a8", fontSize: 11 };
 
// Cor por situacao. Amarrada ao nome, e nao a posicao: quando uma
// situacao nao tem itens ela some da lista, e cores por posicao
// acabariam pintando a fatia errada.
const COR_SITUACAO = {
  Zerado: "#fb5f8d",
  "Abaixo do mínimo": "#f0a020",
  Adequado: "#2dd4a7",
};
const CAIXA_TOOLTIP = {
  background: "#130c24",
  border: "1px solid rgba(168,85,247,0.35)",
  borderRadius: 10,
  fontFamily: "JetBrains Mono, monospace",
  fontSize: 12,
  color: "#ede9f7",
};
 
function moeda(valor) {
  return valor.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}
 
export function Cartao({ rotulo, valor, detalhe, tom = "neutro" }) {
  return (
    <div className={`cartao cartao-${tom}`}>
      <span className="cartao-rotulo">{rotulo}</span>
      <strong className="cartao-valor">{valor}</strong>
      {detalhe && <span className="cartao-detalhe">{detalhe}</span>}
    </div>
  );
}
 
export function Vazio({ mensagem }) {
  return <p className="painel-vazio">{mensagem}</p>;
}
 
/* ---------- Indicadores de Estoque ---------- */
export function IndicadoresEstoque({ produtos }) {
  const totalSkus = produtos.length;
  const unidades = produtos.reduce((s, p) => s + p.saldo, 0);
  const abaixoMinimo = produtos.filter(
    (p) => p.saldo < p.estoque_minimo
  ).length;
  const zerados = produtos.filter((p) => p.saldo === 0).length;
 
  const dadosBarras = produtos
    .slice()
    .sort((a, b) => b.saldo - a.saldo)
    .slice(0, 8)
    .map((p) => ({ nome: p.nome, saldo: p.saldo }));
 
  const dadosPizza = [
    { nome: "Zerado", valor: zerados },
    { nome: "Abaixo do mínimo", valor: abaixoMinimo - zerados },
    { nome: "Adequado", valor: totalSkus - abaixoMinimo },
  ].filter((d) => d.valor > 0);
 
  return (
    <>
      <div className="cartoes">
        <Cartao rotulo="SKUs cadastrados" valor={totalSkus} />
        <Cartao rotulo="Unidades em estoque" valor={unidades} />
        <Cartao
          rotulo="Abaixo do mínimo"
          valor={abaixoMinimo}
          tom={abaixoMinimo > 0 ? "alerta" : "ok"}
          detalhe={abaixoMinimo > 0 ? "requer reposição" : "tudo adequado"}
        />
        <Cartao
          rotulo="Itens zerados"
          valor={zerados}
          tom={zerados > 0 ? "alerta" : "ok"}
        />
      </div>
 
      <div className="paineis">
        <div className="painel">
          <h3>Maiores saldos</h3>
          {dadosBarras.length === 0 ? (
            <Vazio mensagem="Cadastre produtos para ver o gráfico." />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={dadosBarras}>
                <defs>
                  <linearGradient id="g-barra" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22d3ee" />
                    <stop offset="100%" stopColor="#a855f7" />
                  </linearGradient>
                </defs>
                <XAxis dataKey="nome" {...EIXO} />
                <YAxis {...EIXO} />
                <Tooltip contentStyle={CAIXA_TOOLTIP} cursor={{ fill: "rgba(168,85,247,0.08)" }} />
                <Bar dataKey="saldo" fill="url(#g-barra)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
 
        <div className="painel">
          <h3>Itens por situação</h3>
          {dadosPizza.length === 0 ? (
            <Vazio mensagem="Sem dados suficientes." />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={dadosPizza}
                  dataKey="valor"
                  nameKey="nome"
                  outerRadius={90}
                  label
                >
                  {dadosPizza.map((fatia) => (
                    <Cell key={fatia.nome} fill={COR_SITUACAO[fatia.nome]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={CAIXA_TOOLTIP} />
                <Legend wrapperStyle={{ fontSize: 12, fontFamily: "JetBrains Mono, monospace" }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </>
  );
}
 
/* ---------- Indicadores Financeiros ---------- */
export function IndicadoresFinanceiro({ notas }) {
  const quantidade = notas.length;
  const total = notas.reduce((s, n) => s + n.valor_total, 0);
  const ticket = quantidade > 0 ? total / quantidade : 0;
  const fornecedores = new Set(notas.map((n) => n.fornecedor)).size;
 
  const porFornecedor = Object.entries(
    notas.reduce((acc, n) => {
      acc[n.fornecedor] = (acc[n.fornecedor] || 0) + n.valor_total;
      return acc;
    }, {})
  )
    .map(([nome, valor]) => ({ nome, valor }))
    .sort((a, b) => b.valor - a.valor)
    .slice(0, 8);
 
  const evolucao = notas
    .slice()
    .sort((a, b) => new Date(a.criado_em) - new Date(b.criado_em))
    .map((n) => ({
      data: new Date(n.criado_em).toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
      }),
      valor: n.valor_total,
    }));
 
  return (
    <>
      <div className="cartoes">
        <Cartao rotulo="Notas lançadas" valor={quantidade} />
        <Cartao rotulo="Total em compras" valor={moeda(total)} tom="destaque" />
        <Cartao rotulo="Ticket médio" valor={moeda(ticket)} />
        <Cartao rotulo="Fornecedores" valor={fornecedores} />
      </div>
 
      <div className="paineis">
        <div className="painel">
          <h3>Compras por fornecedor</h3>
          {porFornecedor.length === 0 ? (
            <Vazio mensagem="Nenhuma nota fiscal lançada ainda." />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={porFornecedor} layout="vertical">
                <defs>
                  <linearGradient id="g-forn" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#a855f7" />
                    <stop offset="100%" stopColor="#e935c1" />
                  </linearGradient>
                </defs>
                <XAxis type="number" {...EIXO} />
                <YAxis type="category" dataKey="nome" width={110} {...EIXO} />
                <Tooltip contentStyle={CAIXA_TOOLTIP} cursor={{ fill: "rgba(168,85,247,0.08)" }} />
                <Bar dataKey="valor" fill="url(#g-forn)" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
 
        <div className="painel">
          <h3>Evolução das compras</h3>
          {evolucao.length === 0 ? (
            <Vazio mensagem="Nenhuma nota fiscal lançada ainda." />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={evolucao}>
                <CartesianGrid stroke="rgba(168,85,247,0.12)" />
                <XAxis dataKey="data" {...EIXO} />
                <YAxis {...EIXO} />
                <Tooltip contentStyle={CAIXA_TOOLTIP} />
                <Line
                  type="monotone"
                  dataKey="valor"
                  stroke="#22d3ee"
                  strokeWidth={2}
                  dot={{ fill: "#e935c1", r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </>
  );
}
 
/* ---------- Visão geral (executiva) ---------- */
export function IndicadoresGerais({ produtos, notas, movimentacoes }) {
  // Último preço de compra conhecido de cada produto, tirado das notas.
  // Percorre da nota mais antiga para a mais nova, então o último valor
  // gravado é sempre o mais recente.
  const custoUnitario = {};
  notas
    .slice()
    .sort((a, b) => new Date(a.criado_em) - new Date(b.criado_em))
    .forEach((nota) =>
      (nota.itens || []).forEach((item) => {
        custoUnitario[item.produto_id] = item.valor_unitario;
      })
    );
 
  const unidades = produtos.reduce((s, p) => s + p.saldo, 0);
  const abaixoMinimo = produtos.filter((p) => p.saldo < p.estoque_minimo).length;
  const zerados = produtos.filter((p) => p.saldo === 0).length;
  const semCusto = produtos.filter(
    (p) => p.saldo > 0 && custoUnitario[p.id] === undefined
  ).length;
 
  const valorEstoque = produtos.reduce(
    (s, p) => s + p.saldo * (custoUnitario[p.id] || 0),
    0
  );
 
  const totalCompras = notas.reduce((s, n) => s + n.valor_total, 0);
  const ticket = notas.length > 0 ? totalCompras / notas.length : 0;
  const fornecedores = new Set(notas.map((n) => n.fornecedor)).size;
 
  const entradas = movimentacoes.filter((m) => m.tipo === "entrada");
  const saidas = movimentacoes.filter((m) => m.tipo === "saida");
  const unidadesEntrada = entradas.reduce((s, m) => s + m.quantidade, 0);
  const unidadesSaida = saidas.reduce((s, m) => s + m.quantidade, 0);
 
  // Valor em estoque por produto (saldo x último custo)
  const valorPorProduto = produtos
    .map((p) => ({
      nome: p.nome,
      valor: p.saldo * (custoUnitario[p.id] || 0),
    }))
    .filter((d) => d.valor > 0)
    .sort((a, b) => b.valor - a.valor)
    .slice(0, 8);
 
  // Cobertura: quantos itens estão adequados, baixos ou zerados
  const cobertura = [
    { nome: "Zerado", valor: zerados },
    { nome: "Abaixo do mínimo", valor: abaixoMinimo - zerados },
    { nome: "Adequado", valor: produtos.length - abaixoMinimo },
  ].filter((d) => d.valor > 0);
 
  // Entradas e saídas por dia
  const porDia = {};
  movimentacoes.forEach((m) => {
    const dia = new Date(m.criado_em).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
    });
    if (!porDia[dia]) porDia[dia] = { dia, entrada: 0, saida: 0 };
    porDia[dia][m.tipo] += m.quantidade;
  });
  const fluxo = Object.values(porDia);
 
  const semDados =
    produtos.length === 0 && notas.length === 0 && movimentacoes.length === 0;
 
  if (semDados) {
    return (
      <div className="painel">
        <h3>Sem dados ainda</h3>
        <Vazio mensagem="Cadastre produtos no módulo Estoque e lance notas fiscais no Financeiro. Os indicadores aparecem aqui automaticamente." />
      </div>
    );
  }
 
  return (
    <>
      <div className="cartoes">
        <Cartao
          rotulo="Valor em estoque"
          valor={moeda(valorEstoque)}
          tom="destaque"
          detalhe={
            semCusto > 0
              ? `${semCusto} item(ns) sem custo conhecido`
              : "pelo último preço de compra"
          }
        />
        <Cartao rotulo="SKUs cadastrados" valor={produtos.length} />
        <Cartao rotulo="Unidades em estoque" valor={unidades} />
        <Cartao
          rotulo="Abaixo do mínimo"
          valor={abaixoMinimo}
          tom={abaixoMinimo > 0 ? "alerta" : "ok"}
          detalhe={abaixoMinimo > 0 ? "requer reposição" : "tudo adequado"}
        />
        <Cartao
          rotulo="Itens zerados"
          valor={zerados}
          tom={zerados > 0 ? "alerta" : "ok"}
        />
        <Cartao rotulo="Total em compras" valor={moeda(totalCompras)} />
        <Cartao
          rotulo="Ticket médio por nota"
          valor={moeda(ticket)}
          detalhe={`${notas.length} nota(s)`}
        />
        <Cartao
          rotulo="Fluxo de unidades"
          valor={`${unidadesEntrada} / ${unidadesSaida}`}
          detalhe="entradas / saídas"
        />
      </div>
 
      <p className="grupo-titulo">Estoque</p>
      <div className="paineis">
        <div className="painel">
          <h3>Maiores saldos</h3>
          {produtos.length === 0 ? (
            <Vazio mensagem="Cadastre produtos para ver o gráfico." />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart
                data={produtos
                  .slice()
                  .sort((a, b) => b.saldo - a.saldo)
                  .slice(0, 8)
                  .map((p) => ({ nome: p.nome, saldo: p.saldo }))}
              >
                <defs>
                  <linearGradient id="g-saldo" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22d3ee" />
                    <stop offset="100%" stopColor="#a855f7" />
                  </linearGradient>
                </defs>
                <XAxis dataKey="nome" {...EIXO} />
                <YAxis {...EIXO} />
                <Tooltip contentStyle={CAIXA_TOOLTIP} cursor={{ fill: "rgba(168,85,247,0.08)" }} />
                <Bar dataKey="saldo" fill="url(#g-saldo)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
 
        <div className="painel">
          <h3>Itens por situação</h3>
          {cobertura.length === 0 ? (
            <Vazio mensagem="Sem dados suficientes." />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={cobertura} dataKey="valor" nameKey="nome" outerRadius={95} label>
                  {cobertura.map((fatia) => (
                    <Cell key={fatia.nome} fill={COR_SITUACAO[fatia.nome]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={CAIXA_TOOLTIP} />
                <Legend wrapperStyle={{ fontSize: 12, fontFamily: "JetBrains Mono, monospace" }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
 
        <div className="painel">
          <h3>Valor imobilizado por produto</h3>
          {valorPorProduto.length === 0 ? (
            <Vazio mensagem="Lance notas fiscais para o sistema conhecer o custo dos produtos." />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={valorPorProduto} layout="vertical">
                <defs>
                  <linearGradient id="g-valor" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#a855f7" />
                    <stop offset="100%" stopColor="#e935c1" />
                  </linearGradient>
                </defs>
                <XAxis type="number" {...EIXO} />
                <YAxis type="category" dataKey="nome" width={120} {...EIXO} />
                <Tooltip contentStyle={CAIXA_TOOLTIP} cursor={{ fill: "rgba(168,85,247,0.08)" }} />
                <Bar dataKey="valor" fill="url(#g-valor)" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
 
      <p className="grupo-titulo">Financeiro</p>
      <div className="paineis">
        <div className="painel">
          <h3>Compras por fornecedor</h3>
          {notas.length === 0 ? (
            <Vazio mensagem="Nenhuma nota fiscal lançada ainda." />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart
                layout="vertical"
                data={Object.entries(
                  notas.reduce((acc, n) => {
                    acc[n.fornecedor] = (acc[n.fornecedor] || 0) + n.valor_total;
                    return acc;
                  }, {})
                )
                  .map(([nome, valor]) => ({ nome, valor }))
                  .sort((a, b) => b.valor - a.valor)
                  .slice(0, 8)}
              >
                <defs>
                  <linearGradient id="g-forn2" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#22d3ee" />
                    <stop offset="100%" stopColor="#a855f7" />
                  </linearGradient>
                </defs>
                <XAxis type="number" {...EIXO} />
                <YAxis type="category" dataKey="nome" width={120} {...EIXO} />
                <Tooltip contentStyle={CAIXA_TOOLTIP} cursor={{ fill: "rgba(168,85,247,0.08)" }} />
                <Bar dataKey="valor" fill="url(#g-forn2)" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
 
        <div className="painel">
          <h3>Evolução das compras</h3>
          {notas.length === 0 ? (
            <Vazio mensagem="Nenhuma nota fiscal lançada ainda." />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart
                data={notas
                  .slice()
                  .sort((a, b) => new Date(a.criado_em) - new Date(b.criado_em))
                  .map((n) => ({
                    data: new Date(n.criado_em).toLocaleDateString("pt-BR", {
                      day: "2-digit",
                      month: "2-digit",
                    }),
                    valor: n.valor_total,
                  }))}
              >
                <CartesianGrid stroke="rgba(168,85,247,0.12)" />
                <XAxis dataKey="data" {...EIXO} />
                <YAxis {...EIXO} />
                <Tooltip contentStyle={CAIXA_TOOLTIP} />
                <Line
                  type="monotone"
                  dataKey="valor"
                  stroke="#22d3ee"
                  strokeWidth={2}
                  dot={{ fill: "#e935c1", r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
 
        <div className="painel">
          <h3>Entradas e saídas por dia</h3>
          {fluxo.length === 0 ? (
            <Vazio mensagem="Nenhuma movimentação registrada ainda." />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={fluxo}>
                <CartesianGrid stroke="rgba(168,85,247,0.12)" />
                <XAxis dataKey="dia" {...EIXO} />
                <YAxis {...EIXO} />
                <Tooltip contentStyle={CAIXA_TOOLTIP} cursor={{ fill: "rgba(168,85,247,0.08)" }} />
                <Legend wrapperStyle={{ fontSize: 12, fontFamily: "JetBrains Mono, monospace" }} />
                <Bar dataKey="entrada" name="Entradas" fill="#2dd4a7" radius={[5, 5, 0, 0]} />
                <Bar dataKey="saida" name="Saídas" fill="#fb5f8d" radius={[5, 5, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </>
  );
}
 
/* ---------- Módulos ainda não construídos ---------- */
export function ModuloPendente({ nome, descricao, planejado }) {
  return (
    <div className="modulo-pendente">
      <h2>{nome}</h2>
      <p className="pendente-aviso">Módulo ainda não implementado.</p>
      <p>{descricao}</p>
      <p className="pendente-titulo">Previsto para este módulo:</p>
      <ul>
        {planejado.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}