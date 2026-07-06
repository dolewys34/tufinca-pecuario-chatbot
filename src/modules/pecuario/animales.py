class AnimalRegistry:
    def __init__(self) -> None:
        self.animales = []

    def agregar_animal(self, especie: str, nombre: str, peso: float) -> None:
        animal = {
            "especie": especie,
            "nombre": nombre,
            "peso": peso,
        }
        self.animales.append(animal)

    def listar_animales(self) -> None:
        if not self.animales:
            print("No hay animales registrados.")
            return

        for animal in self.animales:
            print(f"- {animal['nombre']} | Especie: {animal['especie']} | Peso: {animal['peso']} kg")
