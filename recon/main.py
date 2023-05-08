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
    right: pd.Series
    relationship: Optional[Relationship]


@dataclass
class ReconResults:
    """Recon results container."""

    common: pd.Series
    """Left's common items."""
    left_unique: pd.Series
    right_unique: pd.Series
    relationship: Optional[Relationship]


def uniques(left: pd.Series, right: pd.Series):
    """
    Filter for unique items which only in one of the series.

    Item order is ignored. Duplicates are preserved. Indexes are preserved.
    """
    left_unique: pd.Series = left[~left.isin(right)]
    right_unique: pd.Series = right[~right.isin(left)]
    return SeriesResults(
        left=left_unique,
        right=right_unique,
        relationship=None,
    )


def common(left: pd.Series, right: pd.Series):
    """
    Filter for common items which exists in both series.

    Item order is ignored. Duplicates are preserved. Indexes are preserved.
    """
    left_common: pd.Series = left[left.isin(right)]
    right_common: pd.Series = right[right.isin(left)]
    return SeriesResults(
        left=left_common,
        right=right_common,
        relationship=possible_relationship(left_common, right_common),
    )


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

    return ReconResults(
        common=common_items.left,
        left_unique=unique_items.left,
        right_unique=unique_items.right,
        relationship=common_items.relationship,
    )
