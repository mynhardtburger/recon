import pandas as pd

from recon.main import Relationship, apply_index_map, common, index_map, recon, uniques


def test_index_map():
    s1 = pd.Series([1, 2, 3])
    s2 = pd.Series([1, 3, 4])

    output = index_map(s1, s2)
    expected = pd.Series(data=[[0], [], [1]], index=[0, 1, 2], name="index_map")

    pd.testing.assert_series_equal(output, expected)


def test_uniques():
    s1 = pd.Series(data=[1, 1, 3, 6])
    s2 = pd.Series(data=[1, 2, 3, 4, 5])

    expected_left = pd.Series(data=[6], index=[3])
    expected_right = pd.Series(data=[2, 4, 5], index=[1, 3, 4])

    expected_left_map = pd.Series(index=[3], data=[[]], name="index_map")
    expected_right_map = pd.Series(index=[1, 3, 4], data=[[], [], []], name="index_map")

    output = uniques(s1, s2)

    pd.testing.assert_series_equal(expected_left, output.left)
    pd.testing.assert_series_equal(expected_right, output.right)
    pd.testing.assert_series_equal(output.left_map, expected_left_map)
    pd.testing.assert_series_equal(output.right_map, expected_right_map)
    assert output.relationship is None


def test_common():
    s1 = pd.Series([1, 2, 3, 4, 4, 6])
    s2 = pd.Series([1, 3, 3, 4, 5])

    expected_left = pd.Series(data=[1, 3, 4, 4], index=[0, 2, 3, 4])
    expected_right = pd.Series(data=[1, 3, 3, 4], index=[0, 1, 2, 3])

    expected_left_map = pd.Series(
        index=[0, 2, 3, 4], data=[[0], [1, 2], [3], [3]], name="index_map"
    )
    expected_right_map = pd.Series(
        index=[0, 1, 2, 3], data=[[0], [2], [2], [3, 4]], name="index_map"
    )

    output = common(s1, s2)

    pd.testing.assert_series_equal(output.left, expected_left)
    pd.testing.assert_series_equal(output.right, expected_right)
    pd.testing.assert_series_equal(output.left_map, expected_left_map)
    pd.testing.assert_series_equal(output.right_map, expected_right_map)
    assert output.relationship == Relationship.MANY_TO_MANY


def test_recon():
    s1 = pd.Series([1, 2, 3])
    s2 = pd.Series([1, 3, 4])

    expected_left_common = pd.Series(data=[1, 3], index=[0, 2])
    expected_right_common = pd.Series(data=[1, 3], index=[0, 1])
    expected_left_unique = pd.Series(data=[2], index=[1])
    expected_right_unique = pd.Series(data=[4], index=[2])

    expected_left_map = pd.Series(
        index=[0, 2, 1], data=[[0], [1], []], name="index_map"
    )
    expected_right_map = pd.Series(
        index=[0, 1, 2], data=[[0], [2], []], name="index_map"
    )

    output = recon(s1, s2)

    # Test recon components
    pd.testing.assert_series_equal(output.left_common, expected_left_common)
    pd.testing.assert_series_equal(output.right_common, expected_right_common)
    pd.testing.assert_series_equal(output.left_unique, expected_left_unique)
    pd.testing.assert_series_equal(output.right_unique, expected_right_unique)
    pd.testing.assert_series_equal(output.left_map, expected_left_map)
    pd.testing.assert_series_equal(output.right_map, expected_right_map)
    assert output.relationship == Relationship.ONE_TO_ONE

    # Test reconstruction of left and right matches their original
    pd.testing.assert_series_equal(
        left=pd.concat([output.left_common, output.left_unique]).sort_index(),
        right=s1,
    )
    pd.testing.assert_series_equal(
        left=pd.concat([output.right_common, output.right_unique]).sort_index(),
        right=s2,
    )

    # Test left + changes = right
    reconstructed_s2 = pd.concat(
        [
            apply_index_map(output.left_common, output.left_map),
            output.right_unique,
        ]
    ).sort_index()
    pd.testing.assert_series_equal(left=reconstructed_s2, right=s2)


def test_apply_index_map():
    s1 = pd.Series([1, 2, 3, 3])
    s2 = pd.Series([1, 3, 4, 1])

    common_output = common(s1, s2)

    index_map_output = apply_index_map(s1, common_output.left_map)
    expected_output = pd.Series(index=[0, 1, 3], data=[1, 3, 1])

    pd.testing.assert_series_equal(
        index_map_output.sort_index(), expected_output.sort_index()
    )
