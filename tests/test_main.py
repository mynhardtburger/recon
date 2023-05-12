import pandas as pd
import pytest

from recon.main import Reconcile, Relationship


@pytest.fixture()
def s1():
    return pd.Series([1, 1, 2, 3, "text"], name="left")


@pytest.fixture()
def s2():
    return pd.Series([1, 2, 2, "text", 4], name="right")


@pytest.fixture()
def rec(s1, s2):
    return Reconcile(s1, s2)


def test_reconcile_attributes(s1: pd.Series, s2: pd.Series, rec: Reconcile):
    # Expected data
    left_uniques = pd.Series(data=[3], index=[3], name="left_uniques").convert_dtypes()
    right_uniques = pd.Series(
        data=[4], index=[4], name="right_uniques"
    ).convert_dtypes()
    commons = (
        pd.DataFrame(
            index=[0, 1, 2, 2, 4],
            data={"value": [1, 1, 2, 2, "text"], "right_index": [0, 0, 1, 2, 3]},
        )
        .rename_axis(index="left_index")
        .convert_dtypes()
    )
    left_commons = pd.Series(
        index=[0, 1, 2, 4], data=[1, 1, 2, "text"], name="left_commons"
    ).convert_dtypes()
    right_commons = pd.Series(
        index=[0, 1, 2, 3], data=[1, 2, 2, "text"], name="right_commons"
    ).convert_dtypes()
    data_map = (
        pd.DataFrame(
            index=[0, 1, 2, 2, 3, 4, pd.NA],
            data={
                "value": [1, 1, 2, 2, 3, "text", 4],
                "right_index": [0, 0, 1, 2, pd.NA, 3, 4],
            },
        )
        .rename_axis(index="left_index")
        .convert_dtypes()
    )
    reconstructed_s2 = pd.concat(
        [
            pd.Series(
                data=rec.commons.drop_duplicates(subset="right_index")["value"].values,
                index=rec.commons.drop_duplicates(subset="right_index")[
                    "right_index"
                ].values,
            ),
            rec.right_uniques,
        ]
    ).convert_dtypes()

    # Assertions
    pd.testing.assert_series_equal(s1, rec.left)
    pd.testing.assert_series_equal(s2, rec.right)

    assert rec.relationship == Relationship.MANY_TO_MANY
    pd.testing.assert_series_equal(rec.left_uniques, left_uniques)
    pd.testing.assert_series_equal(rec.right_uniques, right_uniques)

    pd.testing.assert_series_equal(rec.left_commons, left_commons)
    pd.testing.assert_series_equal(rec.right_commons, right_commons)

    pd.testing.assert_frame_equal(rec.commons, commons, check_index_type=False)
    pd.testing.assert_frame_equal(rec.data_map, data_map, check_index_type=False)

    pd.testing.assert_series_equal(
        reconstructed_s2, s2, check_index_type=False, check_names=False
    )
