import Logo from "./Logo";
 
const MODULOS = [
  { id: "kpi", nome: "KPI Geral", icone: "◈" },
  { id: "estoque", nome: "Estoque", icone: "▤" },
  { id: "financeiro", nome: "Financeiro", icone: "◧" },
  { id: "compras", nome: "Compras", icone: "◪" },
  { id: "producao", nome: "Produção", icone: "◩" },
];
 
const UTILITARIOS = [
  { id: "configuracoes", nome: "Configurações", icone: "⚙" },
  { id: "ajuda", nome: "Ajuda", icone: "?" },
];
 
function Sidebar({ moduloAtivo, aoTrocar, papel, aoSair, aberta, aoFechar }) {
  function selecionar(id) {
    aoTrocar(id);
    if (aoFechar) aoFechar();
  }
 
  return (
    <aside className={`barra-lateral ${aberta ? "barra-aberta" : ""}`}>
      <div className="barra-topo">
        <Logo tamanho={38} comTexto />
      </div>
 
      <nav className="barra-nav">
        <p className="barra-titulo">Módulos</p>
        {MODULOS.map((modulo) => (
          <button
            key={modulo.id}
            className={`barra-item ${moduloAtivo === modulo.id ? "barra-item-ativo" : ""}`}
            onClick={() => selecionar(modulo.id)}
          >
            <span className="barra-icone">{modulo.icone}</span>
            {modulo.nome}
          </button>
        ))}
 
        <p className="barra-titulo">Sistema</p>
        {UTILITARIOS.map((item) => (
          <button
            key={item.id}
            className={`barra-item ${moduloAtivo === item.id ? "barra-item-ativo" : ""}`}
            onClick={() => selecionar(item.id)}
          >
            <span className="barra-icone">{item.icone}</span>
            {item.nome}
          </button>
        ))}
      </nav>
 
      <div className="barra-rodape">
        <span className="barra-papel">{papel}</span>
        <button className="botao-sair" onClick={aoSair}>
          Sair
        </button>
      </div>
    </aside>
  );
}
 
export default Sidebar;