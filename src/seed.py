"""Carga datos de demostración alineados con el esquema real Countryland.

Uso:  python -m src.seed
"""
from __future__ import annotations

from src.database import SessionLocal, init_db
from src import models
from src.models import ESTADO_ACTIVO


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        if db.query(models.Animal).count() > 0:
            print("La base de datos ya tiene datos. No se cargó nada.")
            return

        # --- Catálogos ---
        especies = [
            models.Especie(Especie="Bovino", Estado=ESTADO_ACTIVO),
            models.Especie(Especie="Porcino", Estado=ESTADO_ACTIVO),
            models.Especie(Especie="Avícola", Estado=ESTADO_ACTIVO),
            models.Especie(Especie="Equino", Estado=ESTADO_ACTIVO),
            models.Especie(Especie="Caprino", Estado=ESTADO_ACTIVO),
            models.Especie(Especie="Ovino", Estado=ESTADO_ACTIVO),
        ]
        razas = [
            models.Raza(Raza="Brahman", Estado=ESTADO_ACTIVO),
            models.Raza(Raza="Gyr", Estado=ESTADO_ACTIVO),
            models.Raza(Raza="Normando", Estado=ESTADO_ACTIVO),
            models.Raza(Raza="Holstein", Estado=ESTADO_ACTIVO),
            models.Raza(Raza="Landrace", Estado=ESTADO_ACTIVO),
            models.Raza(Raza="Yorkshire", Estado=ESTADO_ACTIVO),
            models.Raza(Raza="Ponedora", Estado=ESTADO_ACTIVO),
            models.Raza(Raza="Criolla", Estado=ESTADO_ACTIVO),
        ]
        procesos = [
            models.ProcesoPecuario(Proceso_Pecuario="Vacunación", Estado=ESTADO_ACTIVO, Valor=15000),
            models.ProcesoPecuario(Proceso_Pecuario="Alimentación", Estado=ESTADO_ACTIVO, Valor=20000),
            models.ProcesoPecuario(Proceso_Pecuario="Desparasitación", Estado=ESTADO_ACTIVO, Valor=8000),
            models.ProcesoPecuario(Proceso_Pecuario="Pesaje", Estado=ESTADO_ACTIVO, Valor=0),
            models.ProcesoPecuario(Proceso_Pecuario="Inseminación", Estado=ESTADO_ACTIVO, Valor=45000),
        ]
        tipos_vac = [
            models.TipoVacunacion(Tipo_Vacunacion="Aftosa", Estado=ESTADO_ACTIVO),
            models.TipoVacunacion(Tipo_Vacunacion="Brucelosis", Estado=ESTADO_ACTIVO),
            models.TipoVacunacion(Tipo_Vacunacion="Triple bacteriana", Estado=ESTADO_ACTIVO),
            models.TipoVacunacion(Tipo_Vacunacion="Rabia bovina", Estado=ESTADO_ACTIVO),
            models.TipoVacunacion(Tipo_Vacunacion="Carbón sintomático", Estado=ESTADO_ACTIVO),
        ]
        # Lotes reales tomados del dump Countryland
        lotes = [
            models.Lote(Lote="Lote 1", Area=20, Sica="arcilloso", Estado=ESTADO_ACTIVO),
            models.Lote(Lote="Lote 2", Area=12, Sica="arenoso", Estado=ESTADO_ACTIVO),
            models.Lote(Lote="Lote 3", Area=5, Sica="arcilloso", Estado=ESTADO_ACTIVO),
            models.Lote(Lote="Lote 4", Area=5, Sica="tierra negra", Estado=ESTADO_ACTIVO),
            models.Lote(Lote="Lote 5", Area=12, Sica="arenoso", Estado=ESTADO_ACTIVO),
        ]
        # --- Insumos: unidades, marcas, productos, inventario ---
        unidades = [
            models.Unidad(Unidad="Kilogramo", Estado=ESTADO_ACTIVO),
            models.Unidad(Unidad="Litro", Estado=ESTADO_ACTIVO),
            models.Unidad(Unidad="Dosis", Estado=ESTADO_ACTIVO),
            models.Unidad(Unidad="Bulto", Estado=ESTADO_ACTIVO),
        ]
        marcas = [
            models.Marca(Marca="Zoetis", Estado=ESTADO_ACTIVO, Calificacion=5),
            models.Marca(Marca="Bayer", Estado=ESTADO_ACTIVO, Calificacion=4),
            models.Marca(Marca="Solla", Estado=ESTADO_ACTIVO, Calificacion=4),
        ]
        db.add_all(especies + razas + procesos + tipos_vac + lotes + unidades + marcas)
        db.flush()

        uni = {u.Unidad: u.Id_Unidad for u in unidades}
        mar = {m.Marca: m.Id_Marca for m in marcas}
        productos = [
            models.Producto(Producto="Vacuna Aftosa", Codigo="INS-001", Unidad_Id=uni["Dosis"],
                            Marca_Id=mar["Zoetis"], Valor=12000, Estado=ESTADO_ACTIVO),
            models.Producto(Producto="Vacuna Brucelosis", Codigo="INS-002", Unidad_Id=uni["Dosis"],
                            Marca_Id=mar["Zoetis"], Valor=15000, Estado=ESTADO_ACTIVO),
            models.Producto(Producto="Concentrado engorde", Codigo="INS-003", Unidad_Id=uni["Bulto"],
                            Marca_Id=mar["Solla"], Valor=95000, Estado=ESTADO_ACTIVO),
            models.Producto(Producto="Desparasitante", Codigo="INS-004", Unidad_Id=uni["Litro"],
                            Marca_Id=mar["Bayer"], Valor=48000, Estado=ESTADO_ACTIVO),
            models.Producto(Producto="Sal mineralizada", Codigo="INS-005", Unidad_Id=uni["Kilogramo"],
                            Marca_Id=mar["Solla"], Valor=3500, Estado=ESTADO_ACTIVO),
        ]
        db.add_all(productos)
        db.flush()
        db.add_all([
            models.Inventario(Producto_Id=productos[0].Id_Producto, Cantidad=40, Estado=ESTADO_ACTIVO),
            models.Inventario(Producto_Id=productos[1].Id_Producto, Cantidad=25, Estado=ESTADO_ACTIVO),
            models.Inventario(Producto_Id=productos[2].Id_Producto, Cantidad=12, Estado=ESTADO_ACTIVO),
            models.Inventario(Producto_Id=productos[3].Id_Producto, Cantidad=6, Estado=ESTADO_ACTIVO),
            models.Inventario(Producto_Id=productos[4].Id_Producto, Cantidad=80, Estado=ESTADO_ACTIVO),
        ])

        esp = {e.Especie: e.Id_Especie for e in especies}
        rz = {r.Raza: r.Id_Raza for r in razas}

        from datetime import datetime

        def animal(nombre, codigo, especie, raza, avaluo, valor, costo,
                   sexo=None, peso=None, nacimiento=None, estado=ESTADO_ACTIVO):
            return models.Animal(
                Animal=nombre, Codigo=codigo, Especie_Id=esp[especie], Raza_Id=rz[raza],
                Avaluo=avaluo, Valor=valor, Costo=costo, Estado=estado,
                Sexo=sexo, Peso=peso,
                Fecha_Nacimiento=datetime.fromisoformat(nacimiento) if nacimiento else None,
            )

        # --- Animales (con sexo, peso y nacimiento: ACA 2, Figura 17) ---
        animales = [
            animal("Vaca 001", "BOV-001", "Bovino", "Brahman", 2500000, 2800000, 1900000, "H", 380, "2021-03-15"),
            animal("Vaca 002", "BOV-002", "Bovino", "Gyr", 2700000, 3000000, 2100000, "H", 420, "2020-08-02"),
            animal("Toro 003", "BOV-003", "Bovino", "Brahman", 3500000, 4000000, 2600000, "M", 510, "2019-11-20"),
            animal("Vaca 004", "BOV-004", "Bovino", "Holstein", 3200000, 3600000, 2400000, "H", 450, "2021-01-10"),
            animal("Novillo 005", "BOV-005", "Bovino", "Normando", 2200000, 2500000, 1700000, "M", 320, "2023-05-25"),
            animal("Cerdo 010", "POR-010", "Porcino", "Landrace", 600000, 700000, 450000, "M", 120, "2024-02-14"),
            animal("Cerda 011", "POR-011", "Porcino", "Yorkshire", 580000, 680000, 430000, "H", 110, "2024-03-01"),
            animal("Cerdo 012", "POR-012", "Porcino", "Landrace", 610000, 720000, 460000, "M", 125, "2024-01-20"),
            animal("Gallina 100", "AVE-100", "Avícola", "Ponedora", 25000, 30000, 18000, "H", 2, "2025-06-11"),
            animal("Gallina 101", "AVE-101", "Avícola", "Ponedora", 25000, 30000, 18000, "H", 2, "2025-06-11"),
            animal("Cabra 200", "CAP-200", "Caprino", "Criolla", 350000, 420000, 260000, "H", 45, "2023-09-05"),
            animal("Yegua 300", "EQU-300", "Equino", "Criolla", 4500000, 5000000, 3200000, "H", 400, "2018-04-30"),
        ]
        db.add_all(animales)
        db.flush()

        vac, alim, despar = procesos[0], procesos[1], procesos[2]
        aftosa, brucelosis = tipos_vac[0], tipos_vac[1]

        # --- Detalle_Animal (eventos) ---
        db.add_all([
            models.DetalleAnimal(Animal_Id=animales[0].Id_Animal,
                                 Proceso_Pecuario_Id=vac.Id_Proceso_Pecuario,
                                 Tipo_Vacunacion_Id=aftosa.id_Tipo_Vacunacion,
                                 Costo=12000, Estado=ESTADO_ACTIVO, Observaciones="Vacuna aftosa"),
            models.DetalleAnimal(Animal_Id=animales[2].Id_Animal,
                                 Proceso_Pecuario_Id=vac.Id_Proceso_Pecuario,
                                 Tipo_Vacunacion_Id=brucelosis.id_Tipo_Vacunacion,
                                 Costo=15000, Estado=ESTADO_ACTIVO, Observaciones="Vacuna brucelosis"),
            models.DetalleAnimal(Animal_Id=animales[3].Id_Animal,
                                 Proceso_Pecuario_Id=despar.Id_Proceso_Pecuario,
                                 Costo=8000, Estado=ESTADO_ACTIVO, Observaciones="Desparasitante"),
            models.DetalleAnimal(Animal_Id=animales[0].Id_Animal,
                                 Proceso_Pecuario_Id=alim.Id_Proceso_Pecuario,
                                 Costo=18000, Estado=ESTADO_ACTIVO, Observaciones="Silo de maíz"),
            models.DetalleAnimal(Animal_Id=animales[3].Id_Animal,
                                 Proceso_Pecuario_Id=alim.Id_Proceso_Pecuario,
                                 Costo=22000, Estado=ESTADO_ACTIVO, Observaciones="Concentrado"),
        ])
        db.commit()
        print(f"Datos de demostración cargados: {len(animales)} animales, "
              f"{len(especies)} especies, {len(razas)} razas.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
