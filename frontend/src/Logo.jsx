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
          <linearGradient
            id="kf-gradiente"
            gradientUnits="userSpaceOnUse"
            x1="30"
            y1="25"
            x2="85"
            y2="95"
          >
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
          <path d="M40 32 L40 88" />
          <path d="M40 62 L72 32" />
          <path d="M40 62 L74 88" />
        </g>
        <circle cx="40" cy="62" r="3.4" fill="#22D3EE" />
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