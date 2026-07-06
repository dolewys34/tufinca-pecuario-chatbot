import { useEffect, useMemo, useRef, useState } from "react";
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
  generar_grafico: "estadísticas",
};

// Renderiza **negritas** y saltos de línea de forma simple.
function texto_formateado(texto: string) {
  return texto.split("\n").map((linea, i) => {
    const partes = linea.split(/(\*\*[^*]+\*\*)/g);
    return (
      <div key={i}>
        {partes.map((p, j) =>
          p.startsWith("**") && p.endsWith("**") ? (
            <strong key={j}>{p.slice(2, -2)}</strong>
          ) : (
            <span key={j}>{p}</span>
          )
        )}
      </div>
    );
  });
}

export function ChatWidget() {
  const [abierto, setAbierto] = useState(false);
  const [mensajes, setMensajes] = useState<ChatMessage[]>([]);
  const [texto, setTexto] = useState("");
  const [cargando, setCargando] = useState(false);
  const bodyRef = useRef<HTMLDivElement>(null);

  // Un id de sesión estable por pestaña (mantiene el estado de los flujos guiados).
  const sessionId = useMemo(
    () => `web-${Math.random().toString(36).slice(2)}-${Date.now()}`,
    []
  );

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: "smooth" });
  }, [mensajes, cargando]);

  // Al abrir por primera vez, saludamos con el menú.
  useEffect(() => {
    if (abierto && mensajes.length === 0) {
      enviar("hola", true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [abierto]);

  // `mostrar` es lo que ve el usuario en su burbuja; `mensaje` es lo que se envía
  // al servidor (para opciones con valores internos como "__esp:1").
  async function enviar(mensaje: string, oculto = false, mostrar?: string) {
    const q = mensaje.trim();
    if (!q || cargando) return;
    setTexto("");
    if (!oculto) {
      setMensajes((m) => [...m, { autor: "usuario", texto: mostrar ?? q }]);
    }
    setCargando(true);
    try {
      const r = await api.chat(q, sessionId);
      setMensajes((m) => [
        ...m,
        {
          autor: "bot",
          texto: r.respuesta,
          motor: r.motor,
          graficos: r.graficos,
          opciones: r.opciones,
          herramientas: r.herramientas,
        },
      ]);
    } catch {
      setMensajes((m) => [
        ...m,
        { autor: "bot", texto: "Ups, no pude conectar con el servidor. Intenta de nuevo." },
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
        <div className="avatar">🐄</div>
        <div>
          <div className="titulo">TuFinca Bot</div>
          <div className="estado">Asistente agropecuario</div>
        </div>
        <button type="button" className="cerrar" onClick={() => setAbierto(false)}>
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
            {texto_formateado(m.texto)}
            {m.graficos && m.graficos.length > 0 && (
              <div className="graficos-chat">
                {m.graficos.map((g, gi) => (
                  <MiniGrafico grafico={g} key={gi} />
                ))}
              </div>
            )}
            {m.motor && m.motor !== "asistente" && (
              <span className="motor">
                {m.motor === "azure-ai-foundry" ? "⚡ IA · Azure AI Foundry" : "⚙️ motor de reglas"}
              </span>
            )}
          </div>
        ))}
        {cargando && <div className="burbuja bot">Escribiendo…</div>}
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

      <form
        className="chat-input"
        onSubmit={(e) => {
          e.preventDefault();
          enviar(texto);
        }}
      >
        <input
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Escribe tu pregunta…"
        />
        <button type="submit" disabled={cargando}>
          ➤
        </button>
      </form>
    </div>
  );
}
