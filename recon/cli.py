from pathlib import Path

import typer
from typing_extensions import Annotated

from recon.main import Reconcile


def main(
    left: Annotated[
        Path,
        typer.Argument(
            help="Path to the left dataset",
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
            help="Path to the right dataset",
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
            help="Reconcile using this field from the left dataset",
            show_default=False,
        ),
    ],
    right_on: Annotated[
        str,
        typer.Argument(
            help="Reconcile using this field from the right dataset",
            show_default=False,
        ),
    ],
    output_file: Annotated[
        str, typer.Option(help="Path to save results to", show_default=False)
    ] = "",
    left_sheet: Annotated[
        str,
        typer.Option(
            help="Sheet to read from left if left is a spreadsheet",
            show_default=True,
        ),
    ] = "Sheet1",
    right_sheet: Annotated[
        str,
        typer.Option(
            help="Sheet to read from left if left is a spreadsheet",
            show_default=True,
        ),
    ] = "Sheet1",
    std_out: Annotated[bool, typer.Option(help="Print results to stdout")] = False,
    info_only: Annotated[bool, typer.Option(help="Print summary results only")] = False,
    suffixes: Annotated[
        tuple[str, str],
        typer.Argument(help="Print summary results only"),
    ] = ("_left", "_right"),
):
    try:
        recon = Reconcile.read_files(
            left_file=left,
            right_file=right,
            left_on=left_on,
            right_on=right_on,
            suffixes=suffixes,
            left_kwargs={"sheet_name": left_sheet},
            right_kwargs={"sheet_name": right_sheet},
        )
    except ValueError as e:
        print(e)
        raise typer.Abort()

    if info_only:
        recon.info()
        raise typer.Exit()

    if std_out:
        recon.to_stdout(["all_data"])
        raise typer.Exit()

    if output_file:
        recon.to_xlsx(output_file, ["all_data"])
        raise typer.Exit()


if __name__ == "__main__":
    typer.run(main)
