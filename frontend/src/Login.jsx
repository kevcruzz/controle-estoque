import { useState } from "react";
import { API } from "./config";

function Login({ aoEntrar }) {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");

  function entrar() {
    setErro("");

    // O login usa formato de formulário (não JSON), com campos username e password
    const dados = new URLSearchParams();
    dados.append("username", email);
    dados.append("password", senha);

    fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: dados,
    })
      .then(async (resposta) => {
        if (!resposta.ok) {
          throw new Error("E-mail ou senha incorretos");
        }
        return resposta.json();
      })
      .then((resultado) => {
        // Guarda o token e o papel no navegador (sobrevivem ao recarregamento)
        localStorage.setItem("token", resultado.access_token);
        localStorage.setItem("papel", resultado.papel);
        aoEntrar(resultado.papel);
      })
      .catch((e) => setErro(e.message));
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Controle de Estoque</h1>
        <p>Faça login para continuar</p>

        <div className="campo">
          <label>E-mail</label>
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@estoque.com"
          />
        </div>

        <div className="campo">
          <label>Senha</label>
          <input
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            placeholder="••••••••"
          />
        </div>

        <button className="botao" onClick={entrar}>
          Entrar
        </button>

        {erro && <p className="erro">{erro}</p>}
      </div>
    </div>
  );
}

export default Login;