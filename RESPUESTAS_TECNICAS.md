# Parte teórica

He preferido responder esta parte con un **enfoque práctico y directo**, más cercano a cómo se manejan estos conceptos en el día a día de un proyecto real que a una definición académica. La intención es explicar **cómo y por qué** los aplico, basándome en experiencia profesional.

---

## 1. Principios SOLID

Los principios SOLID son básicamente un conjunto de guías para escribir código más **mantenible, extensible y fácil de testear**.

* **Responsabilidad Única (SRP):** cada clase debería encargarse de una sola cosa y hacerlo bien. Esto reduce el impacto de los cambios y evita efectos colaterales inesperados.
* **Abierto/Cerrado (OCP):** las clases/métodos debería estar abierto a extensión pero cerrado a modificación. En la práctica, esto permite añadir nuevas funcionalidades sin tocar código existente.
* **Sustitución de Liskov (LSP):** cuando una clase hereda de otra, debería poder usarse en cualquier lugar donde se espere la clase padre sin romper el comportamiento del sistema.
* **Segregación de Interfaces (ISP):** es mejor tener varias interfaces pequeñas y específicas que una muy grande. Así las clases solo implementan lo que realmente necesitan.
* **Inversión de Dependencias (DIP):** los módulos de alto nivel no deberían depender de implementaciones concretas, sino de abstracciones. Esto hace el código más flexible y testeable.

---

## 2. Inyección de dependencias

La inyección de dependencias consiste en **pasar las dependencias desde fuera**, en lugar de crearlas directamente dentro de una clase.

Por ejemplo, en vez de que un servicio instancie directamente una base de datos, se le pasa esa dependencia por parámetro. Esto permite:

* Cambiar implementaciones fácilmente.
* Testear usando mocks o fakes sin tocar código de producción.
* Reducir el acoplamiento entre componentes.

---

## 3. Controladores delgados

Para evitar meter lógica de negocio en los controladores, estos deberían usarse únicamente como **punto de entrada**:

* Validan los datos de entrada.
* Llaman al caso de uso o servicio correspondiente.
* Devuelven la respuesta formateada.

---

## 4. `yield` en Python

`yield` permite devolver valores de forma incremental en lugar de devolver todo de golpe con `return`.

Una función con `yield` se convierte en un **generador**, que va produciendo valores uno a uno cada vez que se itera sobre él. Esto es útil cuando:

* Trabajas con grandes volúmenes de datos.
* Quieres reducir consumo de memoria.
* Necesitas procesamiento lazy.

Como desventaja, el flujo puede ser menos intuitivo que una función tradicional si no se conoce bien el concepto.

---

## 5. Microservicios vs. monolitos

Para proyectos pequeños o equipos reducidos, un **monolito** suele ser más sencillo de desarrollar, desplegar y mantener.

Los **microservicios** empiezan a tener sentido cuando:

* El sistema es grande.
* Hay varios equipos trabajando en paralelo.
* Necesitas escalar componentes específicos de forma independiente.

Como contrapartida, los microservicios añaden complejidad: comunicación entre servicios, observabilidad, debugging más complejo e infraestructura más exigente. Un sistema grande (por ejemplo, un e‑commerce a gran escala) suele beneficiarse más de este enfoque.

---

## 6. Asincronía (`async/await`)

La programación asíncrona es especialmente útil cuando hay muchas operaciones de **I/O**, como llamadas a APIs externas o acceso a base de datos.

Mientras una operación espera respuesta, el programa puede seguir ejecutando otras tareas sin bloquear el hilo.

Errores comunes:

* Olvidar usar `await`, lo que provoca que la tarea no se ejecute realmente.
* Mezclar código síncrono y asíncrono sin cuidado, generando bloqueos inesperados.

---

## 7. Explicar `async` a un perfil júnior

La asincronía permite lanzar tareas que tardan en responder sin detener todo el programa.

En lugar de esperar a que una petición termine, el sistema puede seguir haciendo otras cosas y retomar la ejecución cuando el resultado esté listo. Esto hace que la aplicación sea más eficiente y responsiva, especialmente cuando depende de servicios externos.

---

## 8. Sistema extensible de tools/plugins para un agente

Un sistema de plugins se puede diseñar definiendo:

* Una **interfaz o clase base** que todas las herramientas deben implementar.
* Un **registro de herramientas** donde se almacenan las disponibles.
* Un núcleo del agente que solo interactúa con ese registro, sin conocer implementaciones concretas.

De esta forma, añadir una nueva herramienta implica únicamente crear una nueva clase que implemente la interfaz y registrarla, sin modificar el código del agente.

---

## 9. Tipos de pruebas

* **Tests unitarios:** prueban funciones o clases de forma aislada, usando mocks para las dependencias. Son rápidos y se ejecutan con frecuencia.
* **Tests de integración:** prueban cómo interactúan varios componentes reales entre sí (por ejemplo, un endpoint con la base de datos). Son más lentos y suelen ejecutarse antes de hacer merge.
* **Tests end‑to‑end (E2E):** prueban todo el sistema como lo usaría un usuario real. Son los más lentos y frágiles, y normalmente se ejecutan antes de desplegar a producción.
