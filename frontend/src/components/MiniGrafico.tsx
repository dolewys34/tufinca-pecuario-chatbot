import type { Grafico } from "../types";

const COLORES = ["#2e7d46", "#3a9d5d", "#b07b46", "#2f6fb0", "#e0a020", "#7d9a86"];

function formatoValor(valor: number, unidad: string): string {
  if (unidad === "$") return `$${valor.toLocaleString("es-CO")}`;
  if (unidad) return `${valor.toLocaleString("es-CO")} ${unidad}`;
  return valor.toLocaleString("es-CO");
}

export function MiniGrafico({ grafico }: { grafico: Grafico }) {
  const max = Math.max(1, ...grafico.datos.map((d) => d.valor));

  return (
    <div className="mini-grafico">
      <div className="mini-titulo">📊 {grafico.titulo}</div>
      {grafico.datos.map((d, i) => (
        <div className="mini-fila" key={d.etiqueta}>
          <span className="mini-label" title={d.etiqueta}>{d.etiqueta}</span>
          <div className="mini-track">
            <div
              className="mini-fill"
              style={{
                width: `${(d.valor / max) * 100}%`,
                background: COLORES[i % COLORES.length],
              }}
            />
          </div>
          <span className="mini-valor">{formatoValor(d.valor, grafico.unidad)}</span>
        </div>
      ))}
    </div>
  );
}
