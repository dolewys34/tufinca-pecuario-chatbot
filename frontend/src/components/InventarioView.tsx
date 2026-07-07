import { useEffect, useState } from "react";
import { api } from "../api";
import type { Animal, AnimalCreate, Catalogo, DetalleAnimal } from "../types";

const VACIO: AnimalCreate = {
  Animal: "",
  Especie_Id: 0,
  Raza_Id: 0,
  Codigo: "",
  Sexo: "H",
  Peso: undefined,
  Fecha_Nacimiento: undefined,
  Avaluo: undefined,
  Valor: undefined,
  Costo: undefined,
};

function money(n: number | null): string {
  return n != null ? `$${n.toLocaleString("es-CO")}` : "—";
}

function fecha(f: string | null): string {
  return f ? f.slice(0, 10) : "—";
}

// Ficha del animal con su historial de eventos (RF-27 del ACA 2).
function FichaAnimal({ animal, onCerrar }: { animal: Animal; onCerrar: () => void }) {
  const [eventos, setEventos] = useState<DetalleAnimal[] | null>(null);

  useEffect(() => {
    api.historialAnimal(animal.Id_Animal).then(setEventos).catch(() => setEventos([]));
  }, [animal.Id_Animal]);

  return (
    <div className="modal-fondo" onClick={onCerrar}>
      <div className="modal-ficha" onClick={(e) => e.stopPropagation()}>
        <div className="ficha-head">
          <h2>🐄 {animal.Animal} {animal.Codigo ? `· ${animal.Codigo}` : ""}</h2>
          <button type="button" className="cerrar-ficha" onClick={onCerrar}>×</button>
        </div>
        <div className="ficha-datos">
          <div><span>Especie</span><b>{animal.especie_nombre ?? "—"}</b></div>
          <div><span>Raza</span><b>{animal.raza_nombre ?? "—"}</b></div>
          <div><span>Sexo</span><b>{animal.Sexo === "M" ? "Macho" : animal.Sexo === "H" ? "Hembra" : "—"}</b></div>
          <div><span>Peso</span><b>{animal.Peso ? `${animal.Peso} kg` : "—"}</b></div>
          <div><span>Nacimiento</span><b>{fecha(animal.Fecha_Nacimiento)}</b></div>
          <div><span>Valor</span><b>{money(animal.Valor)}</b></div>
          <div><span>Avalúo</span><b>{money(animal.Avaluo)}</b></div>
          <div><span>Estado</span><b>{animal.Estado === "A" ? "Activo" : "Inactivo"}</b></div>
        </div>
        <h3>📋 Historial de eventos ({eventos?.length ?? "…"})</h3>
        {eventos === null && <div className="loading">Cargando historial…</div>}
        {eventos !== null && eventos.length === 0 && (
          <div className="empty">Este animal aún no tiene eventos registrados.</div>
        )}
        {eventos !== null && eventos.length > 0 && (
          <div className="tabla-wrap">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Proceso</th>
                  <th>Vacuna</th>
                  <th>Responsable</th>
                  <th>Próxima</th>
                  <th>Costo</th>
                  <th>Observaciones</th>
                </tr>
              </thead>
              <tbody>
                {eventos.map((e) => (
                  <tr key={e.Id_Detalle_Animal}>
                    <td>{fecha(e.Fecha_Inicio)}</td>
                    <td><span className="chip especie">{e.proceso_nombre ?? "—"}</span></td>
                    <td>{e.tipo_vacunacion_nombre ?? "—"}</td>
                    <td>{e.Responsable ?? "—"}</td>
                    <td>{fecha(e.Fecha_Fin)}</td>
                    <td>{money(e.Costo)}</td>
                    <td>{e.Observaciones ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
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
  const [ficha, setFicha] = useState<Animal | null>(null);

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
        Peso: form.Peso ? Number(form.Peso) : null,
        Fecha_Nacimiento: form.Fecha_Nacimiento || null,
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
            <label>Sexo</label>
            <select
              title="Sexo"
              value={form.Sexo ?? "H"}
              onChange={(e) => setForm({ ...form, Sexo: e.target.value })}
            >
              <option value="H">Hembra</option>
              <option value="M">Macho</option>
            </select>
          </div>
          <div className="field">
            <label>Peso (kg)</label>
            <input type="number" min="0" step="0.1" value={form.Peso ?? ""}
              onChange={(e) => setForm({ ...form, Peso: e.target.value ? Number(e.target.value) : undefined })}
              placeholder="380" />
          </div>
          <div className="field">
            <label>Fecha de nacimiento</label>
            <input type="date" title="Fecha de nacimiento" value={form.Fecha_Nacimiento?.slice(0, 10) ?? ""}
              onChange={(e) => setForm({ ...form, Fecha_Nacimiento: e.target.value ? `${e.target.value}T00:00:00` : undefined })} />
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
                <th>Sexo</th>
                <th>Peso</th>
                <th>Valor</th>
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
                <tr key={a.Id_Animal} className="fila-clic" onClick={() => setFicha(a)} title="Ver ficha e historial">
                  <td><strong>{a.Codigo || "—"}</strong></td>
                  <td>{a.Animal}</td>
                  <td><span className="chip especie">{a.especie_nombre || "—"}</span></td>
                  <td>{a.raza_nombre || "—"}</td>
                  <td>{a.Sexo === "M" ? "♂ M" : a.Sexo === "H" ? "♀ H" : "—"}</td>
                  <td>{a.Peso ? `${a.Peso} kg` : "—"}</td>
                  <td>{money(a.Valor)}</td>
                  <td>
                    <span className={`chip ${a.Estado === "A" ? "activo" : "baja"}`}>
                      {a.Estado === "A" ? "Activo" : "Inactivo"}
                    </span>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="btn-ghost"
                      onClick={(e) => { e.stopPropagation(); eliminar(a.Id_Animal, a.Animal); }}
                      title="Eliminar"
                    >
                      🗑
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {ficha && <FichaAnimal animal={ficha} onCerrar={() => setFicha(null)} />}
    </>
  );
}
