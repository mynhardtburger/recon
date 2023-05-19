# recon-cli: Simple command line tool to reconcile lists

## What is it

**recon-cli** is a Python package and cli tool to reconcile datasets against each other using a common key/field. It aims to be provide a simple interface for reliable reconciliations, removing common logic errors made when performing reconciliations. Under the hood it makes use of [pandas](https://github.com/pandas-dev/pandas) to merge, filter and categorize the datasets.

## Where to get it

The source code is currently hosted on GitHub at: https://github.com/mynhardtburger/recon-cli

Binary installers for the latest released version are available at the [Python
Package Index (PyPI)](https://pypi.org/project/recon-cli)

```sh
pipx install recon-cli
```

## Usage

```plaintext
 Usage: recon [OPTIONS] LEFT RIGHT LEFT_ON RIGHT_ON

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────╮
│ *    left          FILE  Path to the left dataset. [required]                                        │
│ *    right         FILE  Path to the right dataset. [required]                                       │
│ *    left_on       TEXT  Reconcile using this field from the left dataset. [required]                │
│ *    right_on      TEXT  Reconcile using this field from the right dataset. [required]               │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Input options ──────────────────────────────────────────────────────────────────────────────────────╮
│ --left-suffix         TEXT  Suffix to append to the left dataset's column names. [default: _left]    │
│ --right-suffix        TEXT  Suffix to append to the right dataset's column names. [default: _right]  │
│ --left-sheet          TEXT  Sheet to read from left if left is a spreadsheet. [default: Sheet1]      │
│ --right-sheet         TEXT  Sheet to read from left if left is a spreadsheet. [default: Sheet1]      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Output options ─────────────────────────────────────────────────────────────────────────────────────╮
│ --output-file                      TEXT  Path to save results (in xlsx format) to.                   │
│ --std-out        --no-std-out            Print results to stdout. [default: no-std-out]              │
│ --info-only      --no-info-only          Print summary results only. [default: no-info-only]         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Dependencies

- [pandas](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html#required-dependencies): NumPy, python-dateutil, pytz.

- [pandas[performance]](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html#performance-dependencies-recommended): numexpr, bottleneck, numba.
- [pandas[excel]](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html#excel-files): xlrd, xlsxwriter, openpyxl, pyxlsb.

## License

[MIT](LICENSE)
