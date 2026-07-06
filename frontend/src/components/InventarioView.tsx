import { useEffect, useState } from "react";
import { api } from "../api";
import type { Animal, AnimalCreate, Catalogo } from "../types";

const VACIO: AnimalCreate = {
  Animal: "",
  Especie_Id: 0,
  Raza_Id: 0,
  Codigo: "",
  Avaluo: undefined,
  Valor: undefined,
  Costo: undefined,
};

function money(n: number | null): string {
  return n != null ? `$${n.toLocaleString("es-CO")}` : "—";
}

export function InventarioView({
  animales,
  onCambio,
}: {
  animales: Animal[];
  onCambio: () => void;
}) {
  const [form, setForm] = useState<AnimalCreate>(VACIO);
  const [especies, setEspecies] = useState<Catalogo[]>([]);
  const [razas, setRazas] = useState<Catalogo[]>([]);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.especies(), api.razas()]).then(([e, r]) => {
      setEspecies(e);
      setRazas(r);
      setForm((f) => ({
        ...f,
        Especie_Id: e[0]?.id ?? 0,
        Raza_Id: r[0]?.id ?? 0,
      }));
    });
  }, []);

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    if (!form.Animal.trim()) {
      setError("El nombre/identificación del animal es obligatorio.");
      return;
    }
    if (!form.Especie_Id || !form.Raza_Id) {
      setError("Selecciona especie y raza.");
      return;
    }
    setGuardando(true);
    setError(null);
    try {
      await api.crearAnimal({
        ...form,
        Avaluo: form.Avaluo ? Number(form.Avaluo) : null,
        Valor: form.Valor ? Number(form.Valor) : null,
        Costo: form.Costo ? Number(form.Costo) : null,
      });
      setForm({ ...VACIO, Especie_Id: especies[0]?.id ?? 0, Raza_Id: razas[0]?.id ?? 0 });
      onCambio();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setGuardando(false);
    }
  }

  async function eliminar(id: number, nombre: string) {
    if (!confirm(`¿Eliminar el animal ${nombre}?`)) return;
    await api.eliminarAnimal(id);
    onCambio();
  }

  return (
    <>
      <div className="page-header">
        <h1>Inventario animal</h1>
        <p>Registra y consulta los animales de la finca</p>
      </div>

      <div className="panel">
        <h2>Registrar nuevo animal</h2>
        {error && <div className="error-banner">{error}</div>}
        <form className="form-grid" onSubmit={guardar}>
          <div className="field">
            <label>Nombre / identificación *</label>
            <input
              value={form.Animal}
              onChange={(e) => setForm({ ...form, Animal: e.target.value })}
              placeholder="Vaca 004"
            />
          </div>
          <div className="field">
            <label>Código / arete</label>
            <input
              value={form.Codigo ?? ""}
              onChange={(e) => setForm({ ...form, Codigo: e.target.value })}
              placeholder="BOV-004"
            />
          </div>
          <div className="field">
            <label>Especie *</label>
            <select
              title="Especie"
              value={form.Especie_Id}
              onChange={(e) => setForm({ ...form, Especie_Id: Number(e.target.value) })}
            >
              {especies.map((esp) => (
                <option key={esp.id} value={esp.id}>{esp.nombre}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Raza *</label>
            <select
              title="Raza"
              value={form.Raza_Id}
              onChange={(e) => setForm({ ...form, Raza_Id: Number(e.target.value) })}
            >
              {razas.map((r) => (
                <option key={r.id} value={r.id}>{r.nombre}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Avalúo ($)</label>
            <input type="number" min="0" value={form.Avaluo ?? ""}
              onChange={(e) => setForm({ ...form, Avaluo: e.target.value ? Number(e.target.value) : undefined })}
              placeholder="2500000" />
          </div>
          <div className="field">
            <label>Valor ($)</label>
            <input type="number" min="0" value={form.Valor ?? ""}
              onChange={(e) => setForm({ ...form, Valor: e.target.value ? Number(e.target.value) : undefined })}
              placeholder="2800000" />
          </div>
          <div className="field">
            <label>Costo ($)</label>
            <input type="number" min="0" value={form.Costo ?? ""}
              onChange={(e) => setForm({ ...form, Costo: e.target.value ? Number(e.target.value) : undefined })}
              placeholder="1900000" />
          </div>
          <button className="btn btn-primary" type="submit" disabled={guardando}>
            {guardando ? "Guardando…" : "+ Agregar animal"}
          </button>
        </form>
      </div>

      <div className="panel">
        <h2>Animales registrados ({animales.length})</h2>
        <div className="tabla-wrap">
          <table>
            <thead>
              <tr>
                <th>Código</th>
                <th>Nombre</th>
                <th>Especie</th>
                <th>Raza</th>
                <th>Avalúo</th>
                <th>Valor</th>
                <th>Costo</th>
                <th>Estado</th>
                <th aria-label="Acciones"></th>
              </tr>
            </thead>
            <tbody>
              {animales.length === 0 && (
                <tr>
                  <td colSpan={9} className="empty">Aún no hay animales. Registra el primero arriba.</td>
                </tr>
              )}
              {animales.map((a) => (
                <tr key={a.Id_Animal}>
                  <td><strong>{a.Codigo || "—"}</strong></td>
                  <td>{a.Animal}</td>
                  <td><span className="chip especie">{a.especie_nombre || "—"}</span></td>
                  <td>{a.raza_nombre || "—"}</td>
                  <td>{money(a.Avaluo)}</td>
                  <td>{money(a.Valor)}</td>
                  <td>{money(a.Costo)}</td>
                  <td>
                    <span className={`chip ${a.Estado === "A" ? "activo" : "baja"}`}>
                      {a.Estado === "A" ? "Activo" : "Inactivo"}
                    </span>
                  </td>
                  <td>
                    <button type="button" className="btn-ghost" onClick={() => eliminar(a.Id_Animal, a.Animal)} title="Eliminar">
                      🗑
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
