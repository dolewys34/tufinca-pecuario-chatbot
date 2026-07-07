import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { ChatMessage } from "../types";
import { MiniGrafico } from "./MiniGrafico";

// Nombres amigables de las herramientas del agente (para mostrar transparencia).
const NOMBRE_HERRAMIENTA: Record<string, string> = {
  resumen_finca: "resumen de la finca",
  buscar_animales: "inventario de animales",
  consultar_inventario: "insumos y stock",
  registrar_animal: "registro de animal",
  registrar_vacunacion: "registro de vacunación",
  registrar_alimentacion: "registro de alimentación",
  registrar_proceso: "registro de proceso pecuario",
  actualizar_animal: "actualización del animal",
  alertas_finca: "alertas de la finca",
  historial_animal: "historial del animal",
  generar_grafico: "estadísticas",
};

// Renderiza **negritas** dentro de una línea.
function renderInline(t: string, key?: number) {
  return t.split(/(\*\*[^*]+\*\*)/g).map((p, j) =>
    p.startsWith("**") && p.endsWith("**") ? (
      <strong key={`${key}-${j}`}>{p.slice(2, -2)}</strong>
    ) : (
      <span key={`${key}-${j}`}>{p}</span>
    )
  );
}

// Mini-markdown del chat: viñetas (-, *, •, 1.), títulos (#) y negritas,
// para que las respuestas de la IA se vean organizadas.
function texto_formateado(texto: string) {
  const lineas = texto.split("\n");
  const salida: React.ReactNode[] = [];
  let items: string[] = [];

  const cerrarLista = () => {
    if (items.length) {
      salida.push(
        <ul className="lista-chat" key={`ul-${salida.length}`}>
          {items.map((li, i) => (
            <li key={i}>{renderInline(li, i)}</li>
          ))}
        </ul>
      );
      items = [];
    }
  };

  lineas.forEach((linea, i) => {
    const vineta = linea.match(/^\s*(?:[-*•]|\d+[.)])\s+(.*)/);
    if (vineta) {
      items.push(vineta[1]);
      return;
    }
    cerrarLista();
    if (linea.trim() === "") {
      salida.push(<div className="salto-chat" key={`s-${i}`} />);
    } else if (/^#{1,4}\s/.test(linea)) {
      salida.push(
        <div className="titulo-chat" key={i}>
          {renderInline(linea.replace(/^#{1,4}\s*/, ""), i)}
        </div>
      );
    } else {
      salida.push(<div key={i}>{renderInline(linea, i)}</div>);
    }
  });
  cerrarLista();
  return salida;
}

const CLAVE_SESION = "tufinca-chat-sesion";
const CLAVE_MENSAJES = "tufinca-chat-mensajes";

function cargarMensajesGuardados(): ChatMessage[] {
  try {
    return JSON.parse(localStorage.getItem(CLAVE_MENSAJES) ?? "[]");
  } catch {
    return [];
  }
}

const nuevoIdSesion = () => `web-${Math.random().toString(36).slice(2)}-${Date.now()}`;

const horaActual = () =>
  new Date().toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });

// Reduce la foto a máx. 1024px (JPEG) para ahorrar tokens y ancho de banda.
function reducirImagen(archivo: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const escala = Math.min(1, 1024 / Math.max(img.width, img.height));
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(img.width * escala);
      canvas.height = Math.round(img.height * escala);
      canvas.getContext("2d")!.drawImage(img, 0, 0, canvas.width, canvas.height);
      resolve(canvas.toDataURL("image/jpeg", 0.8));
      URL.revokeObjectURL(img.src);
    };
    img.onerror = reject;
    img.src = URL.createObjectURL(archivo);
  });
}

