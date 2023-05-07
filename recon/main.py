from typing import NamedTuple

import pandas as pd


class SeriesResults(NamedTuple):
    series_a: pd.Series
    series_b: pd.Series


def uniques(series_a: pd.Series, series_b: pd.Series):
    """
    Filter for unique items which only in one of the series.

    Indexes are preserved.
    """
    if not isinstance(series_a, pd.Series):
        raise ValueError("series_a is not a Pandas.Series object")
    if not isinstance(series_b, pd.Series):
        raise ValueError("series_a is not a Pandas.Series object")

    return SeriesResults(
        series_a=series_a[~series_a.isin(series_b)],
        series_b=series_b[~series_b.isin(series_a)],
    )


def common(series_a: pd.Series, series_b: pd.Series):
    """
    Filter for common items which exists in both series.

    Indexes are preserved.
    """
    if not isinstance(series_a, pd.Series):
        raise ValueError("series_a is not a Pandas.Series object")
    if not isinstance(series_b, pd.Series):
        raise ValueError("series_a is not a Pandas.Series object")

    return SeriesResults(
        series_a=series_a[series_a.isin(series_b)],
        series_b=series_b[series_b.isin(series_a)],
    )
