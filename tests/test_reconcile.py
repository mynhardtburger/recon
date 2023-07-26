from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

import recon as rc


@pytest.fixture()
def s1():
    return pd.Series([1, 1, 2, 3, "text"], name="left")


@pytest.fixture()
def df2():
    return pd.DataFrame({"right": [1, 2, 2, "text", 4]})


@pytest.fixture()
def recon(s1, df2):
    return rc.Reconcile.read_df(s1, df2, left_on="left", right_on="right")


def test_reconcile_attributes(s1: pd.Series, df2: pd.Series, recon: rc.Reconcile):
    # Expected data
    left_only = (
        pd.DataFrame({"left": [3], "index_left": [3]})
        .convert_dtypes()
        .set_index("index_left")
    )
    left_duplicate = (
        pd.DataFrame({"left": [1], "index_left": [1]})
        .convert_dtypes()
        .set_index("index_left")
    )

    right_only = (
        pd.DataFrame({"right": [4], "index_right": [4]})
        .convert_dtypes()
        .set_index("index_right")
    )
    right_duplicate = (
        pd.DataFrame({"right": [2], "index_right": [2]})
        .convert_dtypes()
        .set_index("index_right")
    )

    both = pd.DataFrame(
        {
            "index_left": [0, 1, 2, 2, 4],
            "left": [1, 1, 2, 2, "text"],
            "index_right": [0, 0, 1, 2, 3],
            "right": [1, 1, 2, 2, "text"],
            "_merge": ["both", "both", "both", "both", "both"],
        },
        index=[0, 1, 2, 3, 5],
    ).convert_dtypes()
    categories = pd.CategoricalDtype(
        categories=["left_only", "right_only", "both"], ordered=False
    )
    both["_merge"] = both["_merge"].astype(categories)

    left_both = (
        pd.DataFrame({"index_left": [0, 1, 2, 4], "left": [1, 1, 2, "text"]})
        .convert_dtypes()
        .set_index("index_left")
    )

    right_both = (
        pd.DataFrame({"index_right": [0, 1, 2, 3], "right": [1, 2, 2, "text"]})
        .convert_dtypes()
        .set_index("index_right")
    )

    # Assertions
    pd.testing.assert_frame_equal(s1.to_frame(name="left"), recon.left)
    pd.testing.assert_frame_equal(df2, recon.right)

    assert recon.relationship == rc.Relationship.MANY_TO_MANY
    pd.testing.assert_frame_equal(recon.left_only, left_only)
    pd.testing.assert_frame_equal(recon.right_only, right_only)

    pd.testing.assert_frame_equal(
        recon.left_duplicate, left_duplicate, check_index_type=False
    )
    pd.testing.assert_frame_equal(
        recon.right_duplicate, right_duplicate, check_index_type=False
    )

    pd.testing.assert_frame_equal(recon.left_both, left_both)
    pd.testing.assert_frame_equal(recon.right_both, right_both)

    pd.testing.assert_frame_equal(recon.both, both)

    assert not recon.is_left_unique
    assert not recon.is_right_unique


def test_read_files(tmp_path: Path, s1: pd.Series, df2: pd.DataFrame):
    left_file_path = tmp_path / "left.txt"
    s1.to_csv(left_file_path)

    right_file_path = tmp_path / "right.xlsx"
    df2.to_excel(right_file_path)

    recon2 = rc.Reconcile.read_files(
        left_file_path,
        right_file_path,
        left_on="left",
        right_on="right",
    )

    assert recon2
