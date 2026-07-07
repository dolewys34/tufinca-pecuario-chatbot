import { useEffect, useState } from "react";
import { api } from "../api";
import type { Indicadores } from "../types";

// Indicadores de la evaluación comparativa del Objetivo Específico 4
// (ACA 2, Tabla 16): eficiencia operativa y trazabilidad de la información.

function Medidor({ valor, etiqueta, meta }: { valor: number; etiqueta: string; meta: string }) {
  const color = valor >= 80 ? "var(--verde-500)" : valor >= 50 ? "var(--ambar)" : "var(--rojo)";
  return (
    <div className="panel medidor">
      <div className="medidor-valor" style={{ color }}>{valor}%</div>
      <div className="barra-track">
        <div className="barra-fill" style={{ width: `${valor}%`, background: color }} />
      </div>
      <div className="medidor-etiqueta"><b>{etiqueta}</b></div>
      <div className="medidor-meta">{meta}</div>
    </div>
  );
}

export function IndicadoresView() {
  const [data, setData] = useState<Indicadores | null>(null);

  useEffect(() => {
    api.indicadores().then(setData).catch(() => setData(null));
  }, []);

  if (!data) return <div className="loading">Cargando indicadores…</div>;

  return (
    <>
      <div className="page-header">
        <h1>Indicadores de evaluación</h1>
        <p>
          Evaluación comparativa del Objetivo Específico 4 · trazabilidad y eficiencia
          operativa (línea base manual → sistema TuFinca)
        </p>
      </div>

      <div className="kpi-grid">
        <div className="kpi">
          <div className="icono tint-verde">🐄</div>
          <div className="valor">{data.total_animales}</div>
          <div className="etiqueta">Animales en el sistema</div>
        </div>
        <div className="kpi">
          <div className="icono tint-azul">📋</div>
          <div className="valor">{data.total_eventos}</div>
          <div className="etiqueta">Eventos pecuarios registrados</div>
        </div>
        <div className="kpi">
          <div className="icono tint-verde">💉</div>
          <div className="valor">{data.vacunas_al_dia}</div>
          <div className="etiqueta">Vacunas al día</div>
        </div>
        <div className="kpi">
          <div className="icono tint-ambar">⏰</div>
          <div className="valor">{data.vacunas_proximas}</div>
          <div className="etiqueta">Vacunas próximas (30 días)</div>
        </div>
        <div className="kpi">
          <div className="icono tint-tierra">🚨</div>
          <div className="valor">{data.vacunas_vencidas}</div>
          <div className="etiqueta">Vacunas vencidas</div>
        </div>
      </div>

      <div className="grid-medidores">
        <Medidor
          valor={data.registros_completos_pct}
          etiqueta="Registros completos"
          meta="Animales con código, sexo, peso, nacimiento, especie y raza (Figura 17)"
        />
        <Medidor
          valor={data.animales_con_historial_pct}
          etiqueta="Disponibilidad del historial"
          meta="Animales con al menos un evento registrado (trazabilidad)"
        />
        <Medidor
          valor={data.eventos_con_responsable_pct}
          etiqueta="Eventos con responsable"
          meta="Trazabilidad del responsable de cada actividad (Figura 18)"
        />
      </div>

      <div className="panel nota-metodo">
        ℹ️ Estos indicadores corresponden a la <b>medición posterior (sistema)</b> definida en la
        Tabla 16 del proyecto. La comparación contra la línea base manual (tiempos de registro y
        consulta en cuadernos físicos) se documenta en el trabajo de campo de la Fase II.
      </div>
    </>
  );
}
