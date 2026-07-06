# Proyecto TuFinca Pecuario + Chatbot

## 1. Información general

### Nombre del proyecto
Sistema de información agropecuario integral basado en TuFinca, con módulo pecuario y chatbot conversacional para la finca El Paraíso, Anzoátegui, Tolima.

### Objetivo general
Desarrollar un sistema de información agropecuario integral, a partir del mínimo producto viable (TuFinca) existente, incorporando un módulo pecuario y herramientas conversacionales basadas en chatbots, con el propósito de optimizar la eficiencia operativa y mejorar la trazabilidad de los procesos productivos en la finca El Paraíso.

### Objetivos específicos
- Diseñar el módulo pecuario del sistema de información para gestionar de manera estructurada el inventario animal, los procesos de reproducción, sanidad, alimentación y costos mediante herramientas de automatización digital.
- Diseñar la arquitectura funcional del chatbot, especificando los flujos de interacción, los tipos de usuario y la lógica de comunicación, con el fin de garantizar su integración eficiente al sistema de información agropecuario.
- Integrar los chatbots en plataformas de mensajería digital, como WhatsApp, para facilitar la captura y consulta de información en tiempo real, mejorando el acceso y la interacción de los productores rurales con el sistema.
- Evaluar la eficiencia operativa y la trazabilidad de la información antes y después de la implementación del sistema, mediante indicadores de desempeño y análisis comparativos aplicados en la finca piloto El Paraíso.

---

## 2. Visión del producto

El sistema debe permitir:
- registrar y consultar información del inventario animal,
- gestionar procesos de reproducción, sanidad, alimentación y costos,
- recibir y responder información por medio de un chatbot,
- mejorar la trazabilidad de las operaciones en la finca,
- y servir como base para una futura implementación en producción.

---

## 3. Alcance inicial del MVP

### Módulo pecuario
- Registro de animales
- Gestión básica de inventario
- Registro de salud y vacunación
- Registro de alimentación
- Registro de costos básicos
- Consultas simples por animal o lote

### Chatbot
- Bienvenida y presentación del sistema
- Captura básica de datos
- Consulta de información disponible
- Respuestas automáticas según el tipo de solicitud

### Plataforma de despliegue local
- Desarrollo local en entorno controlado
- Preparación para futura migración a producción
- Estructura modular y escalable

---

## 4. Filosofía de desarrollo

### Mantra del proyecto
“Diseñamos un sistema agropecuario integral que mejora la eficiencia, la trazabilidad y la toma de decisiones en la finca El Paraíso.”

### Principios
- Enfoque práctico y útil para el usuario final
- Desarrollo incremental
- Diseño pensado para crecer hacia producción
- Documentación clara y seguimiento continuo
- Priorización del MVP antes de funciones complejas

---

## 5. Plan de trabajo general

### Fase 1. Comprensión y documentación
- Revisar el documento base del proyecto
- Definir alcance inicial
- Identificar requerimientos funcionales principales
- Establecer el mantra del equipo

### Fase 2. Diseño del módulo pecuario
- Definir entidades y procesos clave
- Diseñar formularios y flujos de registro
- Identificar reportes básicos

### Fase 3. Diseño del chatbot
- Definir tipos de usuario
- Diseñar flujos conversacionales
- Establecer reglas de interacción

### Fase 4. Desarrollo local
- Crear estructura base del proyecto
- Implementar módulo pecuario inicial
- Implementar chatbot base
- Preparar integración con canal de mensajería o simulador local

### Fase 5. Pruebas y validación
- Probar módulos localmente
- Corregir errores de funcionamiento
- Ajustar flujo de usuario

### Fase 6. Preparación para producción futura
- Organizar código y documentación
- Definir configuración para despliegue posterior
- Preparar base de datos y arquitectura escalable

---

## 6. Estructura propuesta del proyecto local

```text
proyecto/
├── docs/
│   └── proyecto_tufinca_pecuario_chatbot.md
├── src/
│   ├── modules/
│   │   ├── pecuario/
│   │   └── chatbot/
│   └── app/
├── tests/
├── requirements.txt
└── README.md
```

---

## 7. Roadmap inicial de desarrollo

### Sprint 1
- Definir alcance del MVP
- Crear documentación base
- Diseñar estructura del proyecto local

### Sprint 2
- Implementar modelo de datos del módulo pecuario
- Crear formularios básicos de registro

### Sprint 3
- Implementar lógica básica del chatbot
- Conectar el chatbot con un flujo de prueba local

### Sprint 4
- Integrar módulos principales
- Realizar pruebas y ajustes
- Preparar versión inicial para demostración

---

## 8. Requisitos funcionales iniciales

### Módulo pecuario
- Registrar animales
- Consultar animales registrados
- Registrar eventos de salud
- Registrar alimentación y costos básicos

### Chatbot
- Responder saludos
- Solicitar datos básicos del usuario
- Consultar información registrada
- Enviar mensajes de confirmación

---

## 9. Requisitos no funcionales

- Fácil de mantener
- Escalable para futuras versiones
- Documentado de forma clara
- Preparado para integrarse con plataformas como WhatsApp en el futuro
- Seguro y ordenado en su estructura

---

## 10. Notas para el desarrollo local

Este proyecto debe construirse pensando en dos etapas:
1. Desarrollo local robusto y funcional.
2. Preparación futura para despliegue en producción.

Por ello, se recomienda:
- separar claramente la lógica de negocio,
- documentar cada módulo,
- usar una estructura organizada,
- y mantener el código listo para evolucionar.

---

## 11. Próximo paso

Crear la estructura inicial del proyecto local, incluyendo:
- carpeta de documentación,
- carpeta de código fuente,
- archivo base de configuración,
- y una versión inicial del módulo pecuario y chatbot.
