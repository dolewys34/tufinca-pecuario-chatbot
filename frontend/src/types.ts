// Tipos alineados con el esquema real Countryland (TuFinca)

export interface Catalogo {
  id: number;
  nombre: string;
}

export interface Animal {
  Id_Animal: number;
  Animal: string;
  Especie_Id: number;
  Raza_Id: number;
  Codigo: string | null;
  Avaluo: number | null;
  Valor: number | null;
  Costo: number | null;
  Estado: string;
  Fecha_Inicio: string;
  Fecha_Fin: string | null;
  Observaciones: string | null;
  especie_nombre: string | null;
  raza_nombre: string | null;
}

export interface AnimalCreate {
  Animal: string;
  Especie_Id: number;
  Raza_Id: number;
  Codigo?: string | null;
  Avaluo?: number | null;
  Valor?: number | null;
  Costo?: number | null;
  Observaciones?: string | null;
}

export interface Producto {
  Id_Producto: number;
  Producto: string;
  Codigo: string | null;
  Valor: number | null;
  Unidad_Id: number | null;
  Marca_Id: number | null;
  Estado: string;
  unidad_nombre: string | null;
  marca_nombre: string | null;
  stock: number;
}

export interface ProductoCreate {
  Producto: string;
  Unidad_Id?: number | null;
  Marca_Id?: number | null;
  Valor?: number | null;
  Codigo?: string | null;
}

export interface Dashboard {
  total_animales: number;
  total_activos: number;
  por_especie: Record<string, number>;
  por_raza: Record<string, number>;
  avaluo_total: number;
  valor_total: number;
  costo_total: number;
  vacunaciones: number;
}

export interface PuntoGrafico {
  etiqueta: string;
  valor: number;
}

export interface Grafico {
  titulo: string;
  tipo: string;
  unidad: string;
  datos: PuntoGrafico[];
}

export interface PuntoUsoDia {
  fecha: string;
  tokens: number;
  llamadas: number;
}

export interface IAEstadisticas {
  conectado: boolean;
  modelo: string;
  endpoint: string;
  total_llamadas: number;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  costo_estimado_usd: number;
  por_dia: PuntoUsoDia[];
}

export interface OpcionChat {
  texto: string;
  valor: string;
}

export interface ChatResponse {
  respuesta: string;
  motor: string;
  graficos: Grafico[];
  opciones: OpcionChat[];
}

export interface ChatMessage {
  autor: "usuario" | "bot";
  texto: string;
  motor?: string;
  graficos?: Grafico[];
  opciones?: OpcionChat[];
}
