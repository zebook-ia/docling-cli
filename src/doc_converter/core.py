import pypandoc
from pathlib import Path

def convert_document(input_file: Path, output_format: str, output_path: Path) -> Path:
    """
    Converte um único documento para o formato de saída especificado usando Pandoc.

    Args:
        input_file (Path): O caminho para o arquivo de entrada.
        output_format (str): O formato de saída desejado.
        output_path (Path): O caminho (diretório ou arquivo) para salvar o resultado.

    Returns:
        Path: O caminho completo para o arquivo de saída gerado.

    Raises:
        FileNotFoundError: Se o arquivo de entrada não for encontrado.
        pypandoc.PandocError: Se a conversão do Pandoc falhar.
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_file}")

    if output_path.is_dir():
        # Se o caminho de saída for um diretório, cria o nome do arquivo de saída
        # com base no nome de entrada e no formato de saída.
        output_filename = input_file.stem + "." + output_format
        output_file = output_path / output_filename
    else:
        # Se o caminho de saída for um arquivo, usa-o diretamente.
        # Garante que o diretório pai exista.
        output_file = output_path
        output_file.parent.mkdir(parents=True, exist_ok=True)


    pypandoc.convert_file(
        str(input_file),
        to=output_format,
        outputfile=str(output_file),
        encoding='utf-8',
    )
    
    return output_file


def batch_convert_documents(
    input_dir: Path,
    output_format: str,
    output_dir: Path,
    recursive: bool,
):
    """
    Converte múltiplos documentos de um diretório de entrada para um diretório de saída.

    Args:
        input_dir (Path): O diretório de entrada contendo os arquivos.
        output_format (str): O formato de saída para a conversão.
        output_dir (Path): O diretório onde os arquivos convertidos serão salvos.
        recursive (bool): Se `True`, busca por arquivos em subdiretórios também.
    
    Yields:
        Tuple[Path, Path]: Uma tupla contendo o caminho do arquivo de entrada e o caminho do arquivo de saída.
    """
    glob_pattern = "**/*" if recursive else "*"
    files_to_convert = [f for f in input_dir.glob(glob_pattern) if f.is_file()]

    if not files_to_convert:
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    
    for input_file in files_to_convert:
        try:
            # A lógica de conversão real acontece aqui, chamando a função para um único arquivo.
            output_file = convert_document(input_file, output_format, output_dir)
            yield input_file, output_file
        except Exception:
            # Se a conversão de um arquivo falhar, ele é pulado, e o erro é retornado
            # para ser tratado pelo chamador (a CLI).
            yield input_file, None 