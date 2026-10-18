"""Evidence-grounded variable extraction for English biological literature."""

from .extraction import (
    CHUNK_SCHEMA_VERSION,
    EXTRACTION_SCHEMA_VERSION,
    build_sections,
    chunk_sections,
)

__all__ = [
    "CHUNK_SCHEMA_VERSION",
    "EXTRACTION_SCHEMA_VERSION",
    "build_sections",
    "chunk_sections",
]

__version__ = "0.1.0"
