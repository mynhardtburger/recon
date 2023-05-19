from pathlib import Path

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing_extensions import Annotated

from recon.reconcile import Reconcile


def main(
    left: Annotated[
        Path,
        typer.Argument(
            default=...,
            help="Path to the left dataset (csv|xlsx).",
            show_default=False,
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    right: Annotated[
        Path,
        typer.Argument(
            default=...,
            help="Path to the right dataset (csv|xlsx).",
            show_default=False,
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    left_on: Annotated[
        str,
        typer.Argument(
            default=...,
            help="Reconcile using this field from the left dataset.",
            show_default=False,
        ),
    ],
    right_on: Annotated[
        str,
        typer.Argument(
            default=...,
            help="Reconcile using this field from the right dataset.",
            show_default=False,
        ),
    ],
    left_suffix: Annotated[
        str,
        typer.Option(
            default=...,
            help="Suffix to append to the left dataset's column names.",
            show_default=True,
            rich_help_panel="Input options",
        ),
    ] = "_left",
    right_suffix: Annotated[
        str,
        typer.Option(
            default=...,
            help="Suffix to append to the right dataset's column names.",
            show_default=True,
            rich_help_panel="Input options",
        ),
    ] = "_right",
    left_sheet: Annotated[
        str,
        typer.Option(
            default=...,
            help="Sheet to read from left if left is a spreadsheet.",
            show_default=True,
            rich_help_panel="Input options",
        ),
    ] = "Sheet1",
    right_sheet: Annotated[
        str,
        typer.Option(
            default=...,
            help="Sheet to read from left if left is a spreadsheet.",
            show_default=True,
            rich_help_panel="Input options",
        ),
    ] = "Sheet1",
    output_file: Annotated[
        str,
        typer.Option(
            default=...,
            help="Path to save results to (xlsx).",
            show_default=False,
            rich_help_panel="Output options",
        ),
    ] = "",
    std_out: Annotated[
        bool,
        typer.Option(
            default=...,
            help="Print results to stdout.",
            rich_help_panel="Output options",
        ),
    ] = False,
    info_only: Annotated[
        bool,
        typer.Option(
            default=...,
            help="Print summary results only.",
            rich_help_panel="Output options",
        ),
    ] = False,
):
    if left_suffix == right_suffix:
        print("Suffixes cannot be the same to avoid field name conflicts.")
        raise typer.Abort()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Reading datasets...", total=None)
        try:
            recon = Reconcile.read_files(
                left_file=left,
                right_file=right,
                left_on=left_on,
                right_on=right_on,
                suffixes=(left_suffix, right_suffix),
                left_kwargs={"sheet_name": left_sheet},
                right_kwargs={"sheet_name": right_sheet},
            )
        except ValueError as e:
            print(e)
            raise typer.Abort()

        progress.add_task(description="Reconciling...", total=None)

        if info_only:
            recon.info()
            raise typer.Exit()

        if std_out:
            recon.to_stdout(["all"])
            raise typer.Exit()

        if output_file:
            recon.to_xlsx(output_file, ["all"])
            print(f"Recon results saved to '{output_file}'.")
            raise typer.Exit()


app = typer.run(main)
