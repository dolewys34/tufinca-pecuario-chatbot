"""Pruebas de la API alineada con el esquema real Countryland."""
from fastapi.testclient import TestClient

from src.app.api import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_catalogos_disponibles() -> None:
    especies = client.get("/api/especies").json()
    razas = client.get("/api/razas").json()
    assert len(especies) >= 1 and "nombre" in especies[0]
    assert len(razas) >= 1


def test_crear_y_listar_animal() -> None:
    especie = client.get("/api/especies").json()[0]
    raza = client.get("/api/razas").json()[0]
    r = client.post(
        "/api/animales",
        json={
            "Animal": "Test 001",
            "Codigo": "TEST-001",
            "Especie_Id": especie["id"],
            "Raza_Id": raza["id"],
            "Valor": 100000,
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["especie_nombre"] == especie["nombre"]
    animal_id = body["Id_Animal"]

    r2 = client.get("/api/animales")
    assert any(a["Id_Animal"] == animal_id for a in r2.json())

    client.delete(f"/api/animales/{animal_id}")


def test_chat_estadisticas_boton() -> None:
    # El botón "__stats" siempre devuelve gráficos (ruta determinista).
    r = client.post("/api/chat", json={"mensaje": "__stats"})
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["graficos"], list)
    assert len(body["graficos"]) >= 1
    assert "datos" in body["graficos"][0]


def test_chat_menu_tiene_opciones() -> None:
    # Un saludo devuelve el menú con botones de opciones.
    r = client.post("/api/chat", json={"mensaje": "hola"})
    body = r.json()
    assert len(body["opciones"]) >= 1
