from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from os import PathLike
from textwrap import dedent
from typing import Any, Literal, Optional, Union

import pandas as pd

from recon.utils import ensure_df

FilePath = Union[str, "PathLike[str]"]
Suffixes = Union[
    list[Union[str, None]], tuple[str, None], tuple[None, str], tuple[str, str]
]

RECON_COMPONENTS = Literal[
    "left_only",
    "right_only",
    "left_duplicate",
    "right_duplicate",
    "left_both",
    "right_both",
    "left",
    "right",
    "both",
    "all_data",
    "all",
]


Relationship = Enum(
    "Relationship", ["ONE_TO_ONE", "ONE_TO_MANY", "MANY_TO_ONE", "MANY_TO_MANY", "NONE"]
)


@dataclass
class ReconciledData:
    both: pd.DataFrame
    left_duplicate: pd.DataFrame
    right_duplicate: pd.DataFrame
    left_only: pd.DataFrame
    right_only: pd.DataFrame


@dataclass
class ReconciledArgs:
    left_on: str
    right_on: str
    left_suffix: Optional[str] = None
    right_suffix: Optional[str] = None
    left_sheet_name: Optional[str] = None
    right_sheet_name: Optional[str] = None


@dataclass
class ReconciledStats:
    rows: int = 0
    both_rows: int = 0
    unique_rows: int = 0
    duplicated_rows: int = 0


@dataclass
class ReconciledReport:
    data: ReconciledData
    args: ReconciledArgs
    relationship: Relationship
    left_stats: ReconciledStats
    right_stats: ReconciledStats


