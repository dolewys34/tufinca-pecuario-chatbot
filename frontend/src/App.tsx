import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { Animal, Dashboard } from "./types";
import { DashboardView } from "./components/DashboardView";
import { InventarioView } from "./components/InventarioView";
import { InsumosView } from "./components/InsumosView";
import { CatalogosView } from "./components/CatalogosView";
import { IndicadoresView } from "./components/IndicadoresView";
import { IAPanelView } from "./components/IAPanelView";
import { ChatWidget } from "./components/ChatWidget";

type Vista = "dashboard" | "inventario" | "insumos" | "catalogos" | "indicadores" | "ia";

export default function App() {
  const [vista, setVista] = useState<Vista>("dashboard");
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [animales, setAnimales] = useState<Animal[]>([]);
  const [ia, setIa] = useState<string>("reglas");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    try {
      const [h, d, a] = await Promise.all([
        api.health(),
        api.dashboard(),
        api.listarAnimales(),
      ]);
      setIa(h.ia);
      setDashboard(d);
      setAnimales(a);
      setError(null);
    } catch {
      setError(
        "No se pudo conectar con el servidor. Verifica que el backend esté corriendo en el puerto 8000."
      );
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    cargar();
  }, [cargar]);

  const iaOn = ia === "azure-ai-foundry";

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo">🌾</div>
          <div>
            <span>TuFinca</span>
            <small>PECUARIO + IA</small>
          </div>
        </div>

        <button
          type="button"
          className={`nav-item ${vista === "dashboard" ? "activo" : ""}`}
          onClick={() => setVista("dashboard")}
        >
          📊 <span>Panel</span>
        </button>
        <button
          type="button"
          className={`nav-item ${vista === "inventario" ? "activo" : ""}`}
          onClick={() => setVista("inventario")}
        >
          🐄 <span>Inventario</span>
        </button>
        <button
          type="button"
          className={`nav-item ${vista === "insumos" ? "activo" : ""}`}
          onClick={() => setVista("insumos")}
        >
          📦 <span>Insumos</span>
        </button>
        <button
          type="button"
          className={`nav-item ${vista === "catalogos" ? "activo" : ""}`}
          onClick={() => setVista("catalogos")}
        >
          🗂️ <span>Catálogos</span>
        </button>
        <button
          type="button"
          className={`nav-item ${vista === "indicadores" ? "activo" : ""}`}
          onClick={() => setVista("indicadores")}
        >
          🎯 <span>Indicadores</span>
        </button>
        <button
          type="button"
          className={`nav-item ${vista === "ia" ? "activo" : ""}`}
          onClick={() => setVista("ia")}
        >
          🤖 <span>Panel de IA</span>
        </button>

        <div className="sidebar-foot">
          <div className={`ia-badge ${iaOn ? "on" : "off"}`}>
            {iaOn ? "⚡ IA activa" : "⚙️ IA en modo reglas"}
          </div>
          <div className="finca-info">Finca El Paraíso</div>
          <div>Anzoátegui, Tolima</div>
        </div>
      </aside>

      <main className="main">
        {error && <div className="error-banner">{error}</div>}
        {cargando && <div className="loading">Cargando datos de la finca…</div>}

        {!cargando && vista === "dashboard" && dashboard && (
          <DashboardView data={dashboard} />
        )}
        {!cargando && vista === "inventario" && (
          <InventarioView animales={animales} onCambio={cargar} />
        )}
        {!cargando && vista === "insumos" && <InsumosView />}
        {!cargando && vista === "catalogos" && <CatalogosView />}
        {!cargando && vista === "indicadores" && <IndicadoresView />}
        {!cargando && vista === "ia" && <IAPanelView />}
      </main>

      <ChatWidget />
    </div>
  );
}
