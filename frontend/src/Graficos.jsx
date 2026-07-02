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

  const CORES = ["#10b981", "#ef4444"]; // verde, vermelho

  return (
    <div className="graficos">
      <div className="grafico">
        <h3>Saldo por produto</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={dadosBarras}>
            <XAxis dataKey="nome" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip />
            <Bar dataKey="saldo" fill="#3b82f6" radius={[6, 6, 0, 0]} />
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
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default Graficos;