export function ChatWidget() {
  const [abierto, setAbierto] = useState(false);
  const [mensajes, setMensajes] = useState<ChatMessage[]>(cargarMensajesGuardados);
  const [texto, setTexto] = useState("");
  const [foto, setFoto] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const bodyRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // Sesión persistente: sobrevive a recargas de página (la memoria del agente
  // y la conversación no se pierden).
  const [sessionId, setSessionId] = useState(() => {
    let s = localStorage.getItem(CLAVE_SESION);
    if (!s) {
      s = nuevoIdSesion();
      localStorage.setItem(CLAVE_SESION, s);
    }
    return s;
  });

  // Borra la conversación y arranca una sesión nueva (memoria limpia).
  function nuevaConversacion() {
    localStorage.removeItem(CLAVE_MENSAJES);
    const s = nuevoIdSesion();
    localStorage.setItem(CLAVE_SESION, s);
    setMensajes([]);
    setFoto(null);
    setSessionId(s); // dispara el saludo inicial de nuevo
  }

  // Guarda la conversación (últimos 50 mensajes) al cambiar.
  useEffect(() => {
    localStorage.setItem(CLAVE_MENSAJES, JSON.stringify(mensajes.slice(-50)));
  }, [mensajes]);

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: "smooth" });
  }, [mensajes, cargando]);

  // Al abrir por primera vez (o tras "nueva conversación"), saludamos con el menú.
  useEffect(() => {
    if (abierto && mensajes.length === 0) {
      enviar("hola", true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [abierto, sessionId]);

  // `mostrar` es lo que ve el usuario en su burbuja; `mensaje` es lo que se envía
  // al servidor (para opciones con valores internos como "__esp:1").
  async function enviar(mensaje: string, oculto = false, mostrar?: string) {
    const q = mensaje.trim() || (foto ? "Analiza esta imagen" : "");
    if (!q || cargando) return;
    const imagen = foto;
    setTexto("");
    setFoto(null);
    if (!oculto) {
      setMensajes((m) => [
        ...m,
        { autor: "usuario", texto: mostrar ?? q, imagen: imagen ?? undefined, hora: horaActual() },
      ]);
    }
    setCargando(true);
    try {
      const r = await api.chat(q, sessionId, imagen);
      setMensajes((m) => [
        ...m,
        {
          autor: "bot",
          texto: r.respuesta,
          motor: r.motor,
          graficos: r.graficos,
          opciones: r.opciones,
          herramientas: r.herramientas,
          hora: horaActual(),
        },
      ]);
    } catch {
      setMensajes((m) => [
        ...m,
        {
          autor: "bot",
          texto: "Ups, no pude conectar con el servidor. Intenta de nuevo.",
          hora: horaActual(),
        },
      ]);
    } finally {
      setCargando(false);
    }
  }

  if (!abierto) {
    return (
      <button type="button" className="chat-fab" onClick={() => setAbierto(true)} title="Abrir chat">
        💬
      </button>
    );
  }

  // Las opciones activas son las del último mensaje del bot.
  const ultimoBot = [...mensajes].reverse().find((m) => m.autor === "bot");
  const opcionesActivas = !cargando ? ultimoBot?.opciones ?? [] : [];

  return (
    <div className="chat-panel">
      <div className="chat-head">
        <div className="avatar">
          🐄<span className="punto-online" />
        </div>
        <div>
          <div className="titulo">TuFinca Bot</div>
          <div className="estado">En línea · Asistente agropecuario</div>
        </div>
        <button
          type="button"
          className="accion-head"
          title="Nueva conversación"
          onClick={nuevaConversacion}
        >
          🗑
        </button>
        <button type="button" className="accion-head cerrar" title="Cerrar" onClick={() => setAbierto(false)}>
          ×
        </button>
      </div>

      <div className="chat-body" ref={bodyRef}>
        {mensajes.map((m, i) => (
          <div key={i} className={`burbuja ${m.autor}`}>
            {m.herramientas && m.herramientas.length > 0 && (
              <div className="herramientas-ia">
                🔎 La IA consultó:{" "}
                {[...new Set(m.herramientas)]
                  .map((h) => NOMBRE_HERRAMIENTA[h] ?? h)
                  .join(", ")}
              </div>
            )}
            {m.imagen && <img src={m.imagen} alt="Foto enviada" className="foto-chat" />}
            {texto_formateado(m.texto)}
            {m.graficos && m.graficos.length > 0 && (
              <div className="graficos-chat">
                {m.graficos.map((g, gi) => (
                  <MiniGrafico grafico={g} key={gi} />
                ))}
              </div>
            )}
            <span className="pie-burbuja">
              {m.motor === "azure-ai-foundry" && <span className="motor">⚡ Azure AI Foundry</span>}
              {m.motor === "reglas" && <span className="motor">⚙️ reglas</span>}
              {m.hora && <span className="hora">{m.hora}</span>}
            </span>
          </div>
        ))}
        {cargando && (
          <div className="burbuja bot escribiendo">
            <span className="punto" />
            <span className="punto" />
            <span className="punto" />
          </div>
        )}
      </div>

      {opcionesActivas.length > 0 && (
        <div className="opciones-chat">
          {opcionesActivas.map((o) => (
            <button type="button" key={o.valor} className="opcion-chat" onClick={() => enviar(o.valor, false, o.texto)}>
              {o.texto}
            </button>
          ))}
        </div>
      )}

      {foto && (
        <div className="foto-preview">
          <img src={foto} alt="Foto adjunta" />
          <span>Foto lista para enviar</span>
          <button type="button" onClick={() => setFoto(null)}>×</button>
        </div>
      )}

      <form
        className="chat-input"
        onSubmit={(e) => {
          e.preventDefault();
          enviar(texto);
        }}
      >
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          title="Adjuntar foto"
          aria-label="Adjuntar foto"
          className="oculto"
          onChange={async (e) => {
            const f = e.target.files?.[0];
            if (f) setFoto(await reducirImagen(f));
            e.target.value = "";
          }}
        />
        <button
          type="button"
          className="adjuntar"
          title="Adjuntar foto (animal, factura...)"
          onClick={() => fileRef.current?.click()}
        >
          📎
        </button>
        <input
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder={foto ? "Describe la foto (opcional)…" : "Escribe tu pregunta…"}
        />
        <button type="submit" disabled={cargando}>
          ➤
        </button>
      </form>
    </div>
  );
}
