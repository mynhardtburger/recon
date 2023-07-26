# recon-cli: Simple command line tool to reconcile datasets

## What is it

**recon-cli** is a Python package and cli tool to reconcile datasets against each other using a common field. It aims to be provide a simple interface for reliable reconciliations, removing common logic errors made when performing reconciliations.

## Where to get it

The source code is currently hosted on GitHub at: https://github.com/mynhardtburger/recon-cli

Binary installers for the latest released version are available at the [Python
Package Index (PyPI)](https://pypi.org/project/recon-cli)

For commandline use install recon-cli via [pipx](https://pypa.github.io/pipx/):

```sh
# For command line usage
pipx install recon-cli
recon --help
```

To use it within your own project install via pip:
```sh
# PyPI install
pip install recon-cli
```

## Usage

### CLI

```plaintext
 Usage: recon [OPTIONS] LEFT RIGHT LEFT_ON RIGHT_ON

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────╮
│ *    left          FILE  Path to the left dataset. [required]                                    │
│ *    right         FILE  Path to the right dataset. [required]                                   │
│ *    left_on       TEXT  Reconcile using this field from the left dataset. [required]            │
│ *    right_on      TEXT  Reconcile using this field from the right dataset. [required]           │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Input options ──────────────────────────────────────────────────────────────────────────────────╮
│ --left-suffix     TEXT  Suffix to append to the left dataset's column names. [default: _left]    │
│ --right-suffix    TEXT  Suffix to append to the right dataset's column names. [default: _right]  │
│ --left-sheet      TEXT  Sheet to read from left if left is a spreadsheet. [default: Sheet1]      │
│ --right-sheet     TEXT  Sheet to read from left if left is a spreadsheet. [default: Sheet1]      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Output options ─────────────────────────────────────────────────────────────────────────────────╮
│ --output-file                  TEXT  Path to save results (in xlsx format) to.                   │
│ --std-out        --no-std-out          Print results to stdout. [default: no-std-out]            │
│ --info-only      --no-info-only        Print summary results only. [default: no-info-only]       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Python

```python
# Recon import
from recon import Reconcile

# Read from files
recon = Reconcile.read_files(
    left_file="sales_orders.xlsx",
    right_file="deliveries.csv",
    left_on="Document #",
    right_on="Sales Order #",
    left_kwargs={"sheet_name": "Sales"},
)

# Or read from pandas dataframes
recon = Reconcile.read_df(
    left_df=sales_df,
    right_df=deliveries_df,
    left_on="Document #",
    right_on="Sales Order #",
)

# Properties:
# Components of the recon are lazily evaluated and cached as you access the relevant properties.
# All properties return a pandas DataFrame.
# The original indexes are preserved, except for the .both property where the original indexes are columns.
recon.left  # Original left dataset
recon.right  # Original right dataset

recon.left_only  # Records from left dataset which is not found in the right dataset.
recon.right_only  # Records from right dataset which is not found in the left dataset.

recon.left_duplicate  # Duplicate records in the left dataset. The first record is not listed.
recon.right_duplicate  # Duplicate records in the right dataset. The first record is not listed.

recon.left_both  # Records from left dataset which is also found in the right dataset.
recon.right_both # Records from right dataset which is also found in the left dataset.

recon.both  # Common records. A merger of both datasets
recon.all_data # All records classified. A merger of both datasets

recon.is_left_unique  # bool. Are there duplicate records within the `left_on` field?
recon.is_right_unique  # bool. Are there duplicate records within the `right_on` field?
recon.relationship  # 1:1, 1:m, m:1 or m:m relationship between datasets

# Output methods:
# `recon_components` parameter is an ordered list of any of the DataFrame property names.
# "all" is a shorthand for most properties.
recon.info()  # Prints a summary of recon results
recon.to_stdout(recon_components=["all"]) # Prints all recon results to console
recon.to_xlsx(path="recon_results.xlsx", recon_components=["all"]) # Saves all recon results to xlsx
recon.to_object() # returns a ReconciledReport object
```

## Dependencies

- [pandas](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html#required-dependencies) with [performance](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html#performance-dependencies-recommended) and [excel](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html#excel-files) optional dependencies to perform the reconciliation.
- [Typer](https://typer.tiangolo.com/) powers the command line interface.

## License

[MIT](LICENSE)
