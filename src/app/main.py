from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.modules.pecuario.animales import AnimalRegistry
from src.modules.chatbot.bot import Chatbot


def main() -> None:
    print("=== TuFinca Pecuario + Chatbot ===")
    registry = AnimalRegistry()
    registry.agregar_animal("Bovino", "Vaca 001", 350)
    registry.agregar_animal("Porcino", "Cerdo 010", 120)

    chatbot = Chatbot()
    print("\nEstado inicial del inventario:")
    registry.listar_animales()

    print("\nRespuesta del chatbot:")
    print(chatbot.responder("hola"))
    print(chatbot.responder("inventario"))


if __name__ == "__main__":
    main()
