import pypandoc
from typing import List

_cached_formats: List[str] = []

def get_supported_formats() -> List[str]:
    """
    Retorna uma lista dos formatos de saída suportados pelo Pandoc.

    Armazena o resultado em cache para evitar chamadas repetidas.

    Returns:
        List[str]: Uma lista de strings, cada uma sendo um formato suportado.
    """
    global _cached_formats
    if not _cached_formats:
        # pypandoc.get_pandoc_formats() retorna ('output', formats)
        # e ('input', formats) mas queremos apenas os de saída.
        all_formats = pypandoc.get_pandoc_formats()
        output_formats = next((fmt[1] for fmt in all_formats if fmt[0] == 'output'), [])
        _cached_formats = sorted(output_formats)
    return _cached_formats 