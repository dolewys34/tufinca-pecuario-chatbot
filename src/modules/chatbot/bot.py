class Chatbot:
    """Motor de respaldo basado en reglas.

    Se usa cuando Azure AI Foundry no está configurado o no está disponible.
    Mantiene compatibilidad con la versión inicial del proyecto.
    """

    def __init__(self) -> None:
        self.saludo = "Hola, soy TuFinca Bot. Puedo ayudarte con información básica del sistema."

    def responder(self, mensaje: str) -> str:
        mensaje = mensaje.lower().strip()

        if mensaje in {"hola", "buenos dias", "buenas tardes", "buenas noches"}:
            return self.saludo
        claves_stats = ("estadistic", "estadístic", "grafic", "gráfic", "reporte", "resumen")
        if any(c in mensaje for c in claves_stats):
            return "Aquí tienes el resumen de tu finca 👇"
        if "raza" in mensaje:
            return "Esta es la distribución de animales por raza 👇"
        if "inventario" in mensaje or "animal" in mensaje or "especie" in mensaje:
            return "Aquí está la distribución de tu inventario animal 👇"
        if "vacun" in mensaje or "salud" in mensaje:
            return "Registra vacunas y eventos de salud en la ficha de cada animal para recibir recordatorios."
        if "costo" in mensaje or "gast" in mensaje:
            return "Los costos de sanidad y alimentación se resumen en el panel principal."
        if "ayuda" in mensaje:
            return "Puedo ayudarte con: inventario, vacunación, alimentación y costos. ¿Qué necesitas?"
        return (
            "No entendí tu solicitud. Prueba con: inventario, vacunación, costos o ayuda. "
            "(Para respuestas más inteligentes, configura Azure AI Foundry.)"
        )
