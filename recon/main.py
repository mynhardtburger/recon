import sys
from enum import StrEnum
from functools import cached_property
from os import PathLike
from textwrap import dedent
from typing import Literal, Union

import pandas as pd

FilePath = Union[str, "PathLike[str]"]
Suffixes = Union[
    list[Union[str, None]], tuple[str, None], tuple[None, str], tuple[str, str]
]

RECON_COMPONENTS = Literal[
    "left_both",
    "right_both",
    "left_only",
    "right_only",
    "left_duplicate",
    "right_duplicate",
    "both",
    "data_map",
    "all_data",
    "all",
]


class Relationship(StrEnum):
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:m"
    MANY_TO_ONE = "m:1"
    MANY_TO_MANY = "m:m"
    NONE = ""


class Reconcile:
    def __init__(
        self,
        left: pd.DataFrame,
        right: pd.DataFrame,
        left_on: str,
        right_on: str,
        suffixes: Suffixes = ("_left", "_right"),
    ) -> None:
        self.left = left
        self.right = right
        self.left_on = left_on
        self.right_on = right_on

        if isinstance(self.left, pd.Series):
            self.left = self.left.to_frame(name="left")
            self.left_on = "left"
        if isinstance(self.right, pd.Series):
            self.right = self.right.to_frame(name="right")
            self.right_on = "right"

        self.suffixes = suffixes

        self._left_name_map, self._right_name_map = self._map_column_names()

        self.output_dispatch: dict[str, Union[pd.Series, pd.DataFrame]] = {
            "left_only": self.left_only,
            "right_only": self.right_only,
            "left_duplicate": self.left_duplicate,
            "right_duplicate": self.right_duplicate,
            "left_both": self.left_both,
            "right_both": self.right_both,
            "left": self.left,
            "right": self.right,
            "both": self.both,
            "all": self.all_data,
        }

    @cached_property
    def all_data(self) -> pd.DataFrame:
        return pd.merge(
            self.left.reset_index(names="index"),
            self.right.reset_index(names="index"),
            left_on=self.left_on,
            right_on=self.right_on,
            indicator=True,
            how="outer",
            suffixes=self.suffixes,
        )

    @cached_property
    def both(self) -> pd.DataFrame:
        return self.all_data.loc[self.all_data["_merge"] == "both"]

    @cached_property
    def left_both(self) -> pd.DataFrame:
        return (
            self.both[self._left_name_map.values()]
            .drop_duplicates()
            .set_index(f"index{self.suffixes[0]}")
        )

    @cached_property
    def right_both(self) -> pd.DataFrame:
        return (
            self.both[self._right_name_map.values()]
            .drop_duplicates()
            .set_index(f"index{self.suffixes[1]}")
        )

    @cached_property
    def left_only(self) -> pd.DataFrame:
        return self.all_data.loc[
            self.all_data["_merge"] == "left_only", list(self._left_name_map.values())
        ].set_index(f"index{self.suffixes[0]}")

    @cached_property
    def right_only(self) -> pd.DataFrame:
        return self.all_data.loc[
            self.all_data["_merge"] == "right_only", list(self._right_name_map.values())
        ].set_index(f"index{self.suffixes[1]}")

    @cached_property
    def left_duplicate(self) -> pd.DataFrame:
        return self.left.loc[self.left.duplicated(keep="first")]

    @cached_property
    def right_duplicate(self) -> pd.DataFrame:
        return self.right.loc[self.right.duplicated(keep="first")]

    @cached_property
    def is_left_unique(self) -> bool:
        return self.left[self.left_on].is_unique

    @cached_property
    def is_right_unique(self) -> bool:
        return self.right[self.right_on].is_unique

    @cached_property
    def relationship(self) -> Relationship:
        if self.is_left_unique and self.is_right_unique:
            return Relationship.ONE_TO_ONE
        elif self.is_left_unique and not self.is_right_unique:
            return Relationship.ONE_TO_MANY
        elif not self.is_left_unique and self.is_right_unique:
            return Relationship.MANY_TO_ONE
        else:
            return Relationship.MANY_TO_MANY

    def _map_column_names(self):
        left_columns = set(self.left.reset_index(names="index").columns)
        right_columns = set(self.right.reset_index(names="index").columns)
        common_columns = left_columns & right_columns
        left_only = left_columns - right_columns
        right_only = right_columns - left_columns

        # Where the merge on column has the same name pandas doesn't add a suffix
        if self.left_on == self.right_on:
            common_columns.remove(self.left_on)
            left_columns.add(self.left_on)
            right_columns.add(self.right_on)

        if len(self.suffixes) == 1:
            suffixes = (self.suffixes[0], "")
        assert self.suffixes[0] or self.suffixes[1]
        suffixes = (
            self.suffixes[0] or "",
            self.suffixes[1] or "",
        )

        left_map: dict[str, str] = {}
        left_map.update({col: col for col in left_only})
        left_map.update({col: col + suffixes[0] for col in common_columns})

        right_map: dict[str, str] = {}
        right_map.update({col: col for col in right_only})
        right_map.update({col: col + suffixes[1] for col in common_columns})

        return left_map, right_map

    def info(self) -> None:
        left_stats = (
            f"{len(self.left_both):,d} common + "
            f"{len(self.left_only):,d} unique = "
            f"{len(self.left):,d} records"
        )
        right_stats = (
            f"{len(self.right_both):,d} common + "
            f"{len(self.left_only):,d} unique = "
            f"{len(self.right):,d} records"
        )
        report = dedent(
            f"""
        Reconciliation summary

        Left: {left_stats}
        Right: {right_stats}
        Relationship: {self.relationship} ({self.left_on}:{self.right_on})
        """
        )
        print(report)

    def to_xlsx(
        self, path: FilePath, recon_components: list[RECON_COMPONENTS], **kwargs
    ) -> None:
        write_list = (
            self.output_dispatch.keys()
            if "all_data" in recon_components
            else recon_components
        )

        with pd.ExcelWriter(path, **kwargs) as writer:
            for component in write_list:
                self.output_dispatch[component].to_excel(
                    writer, sheet_name=component, index_label="index"
                )

    def to_stdout(self, recon_components: list[RECON_COMPONENTS], **kwargs) -> None:
        write_list = (
            self.output_dispatch.keys()
            if "all_data" in recon_components
            else recon_components
        )

        for component in write_list:
            print(f"--------- {component} ----------")
            self.output_dispatch[component].to_csv(
                sys.stdout, index_label="index", **kwargs
            )
