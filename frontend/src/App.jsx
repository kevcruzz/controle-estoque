import { useState, useEffect } from "react";

function App() {
  const [produtos, setProdutos] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/produtos/")
      .then((resposta) => resposta.json())
      .then((dados) => setProdutos(dados));
  }, []);

  return (
    <div>
      <h1>Controle de Estoque</h1>
      <p>Sistema de gerenciamento de produtos</p>

      <h2>Produtos</h2>
      <ul>
        {produtos.map((produto) => (
          <li key={produto.id}>
            {produto.nome} — saldo: {produto.saldo}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
