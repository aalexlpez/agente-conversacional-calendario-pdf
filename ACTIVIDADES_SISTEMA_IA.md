# Objetivo general
El objetivo de esta prueba es evaluar tus conocimientos teóricos en ingeniería de software y
tu capacidad para diseñar e implementar un agente conversacional en Python orientado a la
optimización de procesos. La prueba se divide en dos partes: teórica y práctica. La parte
teórica servirá para conocer tu criterio y comprensión de ciertos conceptos clave, mientras
que la parte práctica demostrará tu capacidad para aplicarlos en un proyecto coherente y
extensible. 

NOTA: La parte teórica no está acá contemplada

# Práctica: diseño e implementación de un agente conversacional

# Descripción general
Diseña e implementa un agente conversacional en Python que ayude a un usuario a gestionar
eventos en un calendario. El agente debe ser capaz de mantener conversaciones
contextuales, interactuar con herramientas externas y responder preguntas sobre un
documento PDF. Se valorará una arquitectura limpia y extensible, así como el uso adecuado
de asincronía cuando proceda.

# Requisitos funcionales

1. Autenticación. El agente deberá permitir que el usuario se autentique contra la
aplicación con credenciales válidas. No es necesario implementar un proveedor de
identidad completo; puede simularse la autenticación (p. ej., validando contra un
almacén local).

2. Gestión de conversaciones múltiples. El sistema debe soportar varias
conversaciones simultáneas. Cada conversación debe mantener su propio contexto y
memoria, de manera que el agente recuerde el historial para dar respuestas
coherentes.

3. Memoria y contexto. Implementa un mecanismo de almacenamiento (en memoria o
SQLite) que permita al agente recuperar y actualizar el contexto de cada
conversación, incluyendo datos sobre el usuario y eventos del calendario. Explica en
tu código cómo se gestiona la persistencia.

4. Herramientas externas. El agente debe utilizar al menos una herramienta externa
(API de calendario, servicio de preguntas sobre PDFs u otra que consideres
apropiada). Encapsula la integración en una clase o módulo para que pueda sustituirse
con facilidad. Describe en tu diseño cómo incorporar nuevas herramientas sin
modificar el núcleo del agente (por ejemplo, mediante un registro de plugins).

5. Cambio de conversación durante respuestas. El usuario debe poder cambiar de
conversación mientras espera la respuesta de una conversación anterior. El agente
debe indicar cuándo finaliza la respuesta pendiente (puedes usar notificaciones o
streaming de respuestas). Considera el uso de asincronía (async/await) para
gestionar múltiples tareas concurrentes.

6. Extensibilidad y diseño. Estructura tu código siguiendo principios SOLID y buenas
prácticas de diseño. Se valorará la separación de responsabilidades (controladores
delgados), el uso de interfaces abstractas para las herramientas y la inversión de
dependencias para facilitar el testeo y la extensibilidad.

7. Persistencia simple. Para almacenar el estado de los eventos, conversaciones y
usuarios, puedes utilizar un almacenamiento en memoria (diccionarios) o una base de
datos ligera como SQLite. Documenta cómo inicializas y accedes a estos datos.

8. Responder sobre un PDF. Proporciona una función o endpoint que permita al usuario
subir un documento PDF y luego formular preguntas sobre su contenido. Implementa
una abstracción sobre la herramienta que analice el PDF y permita realizar búsquedas
o extracción de datos. Explica en la documentación cómo se integra esta
funcionalidad con la memoria del agente.

# Consideraciones y buenas prácticas
● Asincronía. Utiliza async/await para operaciones I/O o llamadas externas.
Asegúrate de await todas las tareas para evitar cancelaciones inesperadas.
Documenta en qué partes del código implementas asincronía y por qué.
● Lógica de negocio desacoplada. Mantén los controladores o manejadores de
peticiones libres de lógica compleja. Delegan las operaciones a servicios o casos de
uso, respetando así la separación de responsabilidades.
● Pruebas. Incluye pruebas unitarias para funciones y clases individuales y, si es posible,
alguna prueba de integración que valide la interacción con la herramienta externa.
Describe cómo planificarías pruebas end‑to‑end en un contexto de CI/CD.
● Robustez y manejo de errores. Define cómo gestionas las excepciones (por ejemplo,
operaciones fallidas al acceder al calendario o al PDF). Asegúrate de que el agente
notifique claramente los errores y no se bloquee ante entradas inesperadas.
● Extensibilidad. Organiza el proyecto de modo que incorporar una nueva herramienta
o funcionalidad requiera un esfuerzo mínimo. Considera un patrón de plugins o
registro de herramientas

# Entregables
● Código fuente organizado y documentado. Incluye instrucciones claras para ejecutar
la aplicación y sus dependencias. Utiliza un archivo README.md para explicar cómo se
instala y se arranca el agente.
● Scripts o funciones que permitan inicializar el almacenamiento (en memoria o SQLite)
y realizar pruebas básicas. Se valorarán tests de al menos una parte crítica (por
ejemplo, de los servicios de calendario o de la lógica de conversación).
● Diagramas o esquemas opcionales que ayuden a entender tu arquitectura (p. ej.,
diagramas de clases o de componentes). No es obligatorio, pero facilita la revisión.
● (Opcional) Despliegue: si deseas demostrar capacidades de despliegue, puedes
entregar un Dockerfile o un entorno de ejecución que facilite la puesta en marcha
del agente.

Lista exacta de lo que se debe hacer a grandes rasgos:

1 Diseñar e implementar en Python un agente conversacional para gestionar eventos de calendario, capaz de mantener conversaciones contextuales, interactuar con herramientas externas y responder preguntas sobre un PDF.
2 Implementar autenticación de usuarios con credenciales válidas (simulada con almacén local).
3 Habilitar gestión de múltiples conversaciones simultáneas, cada una con su propio contexto y memoria.
4 Implementar almacenamiento de contexto por conversación (memoria o SQLite) para usuarios y eventos; explicar en el código cómo se gestiona la persistencia.
5 Integrar al menos una herramienta externa (API de calendario, servicio de PDFs u otra); encapsularla en una clase o módulo sustituible; describir cómo añadir nuevas herramientas sin modificar el núcleo (registro de plugins).
6 Implementar cambio de conversación mientras se esperan respuestas, indicando cuándo finaliza la respuesta pendiente; usar async/await para concurrencia.
7 Estructurar el código con principios SOLID, controladores delgados, interfaces abstractas e inversión de dependencias.
8 Implementar persistencia simple para eventos, conversaciones y usuarios (memoria o SQLite) y documentar inicialización y acceso.
9 Proporcionar una función o endpoint para subir PDFs y hacer preguntas sobre su contenido; abstraer la herramienta de análisis y explicar su integración con la memoria del agente.
10 Documentar y aplicar asincronía en operaciones I/O o externas; asegurar await de todas las tareas.
11 Mantener lógica de negocio desacoplada de controladores, delegando en servicios o casos de uso.
12 Incluir pruebas unitarias y, si es posible, una prueba de integración con la herramienta externa; describir la planificación de pruebas end‑to‑end en CI/CD.
13 Definir y manejar excepciones (calendario/PDF), notificando errores sin bloquear el agente.
14 Organizar el proyecto para facilitar extensibilidad mediante patrón de plugins o registro de herramientas.
15 Entregar código fuente organizado y documentado con README.md (instalación y arranque).
16 Entregar scripts o funciones para inicializar el almacenamiento y realizar pruebas básicas.
17 Entregar diagramas o esquemas opcionales de arquitectura (si se desea).
18 Entregar Dockerfile o entorno de ejecución opcional para despliegue (si se desea).