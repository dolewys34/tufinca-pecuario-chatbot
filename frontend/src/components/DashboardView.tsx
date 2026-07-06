import type { Dashboard } from "../types";

function Kpi({ icono, tint, valor, etiqueta }: { icono: string; tint: string; valor: string | number; etiqueta: string }) {
  return (
    <div className="kpi">
      <div className={`icono ${tint}`}>{icono}</div>
      <div className="valor">{valor}</div>
      <div className="etiqueta">{etiqueta}</div>
    </div>
  );
}

function money(n: number): string {
  return `$${n.toLocaleString("es-CO")}`;
}

function Barras({ titulo, datos }: { titulo: string; datos: [string, number][] }) {
  const max = Math.max(1, ...datos.map(([, v]) => v));
  return (
    <div className="panel">
      <h2>{titulo}</h2>
      {datos.length === 0 && <div className="empty">Sin registros aún.</div>}
      {datos.map(([nombre, cant]) => (
        <div className="barra-fila" key={nombre}>
          <span>{nombre}</span>
          <div className="barra-track">
            <div className="barra-fill" style={{ width: `${(cant / max) * 100}%` }} />
          </div>
          <span className="num">{cant}</span>
        </div>
      ))}
    </div>
  );
}

export function DashboardView({ data }: { data: Dashboard }) {
  return (
    <>
      <div className="page-header">
        <h1>Panel de la finca</h1>
        <p>Resumen operativo de la finca El Paraíso · Anzoátegui, Tolima</p>
      </div>

      <div className="kpi-grid">
        <Kpi icono="🐄" tint="tint-verde" valor={data.total_animales} etiqueta="Animales registrados" />
        <Kpi icono="✅" tint="tint-azul" valor={data.total_activos} etiqueta="Animales activos" />
        <Kpi icono="💉" tint="tint-ambar" valor={data.vacunaciones} etiqueta="Vacunaciones registradas" />
        <Kpi icono="🏷️" tint="tint-tierra" valor={money(data.avaluo_total)} etiqueta="Avalúo total" />
        <Kpi icono="📈" tint="tint-verde" valor={money(data.valor_total)} etiqueta="Valor total" />
        <Kpi icono="💰" tint="tint-azul" valor={money(data.costo_total)} etiqueta="Costo total" />
      </div>

      <div className="panel-2col">
        <Barras titulo="Distribución por especie" datos={Object.entries(data.por_especie)} />
        <Barras titulo="Distribución por raza" datos={Object.entries(data.por_raza)} />
      </div>
    </>
  );
}
