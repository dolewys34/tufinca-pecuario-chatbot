import type { Alerta, Animal, AnimalCreate, Catalogo, ChatResponse, Dashboard, IAEstadisticas, Producto, ProductoCreate } from "./types";

async function req<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Error ${res.status}: ${detail}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  health: () => req<{ status: string; ia: string }>("/api/health"),
  dashboard: () => req<Dashboard>("/api/dashboard"),
  especies: () => req<Catalogo[]>("/api/especies"),
  razas: () => req<Catalogo[]>("/api/razas"),
  listarAnimales: () => req<Animal[]>("/api/animales"),
  crearAnimal: (datos: AnimalCreate) =>
    req<Animal>("/api/animales", { method: "POST", body: JSON.stringify(datos) }),
  eliminarAnimal: (id: number) =>
    req<void>(`/api/animales/${id}`, { method: "DELETE" }),
  unidades: () => req<Catalogo[]>("/api/unidades"),
  marcas: () => req<Catalogo[]>("/api/marcas"),
  listarProductos: () => req<Producto[]>("/api/productos"),
  crearProducto: (datos: ProductoCreate) =>
    req<Producto>("/api/productos", { method: "POST", body: JSON.stringify(datos) }),
  alertas: () => req<Alerta[]>("/api/alertas"),
  iaEstadisticas: () => req<IAEstadisticas>("/api/ia/estadisticas"),
  chat: (mensaje: string, session_id: string, imagen?: string | null) =>
    req<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ mensaje, session_id, imagen: imagen ?? null }),
    }),
};
