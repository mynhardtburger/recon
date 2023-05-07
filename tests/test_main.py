import pandas as pd

from recon.main import SeriesResults, common, uniques


def test_uniques():
    s1 = pd.Series(data=[1, 1, 3, 6])
    s2 = pd.Series(data=[1, 2, 3, 4, 5])

    expected = SeriesResults(
        series_a=pd.Series(data=[6], index=[3]),
        series_b=pd.Series(data=[2, 4, 5], index=[1, 3, 4]),
    )

    output = uniques(s1, s2)

    pd.testing.assert_series_equal(expected.series_a, output.series_a)
    pd.testing.assert_series_equal(expected.series_b, output.series_b)


def test_common():
    s1 = pd.Series([1, 2, 3, 4, 4, 6])
    s2 = pd.Series([1, 3, 3, 4, 5])

    expected = SeriesResults(
        series_a=pd.Series(data=[1, 3, 4, 4], index=[0, 2, 3, 4]),
        series_b=pd.Series(data=[1, 3, 3, 4], index=[0, 1, 2, 3]),
    )

    output = common(s1, s2)

    pd.testing.assert_series_equal(expected.series_a, output.series_a)
    pd.testing.assert_series_equal(expected.series_b, output.series_b)
