import { useEffect, useState } from "react";
import { api } from "../api";
import type { Catalogo, Producto, ProductoCreate } from "../types";

const VACIO: ProductoCreate = { Producto: "", Codigo: "", Valor: undefined, Unidad_Id: undefined, Marca_Id: undefined };

function money(n: number | null): string {
  return n != null ? `$${n.toLocaleString("es-CO")}` : "—";
}

export function InsumosView() {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [unidades, setUnidades] = useState<Catalogo[]>([]);
  const [marcas, setMarcas] = useState<Catalogo[]>([]);
  const [form, setForm] = useState<ProductoCreate>(VACIO);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function cargar() {
    const [p, u, m] = await Promise.all([api.listarProductos(), api.unidades(), api.marcas()]);
    setProductos(p);
    setUnidades(u);
    setMarcas(m);
  }

  useEffect(() => {
    cargar();
  }, []);

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    if (!form.Producto.trim()) {
      setError("El nombre del producto es obligatorio.");
      return;
    }
    setGuardando(true);
    setError(null);
    try {
      await api.crearProducto({
        ...form,
        Valor: form.Valor ? Number(form.Valor) : null,
        Unidad_Id: form.Unidad_Id || null,
        Marca_Id: form.Marca_Id || null,
      });
      setForm(VACIO);
      cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setGuardando(false);
    }
  }

  const stockBajo = productos.filter((p) => p.stock <= 10).length;

  return (
    <>
      <div className="page-header">
        <h1>Insumos e inventario</h1>
        <p>Productos (vacunas, alimentos, medicinas) y su stock disponible</p>
      </div>

      <div className="kpi-grid">
        <div className="kpi">
          <div className="icono tint-verde">📦</div>
          <div className="valor">{productos.length}</div>
          <div className="etiqueta">Productos registrados</div>
        </div>
        <div className="kpi">
          <div className="icono tint-azul">🔢</div>
          <div className="valor">{productos.reduce((s, p) => s + p.stock, 0)}</div>
          <div className="etiqueta">Unidades en inventario</div>
        </div>
        <div className="kpi">
          <div className="icono tint-ambar">⚠️</div>
          <div className="valor">{stockBajo}</div>
          <div className="etiqueta">Productos con stock bajo (≤10)</div>
        </div>
      </div>

      <div className="panel">
        <h2>Registrar nuevo insumo</h2>
        {error && <div className="error-banner">{error}</div>}
        <form className="form-grid" onSubmit={guardar}>
          <div className="field">
            <label>Nombre del producto *</label>
            <input value={form.Producto} onChange={(e) => setForm({ ...form, Producto: e.target.value })} placeholder="Vacuna triple" />
          </div>
          <div className="field">
            <label>Código</label>
            <input value={form.Codigo ?? ""} onChange={(e) => setForm({ ...form, Codigo: e.target.value })} placeholder="INS-006" />
          </div>
          <div className="field">
            <label>Unidad</label>
            <select title="Unidad" value={form.Unidad_Id ?? ""} onChange={(e) => setForm({ ...form, Unidad_Id: e.target.value ? Number(e.target.value) : undefined })}>
              <option value="">—</option>
              {unidades.map((u) => <option key={u.id} value={u.id}>{u.nombre}</option>)}
            </select>
          </div>
          <div className="field">
            <label>Marca</label>
            <select title="Marca" value={form.Marca_Id ?? ""} onChange={(e) => setForm({ ...form, Marca_Id: e.target.value ? Number(e.target.value) : undefined })}>
              <option value="">—</option>
              {marcas.map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
            </select>
          </div>
          <div className="field">
            <label>Valor unitario ($)</label>
            <input type="number" min="0" value={form.Valor ?? ""} onChange={(e) => setForm({ ...form, Valor: e.target.value ? Number(e.target.value) : undefined })} placeholder="12000" />
          </div>
          <button className="btn btn-primary" type="submit" disabled={guardando}>
            {guardando ? "Guardando…" : "+ Agregar insumo"}
          </button>
        </form>
      </div>

      <div className="panel">
        <h2>Productos registrados ({productos.length})</h2>
        <div className="tabla-wrap">
          <table>
            <thead>
              <tr>
                <th>Código</th>
                <th>Producto</th>
                <th>Marca</th>
                <th>Unidad</th>
                <th>Valor</th>
                <th>Stock</th>
              </tr>
            </thead>
            <tbody>
              {productos.length === 0 && (
                <tr><td colSpan={6} className="empty">Aún no hay insumos. Registra el primero arriba.</td></tr>
              )}
              {productos.map((p) => (
                <tr key={p.Id_Producto}>
                  <td><strong>{p.Codigo || "—"}</strong></td>
                  <td>{p.Producto}</td>
                  <td>{p.marca_nombre || "—"}</td>
                  <td>{p.unidad_nombre || "—"}</td>
                  <td>{money(p.Valor)}</td>
                  <td>
                    <span className={`chip ${p.stock <= 10 ? "baja" : "activo"}`}>{p.stock}</span>
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
