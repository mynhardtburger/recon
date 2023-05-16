import sys
from enum import Enum
from functools import cached_property
from os import PathLike
from pathlib import PurePath
from textwrap import dedent
from typing import Any, Literal, Union

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


Relationship = Enum(
    "Relationship", ["ONE_TO_ONE", "ONE_TO_MANY", "MANY_TO_ONE", "MANY_TO_MANY", "NONE"]
)


class Reconcile:
    def __init__(self) -> None:
        self.left: pd.DataFrame
        self.right: pd.DataFrame
        self.left_on: str
        self.right_on: str

        self.suffixes: tuple[str, str]

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
            print("--------- END ----------")

    @staticmethod
    def _read_file(
        data: Union[pd.Series, pd.DataFrame, FilePath],
        position: Literal["left", "right"],
        sheet_name: str = "Sheet1",
        **kwargs,
    ):
        if isinstance(data, pd.DataFrame):
            return data

        if isinstance(data, pd.Series):
            return data.to_frame(name=position)

        file_path = PurePath(data)
        if file_path.suffix.lower() in {"xlsx", "xls", "xlsm", "xlsb"}:
            if not isinstance(sheet_name, (str, int)):
                raise ValueError("Importing of multiple sheets is not supported")
            return pd.read_excel(file_path, sheet_name, **kwargs)
        else:
            return pd.read_csv(file_path, **kwargs)

    @staticmethod
    def read_files(
        left: FilePath,
        right: FilePath,
        left_on: str,
        right_on: str,
        suffixes: tuple[str, str] = ("_left", "_right"),
        left_kwargs: dict[str, Any] = {},
        right_kwargs: dict[str, Any] = {},
    ):
        """
        Returns a :class:`Reconcile` object which can be queried.

        Excel files are identified by the ".xlsx" extension. All other extensions
        are assumed to be csv. :param:`left_kwargs` and :param:`right_kwargs` are
        passed onto the `pandas.read_excel()` and `pandas.read_csv()` methods.
        """
        recon = Reconcile()

        recon.left = Reconcile._read_file(left, "left", **left_kwargs)
        if left_on in recon.left.columns:
            recon.left_on = left_on
        else:
            raise ValueError(
                f"left_on ({left_on}) doesn't exist within the left dataset."
            )

        recon.right = Reconcile._read_file(right, "right", **right_kwargs)
        if right_on in recon.right.columns:
            recon.right_on = right_on
        else:
            raise ValueError(
                f"right_on ({right_on}) doesn't exist within the right dataset."
            )

        recon.suffixes = suffixes

        return recon