class Reconcile:
    def __init__(self) -> None:
        self.left: pd.DataFrame
        self.right: pd.DataFrame
        self.left_on: str
        self.right_on: str
        self.left_sheet_name: Optional[str] = None
        self.right_sheet_name: Optional[str] = None

        self.suffixes: tuple[str, str]

        self._output_dispatch = [
            "left_only",
            "right_only",
            "left_duplicate",
            "right_duplicate",
            "left_both",
            "right_both",
            "left",
            "right",
            "both",
            "all_data",
        ]
        """List of property names available for output."""

        self._all = [
            "left_only",
            "right_only",
            "left_duplicate",
            "right_duplicate",
            "left_both",
            "right_both",
            "left",
            "right",
        ]
        """List of property names represented by "all"."""

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

    @cached_property
    def all_data(self) -> pd.DataFrame:
        self._left_name_map, self._right_name_map = self._map_column_names()

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
        return self.all_data.loc[self.all_data["_merge"] == "both"].convert_dtypes()

    @cached_property
    def left_both(self) -> pd.DataFrame:
        return (
            self.both[self._left_name_map.values()]
            .drop_duplicates()
            .convert_dtypes()
            .set_index(f"index{self.suffixes[0]}")
        )

    @cached_property
    def right_both(self) -> pd.DataFrame:
        return (
            self.both[self._right_name_map.values()]
            .drop_duplicates()
            .convert_dtypes()
            .set_index(f"index{self.suffixes[1]}")
        )

    @cached_property
    def left_only(self) -> pd.DataFrame:
        return (
            self.all_data.loc[
                self.all_data["_merge"] == "left_only",
                list(self._left_name_map.values()),
            ]
            .convert_dtypes()
            .set_index(f"index{self.suffixes[0]}")
        )

    @cached_property
    def right_only(self) -> pd.DataFrame:
        return (
            self.all_data.loc[
                self.all_data["_merge"] == "right_only",
                list(self._right_name_map.values()),
            ]
            .convert_dtypes()
            .set_index(f"index{self.suffixes[1]}")
        )

    @cached_property
    def left_duplicate(self) -> pd.DataFrame:
        return (
            self.left.loc[self.left.duplicated(keep="first")]
            .rename_axis(index=f"index{self.suffixes[0]}")
            .convert_dtypes()
        )

    @cached_property
    def right_duplicate(self) -> pd.DataFrame:
        return (
            self.right.loc[self.right.duplicated(keep="first")]
            .rename_axis(index=f"index{self.suffixes[1]}")
            .convert_dtypes()
        )

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

    def to_object(self) -> ReconciledReport:
        return ReconciledReport(
            data=ReconciledData(
                both=self.both,
                left_duplicate=self.left_duplicate,
                right_duplicate=self.right_duplicate,
                left_only=self.left_only,
                right_only=self.right_only,
            ),
            args=ReconciledArgs(
                left_on=self.left_on,
                right_on=self.right_on,
                left_suffix=self.suffixes[0],
                right_suffix=self.suffixes[1],
                left_sheet_name=self.left_sheet_name,
                right_sheet_name=self.right_sheet_name,
            ),
            relationship=self.relationship,
            left_stats=ReconciledStats(
                rows=len(self.left),
                both_rows=len(self.left_both),
                unique_rows=len(self.left_only),
                duplicated_rows=len(self.left_duplicate),
            ),
            right_stats=ReconciledStats(
                rows=len(self.right),
                both_rows=len(self.right_both),
                unique_rows=len(self.right_only),
                duplicated_rows=len(self.right_duplicate),
            ),
        )

    def to_xlsx(
        self,
        path: FilePath,
        recon_components: list[RECON_COMPONENTS] = ["all"],
        **kwargs,
    ) -> None:
        if recon_components == ["all"]:
            write_list = self._all
        else:
            write_list = [x for x in recon_components if x in self._output_dispatch]

        with pd.ExcelWriter(path, **kwargs) as writer:
            for component in write_list:
                getattr(self, component).to_excel(
                    writer, sheet_name=component, index_label="index"
                )

    def to_stdout(
        self, recon_components: list[RECON_COMPONENTS] = ["all"], **kwargs
    ) -> None:
        if recon_components == ["all"]:
            write_list = self._all
        else:
            write_list = [x for x in recon_components if x in self._output_dispatch]

        print("--------- START ----------")
        for component in write_list:
            print(f"--------- {component} ----------")
            getattr(self, component).to_csv(sys.stdout, index_label="index", **kwargs)
        print("--------- END ----------")

    @staticmethod
    def _read_obj(
        data: Any,
        sheet_name: str = "Sheet1",
        **kwargs,
    ):
        try:
            excel_file = pd.ExcelFile(data)
        except Exception:
            pass
        else:
            return pd.read_excel(excel_file, sheet_name, **kwargs)

        return pd.read_csv(data, **kwargs)

    @staticmethod
    def _load_df(
        recon_obj: "Reconcile",
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        left_on: str,
        right_on: str,
        suffixes: tuple[str, str] = ("_left", "_right"),
    ):
        recon_obj.left = left_df
        if left_on in recon_obj.left.columns:
            recon_obj.left_on = left_on
        else:
            raise ValueError(
                f"left_on ({left_on}) doesn't exist within the left dataset."
            )

        recon_obj.right = right_df
        if right_on in recon_obj.right.columns:
            recon_obj.right_on = right_on
        else:
            raise ValueError(
                f"right_on ({right_on}) doesn't exist within the right dataset."
            )

        recon_obj.suffixes = suffixes

        return recon_obj

    @staticmethod
    def read_files(
        left_file: FilePath,
        right_file: FilePath,
        left_on: str,
        right_on: str,
        suffixes: tuple[str, str] = ("_left", "_right"),
        left_kwargs: dict[str, Any] = {},
        right_kwargs: dict[str, Any] = {},
    ):
        """
        Returns a :class:`Reconcile` object populated with data which can be queried.

        :param:`left_kwargs` and :param:`right_kwargs` are
        passed onto the `pandas.read_excel()` and `pandas.read_csv()` methods.
        """
        recon = Reconcile()

        left_df = Reconcile._read_obj(left_file, **left_kwargs)
        recon.left_sheet_name = left_kwargs.get("sheet_name", None)

        right_df = Reconcile._read_obj(right_file, **right_kwargs)
        recon.right_sheet_name = right_kwargs.get("sheet_name", None)

        recon = Reconcile._load_df(
            recon, left_df, right_df, left_on, right_on, suffixes
        )

        return recon

    @staticmethod
    def read_df(
        left_df: Union[pd.DataFrame, pd.Series[Any]],
        right_df: Union[pd.DataFrame, pd.Series[Any]],
        left_on: str,
        right_on: str,
        suffixes: tuple[str, str] = ("_left", "_right"),
    ):
        """
        Returns a :class:`Reconcile` object populated with data which can be queried.
        """
        recon = Reconcile()
        recon = Reconcile._load_df(
            recon,
            ensure_df(left_df, "left"),
            ensure_df(right_df, "right"),
            left_on,
            right_on,
            suffixes,
        )

        return recon
