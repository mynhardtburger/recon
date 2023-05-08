import pandas as pd

from recon.main import Relationship, common, recon, uniques


def test_uniques():
    s1 = pd.Series(data=[1, 1, 3, 6])
    s2 = pd.Series(data=[1, 2, 3, 4, 5])

    expected_left = pd.Series(data=[6], index=[3])
    expected_right = pd.Series(data=[2, 4, 5], index=[1, 3, 4])

    output = uniques(s1, s2)

    pd.testing.assert_series_equal(expected_left, output.left)
    pd.testing.assert_series_equal(expected_right, output.right)
    assert output.relationship is None


def test_common():
    s1 = pd.Series([1, 2, 3, 4, 4, 6])
    s2 = pd.Series([1, 3, 3, 4, 5])

    expected_left = pd.Series(data=[1, 3, 4, 4], index=[0, 2, 3, 4])
    expected_right = pd.Series(data=[1, 3, 3, 4], index=[0, 1, 2, 3])

    output = common(s1, s2)

    pd.testing.assert_series_equal(expected_left, output.left)
    pd.testing.assert_series_equal(expected_right, output.right)
    assert output.relationship == Relationship.MANY_TO_MANY


def test_recon():
    s1 = pd.Series([1, 2, 3])
    s2 = pd.Series([1, 3, 4])

    expected_common = pd.Series(data=[1, 3], index=[0, 2])
    expected_left_unique = pd.Series(data=[2], index=[1])
    expected_right_unique = pd.Series(data=[4], index=[2])

    output = recon(s1, s2)

    pd.testing.assert_series_equal(expected_common, output.common)
    pd.testing.assert_series_equal(expected_left_unique, output.left_unique)
    pd.testing.assert_series_equal(expected_right_unique, output.right_unique)
    assert output.relationship == Relationship.ONE_TO_ONE

    s1._is_copy()
