import { useEffect, useState } from "react";
import { api } from "../api";
import type { IAEstadisticas } from "../types";

export function IAPanelView() {
  const [data, setData] = useState<IAEstadisticas | null>(null);

  async function cargar() {
    setData(await api.iaEstadisticas());
  }

  useEffect(() => {
    cargar();
    const t = setInterval(cargar, 10000); // refresca cada 10s
    return () => clearInterval(t);
  }, []);

  if (!data) return <div className="loading">Cargando analítica de IA…</div>;

  const maxTok = Math.max(1, ...data.por_dia.map((d) => d.tokens));

  return (
    <>
      <div className="page-header">
        <h1>Panel de IA</h1>
        <p>Consumo del modelo de Azure AI Foundry en tiempo real</p>
      </div>

      <div className="panel" style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <div className={`icono ${data.conectado ? "tint-verde" : "tint-ambar"}`} style={{ width: 46, height: 46, borderRadius: 12, display: "grid", placeItems: "center", fontSize: "1.3rem" }}>
          {data.conectado ? "⚡" : "⚙️"}
        </div>
        <div>
          <strong>{data.conectado ? "Azure AI Foundry conectado" : "Modo reglas (IA no conectada)"}</strong>
          <div style={{ color: "var(--texto-suave)", fontSize: "0.85rem" }}>
            Modelo: <b>{data.modelo}</b>{data.endpoint ? ` · ${data.endpoint}` : ""}
          </div>
        </div>
      </div>

      <div className="kpi-grid">
        <div className="kpi">
          <div className="icono tint-azul">💬</div>
          <div className="valor">{data.total_llamadas}</div>
          <div className="etiqueta">Consultas al modelo</div>
        </div>
        <div className="kpi">
          <div className="icono tint-verde">🔢</div>
          <div className="valor">{data.total_tokens.toLocaleString("es-CO")}</div>
          <div className="etiqueta">Tokens totales</div>
        </div>
        <div className="kpi">
          <div className="icono tint-tierra">📥</div>
          <div className="valor">{data.prompt_tokens.toLocaleString("es-CO")}</div>
          <div className="etiqueta">Tokens de entrada</div>
        </div>
        <div className="kpi">
          <div className="icono tint-ambar">📤</div>
          <div className="valor">{data.completion_tokens.toLocaleString("es-CO")}</div>
          <div className="etiqueta">Tokens de respuesta</div>
        </div>
        <div className="kpi">
          <div className="icono tint-verde">💵</div>
          <div className="valor">${data.costo_estimado_usd.toFixed(4)}</div>
          <div className="etiqueta">Costo estimado (USD)</div>
        </div>
      </div>

      <div className="panel">
        <h2>Consumo de tokens por día</h2>
        {data.por_dia.length === 0 && (
          <div className="empty">Aún no hay consultas al modelo. Abre el chat 💬 y hazle una pregunta.</div>
        )}
        {data.por_dia.map((d) => (
          <div className="barra-fila" key={d.fecha}>
            <span>{d.fecha}</span>
            <div className="barra-track">
              <div className="barra-fill" style={{ width: `${(d.tokens / maxTok) * 100}%` }} />
            </div>
            <span className="num">{d.tokens.toLocaleString("es-CO")}</span>
          </div>
        ))}
      </div>

      <div className="panel" style={{ fontSize: "0.85rem", color: "var(--texto-suave)" }}>
        ℹ️ El costo es una <b>estimación</b> con las tarifas de gpt-4.1-mini. Los datos oficiales
        de facturación están en el portal de Azure (Cost Management). Esta analítica se actualiza
        cada 10 segundos.
      </div>
    </>
  );
}
