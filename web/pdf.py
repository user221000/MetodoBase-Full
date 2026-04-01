"""
web/pdf.py — Re-export del generador de PDFs para la app web.

Web importa desde aquí, no desde api/pdf_generator.py.
"""
from api.pdf_generator import PDFGenerator  # noqa: F401

__all__ = ["PDFGenerator"]
