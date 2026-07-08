// URL base da API. Em produção vem da variável VITE_API_URL (configurada na Vercel).
// Em desenvolvimento, cai automaticamente no localhost.
export const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Deriva a URL do WebSocket a partir da API:
// http://  -> ws://   |   https:// -> wss://  (resolve a pegadinha do HTTPS)
export const WS_URL = API.replace(/^http/, "ws") + "/ws";