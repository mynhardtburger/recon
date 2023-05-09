from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

import pandas as pd


class Relationship(StrEnum):
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:m"
    MANY_TO_ONE = "m:1"
    MANY_TO_MANY = "m:m"


@dataclass
class SeriesResults:
    """Container for left and right series'."""

    left: pd.Series
    left_map: pd.Series
    """`pandas.Series` mapping `left.index` to an Array of right indexes."""

    right: pd.Series
    right_map: pd.Series
    """`pandas.Series` mapping `right.index` to an Array of left indexes."""

    relationship: Optional[Relationship]


@dataclass
class ReconResults:
    """Recon results container."""

    left_common: pd.Series
    left_unique: pd.Series
    left_map: pd.Series
    """`pandas.Series` mapping `left.index` to an Array of right indexes."""

    right_common: pd.Series
    right_unique: pd.Series
    right_map: pd.Series
    """`pandas.Series` mapping `right.index` to an Array of left indexes."""

    relationship: Optional[Relationship]


def uniques(left: pd.Series, right: pd.Series):
    """
    Filter for unique items which only in one of the series.

    Item order is ignored. Duplicates are preserved. Indexes are preserved.
    """
    left_unique: pd.Series = left[~left.isin(right)]
    right_unique: pd.Series = right[~right.isin(left)]
    left_map = index_map(left_unique, right_unique)
    right_map = index_map(right_unique, left_unique)

    return SeriesResults(
        left=left_unique,
        left_map=left_map,
        right=right_unique,
        right_map=right_map,
        relationship=None,
    )


def common(left: pd.Series, right: pd.Series):
    """
    Filter for common items which exists in both series.

    Complex 1:m, m:1 and m:m relationships can be traced using the `left_map` and
    `right_map`.
    Item order is ignored. Duplicates are preserved. Indexes are preserved.
    """
    left_common: pd.Series = left[left.isin(right)]
    right_common: pd.Series = right[right.isin(left)]
    left_map = index_map(left_common, right_common)
    right_map = index_map(right_common, left_common)

    return SeriesResults(
        left=left_common,
        left_map=left_map,
        right=right_common,
        right_map=right_map,
        relationship=possible_relationship(left_common, right_common),
    )


def index_map(left: pd.Series, right: pd.Series):
    """
    Map the index of `left` to the index of `right`.

    Returns a `pandas.Series`, named 'index_map' where the index=left.index and the
    data=mapped right.index.
    """
    # TODO: replace .apply() with a .merge()/.join() based approach
    df = left.to_frame(name="left")
    df["index_map"] = df["left"].apply(lambda x: right.loc[right == x].index.values)
    return df["index_map"]


def possible_relationship(left: pd.Series, right: pd.Series):
    """
    Determines the possible relationship between `left` and `right`.

    Given the data, determines the most optimistic or tightest relationship possible.
    """
    left_unique = left.is_unique
    right_unique = right.is_unique

    if left_unique and right_unique:
        return Relationship.ONE_TO_ONE
    if left_unique and not right_unique:
        return Relationship.ONE_TO_MANY
    if not left_unique and right_unique:
        return Relationship.MANY_TO_ONE
    return Relationship.MANY_TO_MANY


def validate_relationship(
    left: pd.Series, right: pd.Series, relationship: Relationship
):
    """Validates that the relationship between `left` and `right` matches the given
    `relationship`."""
    left_unique = left.is_unique
    right_unique = right.is_unique

    if relationship == Relationship.ONE_TO_ONE:
        return left_unique and right_unique
    if relationship == Relationship.ONE_TO_MANY:
        return left_unique and not right_unique
    if relationship == Relationship.MANY_TO_ONE:
        return not left_unique and right_unique
    if relationship == Relationship.MANY_TO_MANY:
        return not left_unique and not right_unique


def recon(left: pd.Series, right: pd.Series):
    """
    Reconciles `left` against `right`.

    Returns the common,  and unique items in left and right.
    """
    common_items = common(left, right)
    unique_items = uniques(left, right)

    left_map = pd.concat([common_items.left_map, unique_items.left_map])
    right_map = pd.concat([common_items.right_map, unique_items.right_map])

    return ReconResults(
        left_common=common_items.left,
        left_unique=unique_items.left,
        left_map=left_map,
        right_common=common_items.right,
        right_unique=unique_items.right,
        right_map=right_map,
        relationship=common_items.relationship,
    )


def apply_index_map(left_common: pd.Series, left_map: pd.Series):
    """
    Apply element duplicationa and deduplication using `left_map`.

    This had the effect of growing and shrinking `left_common` for frequency
    differences between `left` and `right`.
    The returned `pandas.Series` is equivalent to `right_common`.
    """
    # Method chained to contain memory usage
    exploded_map = left_map.explode().drop_duplicates().dropna().astype("int64")

    # TODO: replace .apply() with a .merge()/.join() based approach
    return pd.Series(data=exploded_map.index, index=exploded_map.values).map(
        lambda x: left_common.loc[x]
    )
