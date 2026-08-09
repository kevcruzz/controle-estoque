function Logo({ tamanho = 40, comTexto = false }) {
  return (
    <div className="marca">
      <svg
        className="marca-simbolo"
        width={tamanho}
        height={tamanho}
        viewBox="0 0 120 120"
        fill="none"
        role="img"
        aria-label="KFuture"
      >
        <defs>
          <linearGradient id="kf-gradiente" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#22D3EE" />
            <stop offset="55%" stopColor="#A855F7" />
            <stop offset="100%" stopColor="#E935C1" />
          </linearGradient>
        </defs>
 
        {/* Orbita tracejada: gira devagar, como um sistema em operacao */}
        <g className="marca-orbita">
          <circle
            cx="60"
            cy="60"
            r="47"
            stroke="url(#kf-gradiente)"
            strokeWidth="1.5"
            strokeDasharray="3 9"
            opacity="0.55"
          />
          <circle cx="60" cy="13" r="2.6" fill="#22D3EE" />
          <circle cx="101" cy="83" r="2" fill="#E935C1" />
          <circle cx="19" cy="83" r="2" fill="#A855F7" />
        </g>
 
        {/* O K */}
        <g
          stroke="url(#kf-gradiente)"
          strokeWidth="9"
          strokeLinecap="round"
          fill="none"
        >
          <path d="M45 33 L45 87" />
          <path d="M45 61 L75 33" />
          <path d="M49 63 L77 87" />
        </g>
        <circle cx="45" cy="61" r="4" fill="#22D3EE" />
      </svg>
 
      {comTexto && (
        <div className="marca-texto">
          <span className="marca-nome">KFuture</span>
          <span className="marca-linha">ERP</span>
        </div>
      )}
    </div>
  );
}
 
export default Logo;