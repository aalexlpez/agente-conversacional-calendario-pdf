"""Integración de PDFTool con un PDF mínimo construido manualmente."""

from __future__ import annotations

from pathlib import Path

from src.infrastructure.memory_store import InMemoryStore
from src.tools.pdf_tool import PDFTool


def build_simple_pdf_bytes(text: str) -> bytes:
	"""Genera bytes de un PDF muy simple con un texto embebido."""
	header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
	stream = f"BT /F1 24 Tf 72 120 Td ({text}) Tj ET".encode("latin1")
	objects: list[bytes] = []

	def add_obj(num: int, content: bytes) -> None:
		obj = b"%d 0 obj\n" % num + content + b"\nendobj\n"
		objects.append(obj)

	add_obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")
	add_obj(2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
	add_obj(
		3,
		b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
	)
	add_obj(4, b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
	add_obj(5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

	body = b""
	offsets = [0]
	current_offset = len(header)
	for obj in objects:
		offsets.append(current_offset)
		body += obj
		current_offset += len(obj)

	xref_start = len(header) + len(body)
	xref = b"xref\n0 %d\n" % len(offsets)
	xref += b"0000000000 65535 f \n"
	for off in offsets[1:]:
		xref += b"%010d 00000 n \n" % off

	trailer = (
		b"trailer\n"
		+ b"<< /Size %d /Root 1 0 R >>\n" % len(offsets)
		+ b"startxref\n"
		+ b"%d\n" % xref_start
		+ b"%%EOF\n"
	)

	return header + body + xref + trailer


def test_pdf_extraction_integration(tmp_path: Path) -> None:
	"""Verifica que PDFTool puede extraer texto del PDF generado."""
	pdf_bytes = build_simple_pdf_bytes("Hola PDF")
	pdf_path = tmp_path / "simple.pdf"
	pdf_path.write_bytes(pdf_bytes)

	tool = PDFTool(InMemoryStore())
	extracted = tool.extract_text(str(pdf_path))

	assert "Hola" in extracted
