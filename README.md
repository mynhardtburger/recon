# recon-cli: Simple command line tool to reconcile lists

## What is it

**recon-cli** is a Python package and cli tool to reconcile datasets against each other using a common key/field. It aims to be provide a simple interface for reliable reconciliations, removing common logic errors made when performing reconciliations. Under the hood it makes use of [pandas](https://github.com/pandas-dev/pandas) to merge, filter and categorize the datasets.

## Where to get it
The source code is currently hosted on GitHub at: https://github.com/mynhardtburger/recon-cli

Binary installers for the latest released version are available at the [Python
Package Index (PyPI)](https://pypi.org/project/recon-cli)

```sh
pip install recon-cli
```

## Dependencies
- [pandas](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html#required-dependencies): NumPy, python-dateutil, pytz.

- [pandas[performance]](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html#performance-dependencies-recommended): numexpr, bottleneck, numba.
- [pandas[excel]](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html#excel-files): xlrd, xlsxwriter, openpyxl, pyxlsb.

## License
[MIT](LICENSE)
