from src.modules.pecuario.animales import AnimalRegistry
from src.modules.chatbot.bot import Chatbot


def test_registro_basico() -> None:
    registry = AnimalRegistry()
    registry.agregar_animal("Bovino", "Vaca 001", 350)
    assert len(registry.animales) == 1


def test_chatbot_respuesta() -> None:
    chatbot = Chatbot()
    respuesta = chatbot.responder("hola")
    assert "TuFinca Bot" in respuesta
