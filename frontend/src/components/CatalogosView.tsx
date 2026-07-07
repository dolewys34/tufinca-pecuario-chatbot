import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { Catalogo } from "../types";

// Gestión de catálogos del módulo pecuario (RF-22, RF-23, RF-25, RF-26 del ACA 2).
const CATALOGOS: { clave: string; titulo: string; icono: string; rf: string }[] = [
  { clave: "especies", titulo: "Especies", icono: "🐄", rf: "RF-22" },
  { clave: "razas", titulo: "Razas", icono: "🧬", rf: "RF-23" },
  { clave: "tipos-vacunacion", titulo: "Tipos de vacunación", icono: "💉", rf: "RF-25" },
  { clave: "procesos-pecuarios", titulo: "Procesos pecuarios", icono: "⚙️", rf: "RF-26" },
];

function TarjetaCatalogo({ clave, titulo, icono, rf }: (typeof CATALOGOS)[number]) {
  const [items, setItems] = useState<Catalogo[]>([]);
  const [nuevo, setNuevo] = useState("");
  const [editando, setEditando] = useState<Catalogo | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(() => {
    api.catalogo(clave).then(setItems).catch(() => setItems([]));
  }, [clave]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  async function agregar(e: React.FormEvent) {
    e.preventDefault();
    if (!nuevo.trim()) return;
    setError(null);
    try {
      await api.crearCatalogo(clave, nuevo.trim());
      setNuevo("");
      cargar();
    } catch (err) {
      setError(err instanceof Error && err.message.includes("409") ? "Ya existe." : "Error al guardar.");
    }
  }

  async function renombrar(e: React.FormEvent) {
    e.preventDefault();
    if (!editando || !editando.nombre.trim()) return;
    await api.renombrarCatalogo(clave, editando.id, editando.nombre.trim());
    setEditando(null);
    cargar();
  }

  async function eliminar(item: Catalogo) {
    if (!confirm(`¿Eliminar "${item.nombre}"?`)) return;
    setError(null);
    try {
      await api.eliminarCatalogo(clave, item.id);
      cargar();
    } catch {
      setError(`No se puede eliminar "${item.nombre}": tiene registros asociados.`);
    }
  }

  return (
    <div className="panel">
      <h2>
        {icono} {titulo} <span className="rf-tag">{rf}</span>
      </h2>
      {error && <div className="error-banner">{error}</div>}
      <form className="fila-agregar" onSubmit={agregar}>
        <input
          value={nuevo}
          onChange={(e) => setNuevo(e.target.value)}
          placeholder={`Nueva ${titulo.toLowerCase().replace(/s$/, "")}…`}
        />
        <button type="submit" className="btn btn-primary">+</button>
      </form>
      <ul className="lista-catalogo">
        {items.map((item) => (
          <li key={item.id}>
            {editando?.id === item.id ? (
              <form className="fila-agregar" onSubmit={renombrar}>
                <input
                  value={editando.nombre}
                  onChange={(e) => setEditando({ ...editando, nombre: e.target.value })}
                  aria-label="Nuevo nombre"
                />
                <button type="submit" className="btn btn-primary">✓</button>
                <button type="button" className="btn-ghost" onClick={() => setEditando(null)}>×</button>
              </form>
            ) : (
              <>
                <span>{item.nombre}</span>
                <span className="acciones">
                  <button type="button" className="btn-ghost" title="Renombrar" onClick={() => setEditando(item)}>✏️</button>
                  <button type="button" className="btn-ghost" title="Eliminar" onClick={() => eliminar(item)}>🗑</button>
                </span>
              </>
            )}
          </li>
        ))}
        {items.length === 0 && <li className="empty">Sin registros.</li>}
      </ul>
    </div>
  );
}

export function CatalogosView() {
  return (
    <>
      <div className="page-header">
        <h1>Catálogos del módulo pecuario</h1>
        <p>Gestión de especies, razas, tipos de vacunación y procesos (RF-22 a RF-26)</p>
      </div>
      <div className="grid-catalogos">
        {CATALOGOS.map((c) => (
          <TarjetaCatalogo key={c.clave} {...c} />
        ))}
      </div>
    </>
  );
}
