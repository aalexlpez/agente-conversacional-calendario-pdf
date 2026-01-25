import asyncio

from src.application.tool_registry import ToolRegistry
from src.infrastructure.memory_store import InMemoryStore
from src.tools.pdf_tool import PDFTool

# Pruebas unitarias de la lógica interna del agente conversacional.
# Estas pruebas verifican el funcionamiento de las herramientas, el registro de plugins y la manipulación de eventos y documentos en memoria.


def test_tool_registry_registers_tool() -> None:
    """
    Prueba que el registro de herramientas (ToolRegistry) almacena correctamente una herramienta
    y permite recuperarla por nombre. Verifica también que la lista de herramientas registradas es correcta.
    """
    registry = ToolRegistry()
    pdf_tool = PDFTool(InMemoryStore())

    registry.register(pdf_tool)

    assert registry.get("pdf") is pdf_tool
    assert list(registry.list()) == [pdf_tool]


def test_pdf_tool_search() -> None:
    """
    Prueba la herramienta de PDF:
    - Agrega un documento PDF ficticio al almacenamiento.
    - Ejecuta una búsqueda de palabra clave en el contenido del PDF.
    - Verifica que la respuesta contiene coincidencias.
    """
    store = InMemoryStore()
    pdf_tool = PDFTool(store)
    doc = pdf_tool.add_document(
        user_id="user-1",
        conversation_id="conv-1",
        filename="doc.pdf",
        content="Hola mundo. Hola agente.",
    )

    result = asyncio.run(pdf_tool.execute(f"search:{doc.id}:hola"))
    assert "Coincidencias" in result
