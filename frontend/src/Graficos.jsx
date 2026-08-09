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
} from "recharts";
 
function Graficos({ produtos }) {
  // Dados para o gráfico de barras: saldo de cada produto
  const dadosBarras = produtos.map((produto) => ({
    nome: produto.nome,
    saldo: produto.saldo,
  }));
 
  // Dados para o gráfico de pizza: quantos OK vs quantos Baixo
  const emOk = produtos.filter((p) => p.saldo > p.estoque_minimo).length;
  const emBaixo = produtos.length - emOk;
  const dadosPizza = [
    { nome: "OK", valor: emOk },
    { nome: "Baixo", valor: emBaixo },
  ];
 
  const CORES = ["#2dd4a7", "#fb5f8d"]; // paleta KFuture
 
  return (
    <div className="graficos">
      <div className="grafico">
        <h3>Saldo por produto</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={dadosBarras}>
            <defs>
              <linearGradient id="kf-barra" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22d3ee" />
                <stop offset="100%" stopColor="#a855f7" />
              </linearGradient>
            </defs>
            <XAxis dataKey="nome" stroke="#8e86a8" />
            <YAxis stroke="#8e86a8" />
            <Tooltip contentStyle={{ background: "#130c24", border: "1px solid rgba(168,85,247,0.35)", borderRadius: 10, fontFamily: "JetBrains Mono, monospace", fontSize: 12, color: "#ede9f7" }} />
            <Bar dataKey="saldo" fill="url(#kf-barra)" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
 
      <div className="grafico">
        <h3>Situação do estoque</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={dadosPizza}
              dataKey="valor"
              nameKey="nome"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label
            >
              {dadosPizza.map((entrada, indice) => (
                <Cell key={indice} fill={CORES[indice]} />
              ))}
            </Pie>
            <Legend />
            <Tooltip contentStyle={{ background: "#130c24", border: "1px solid rgba(168,85,247,0.35)", borderRadius: 10, fontFamily: "JetBrains Mono, monospace", fontSize: 12, color: "#ede9f7" }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
 
export default Graficos;