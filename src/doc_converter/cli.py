import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from pathlib import Path
import pypandoc
from typing import List

from .formats import get_supported_formats
from .core import convert_document, batch_convert_documents

app = typer.Typer(
    name="doc-converter",
    help="Uma ferramenta CLI para converter formatos de documentos.",
    add_completion=False,
)
console = Console()


@app.command(name="list-formats")
def list_formats():
    """
    Lista todos os formatos de saída suportados, exibidos em colunas.
    """
    try:
        formats = get_supported_formats()
        if not formats:
            console.print("[yellow]Nenhum formato de saída encontrado.[/yellow]")
            return

        table = Table(title="Formatos de Saída Suportados pelo Pandoc", show_header=True, header_style="bold magenta")
        
        # Define o número de colunas para a tabela
        num_columns = 4
        for i in range(num_columns):
            table.add_column(f"Formato {i+1}")

        # Preenche a tabela com os formatos
        rows = [formats[i:i + num_columns] for i in range(0, len(formats), num_columns)]
        for row in rows:
            # Garante que cada linha tenha o número correto de células
            padded_row = row + [""] * (num_columns - len(row))
            table.add_row(*padded_row)
        
        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Erro ao buscar formatos:[/] {e}")


@app.command()
def convert(
    file: Path = typer.Argument(
        ..., help="O caminho para o arquivo a ser convertido.", exists=True, file_okay=True, dir_okay=False, readable=True
    ),
    format: str = typer.Option(
        ..., "--format", "-f", help="O formato de saída para a conversão."
    ),
    output: Path = typer.Option(
        None, "--output", "-o", help="O diretório ou nome do arquivo de saída. Se for um diretório, o nome do arquivo será inferido."
    ),
):
    """
    Converte um arquivo de um formato para outro.
    """
    if output is None:
        output = Path.cwd()

    output_format = format.lower()
    
    try:
        supported_formats = get_supported_formats()
        if output_format not in supported_formats:
            console.print(f"[bold red]Erro:[/] Formato de saída '{output_format}' não é suportado.")
            raise typer.Exit(code=1)

        with console.status(f"[yellow]Convertendo [cyan]'{file.name}'[/] para [cyan]'{output_format}'[/]...", spinner="dots") as status:
            final_output_path = convert_document(file, output_format, output)
            status.stop()
        
        success_message = Panel(
            f"Arquivo [bold green]'{file.name}'[/] convertido com sucesso para [bold green]'{final_output_path.name}'[/]!\n"
            f"Salvo em: [cyan]{final_output_path.parent.resolve()}[/]",
            title="[bold green]Conversão Concluída[/]",
            border_style="green",
            expand=False
        )
        console.print(success_message)

    except FileNotFoundError as e:
        console.print(f"[bold red]Erro:[/] {e}")
        raise typer.Exit(code=1)
    except pypandoc.PandocError as e:
        console.print(f"[bold red]Erro durante a conversão do Pandoc:[/] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Ocorreu um erro inesperado:[/] {e}")
        raise typer.Exit(code=1)


@app.command()
def batch(
    input_dir: Path = typer.Argument(
        ..., help="O diretório de entrada a ser processado.", exists=True, file_okay=False, dir_okay=True, readable=True
    ),
    format: str = typer.Option(
        ..., "--format", "-f", help="O formato de saída para a conversão."
    ),
    output: Path = typer.Option(
        None, "--output", "-o", help="O diretório de saída para os arquivos convertidos. Padrão: 'output' no diretório atual."
    ),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Processa subdiretórios recursivamente."
    ),
):
    """
    Converte múltiplos arquivos em um diretório.
    """
    if output is None:
        output = Path.cwd() / "output"
    
    output.mkdir(parents=True, exist_ok=True)
    output_format = format.lower()

    try:
        supported_formats = get_supported_formats()
        if output_format not in supported_formats:
            console.print(f"[bold red]Erro:[/] Formato de saída '{output_format}' não é suportado.")
            raise typer.Exit(code=1)

        # Usando um gerador para encontrar os arquivos primeiro para poder contar o total
        glob_pattern = "**/*" if recursive else "*"
        files_to_process = [f for f in input_dir.glob(glob_pattern) if f.is_file()]
        total_files = len(files_to_process)

        if total_files == 0:
            console.print("[yellow]Nenhum arquivo encontrado no diretório de entrada.[/yellow]")
            raise typer.Exit()
            
        successes: List[str] = []
        failures: List[str] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"[cyan]Convertendo {total_files} arquivos...", total=total_files)

            for input_file in files_to_process:
                try:
                    convert_document(input_file, output_format, output)
                    successes.append(input_file.name)
                except Exception as e:
                    failures.append(f"{input_file.name} ([red]Falha: {e}[/red])")
                progress.update(task, advance=1)

        console.print("\n[bold green]Processo em lote concluído![/]")
        if successes:
            console.print(Panel(f"[bold]Sucessos ({len(successes)}):[/bold]\n" + "\n".join(successes), title="Relatório", border_style="green"))
        if failures:
            console.print(Panel(f"[bold]Falhas ({len(failures)}):[/bold]\n" + "\n".join(failures), title="Relatório", border_style="red"))


    except Exception as e:
        console.print(f"[bold red]Ocorreu um erro inesperado durante o processo em lote:[/] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app() 