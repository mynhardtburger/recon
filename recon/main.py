from enum import StrEnum
from os import PathLike
from textwrap import dedent
from typing import Literal, Union

import pandas as pd

FilePath = Union[str, "PathLike[str]"]

RECON_COMPONENTS = Literal[
    "left_commons",
    "right_commons",
    "left_uniques",
    "right_uniques",
    "commons",
    "data_map",
    "all",
]


class Relationship(StrEnum):
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:m"
    MANY_TO_ONE = "m:1"
    MANY_TO_MANY = "m:m"
    NONE = ""


class Reconcile:
    def __init__(self, left: pd.Series, right: pd.Series) -> None:
        self.left = left.convert_dtypes()
        self.right = right.convert_dtypes()
        self.data_map = pd.DataFrame()
        """
        index = `left.index`.
        ["value"] = Combined values from `left` and `right`.
        ["right_index"] = Mapped `right.index`.
        """
        self.commons = pd.DataFrame()
        self.left_commons = pd.Series()
        self.right_commons = pd.Series()
        self.left_uniques = pd.Series()
        self.right_uniques = pd.Series()
        self.relationship: Relationship

        self._uniques()
        self._common()
        self._possible_relationship()

    def _uniques(self, refresh=False):
        """
        Filter for unique items which only in one of the series.

        Item order is ignored. Duplicates are preserved. Indexes are preserved.
        """

        def to_series_left(x: pd.DataFrame):
            return pd.Series(
                data=x["value"].convert_dtypes().values,
                index=x.index.astype("int64"),
                name="left_uniques",
            ).rename_axis(index=None)

        def to_series_right(x: pd.Series):
            return pd.Series(
                data=x["value"].convert_dtypes().values,
                index=x["right_index"].astype("int64"),
                name="right_uniques",
            ).rename_axis(index=None)

        self._map_data()

        if self.left_uniques.empty or refresh:
            self.left_uniques = to_series_left(
                self.data_map.loc[self.data_map["right_index"].isna()]
            )

        if self.right_uniques.empty or refresh:
            self.right_uniques = to_series_right(
                self.data_map.loc[self.data_map.index.isna()]
            )

    def _common(self, refresh=False):
        """
        Filter for common items which exists in both series.

        Complex 1:m, m:1 and m:m relationships can be traced using the `left_map` and
        `right_map`.
        Item order is ignored. Duplicates are preserved. Indexes are preserved.
        """

        def to_series_right(x: pd.DataFrame):
            return pd.Series(
                data=x["value"].convert_dtypes().values,
                index=x["right_index"].astype("int64"),
                name="right_commons",
            ).rename_axis(index=None)

        self._map_data()

        if self.commons.empty or refresh:
            self.commons = (
                self.data_map.loc[
                    ~self.data_map.index.isna() & ~self.data_map["right_index"].isna()
                ]
                .rename_axis(index="left_index")
                .convert_dtypes()
            )
            self.left_commons = (
                self.commons["value"]
                .iloc[self.commons.index.drop_duplicates()]
                .rename("left_commons")
                .rename_axis(index=None)
                .convert_dtypes()
            )
            self.left_commons.index = self.left_commons.index.astype("int64")

            self.right_commons = to_series_right(
                self.commons.drop_duplicates("right_index")
            )

    @staticmethod
    def _swap_series_data_index(series: pd.Series, series_name: str):
        return pd.Series(
            data=series.index.values,
            index=series.values,
            name=series_name,
        ).convert_dtypes()

    def _map_data(self, refresh=False):
        """
        Map `left` to `right` through an 'outer' join.
        """
        if self.data_map.empty or refresh:
            self.data_map = (
                self.left.rename_axis(index="left_index")
                .to_frame("value")
                .join(
                    on="value",
                    other=self._swap_series_data_index(self.right, "right_index"),
                    how="outer",
                )
                .rename_axis(index="left_index")
            )

    def _possible_relationship(self, refresh=False):
        """
        Determines the possible relationship between `left` and `right`.
        """

        left_unique = self.left.is_unique
        right_unique = self.right.is_unique

        if left_unique and right_unique:
            self.relationship = Relationship.ONE_TO_ONE
        elif left_unique and not right_unique:
            self.relationship = Relationship.ONE_TO_MANY
        elif not left_unique and right_unique:
            self.relationship = Relationship.MANY_TO_ONE
        else:
            self.relationship = Relationship.MANY_TO_MANY

    def info(self):
        left_stats = (
            f"{self.commons.index.nunique():,d} common + "
            f"{self.left_uniques.size:,d} unique = "
            f"{self.left.size:,d} records"
        )
        right_stats = (
            f"{self.commons['right_index'].nunique():,d} common + "
            f"{self.left_uniques.size:,d} unique = "
            f"{self.right.size:,d} records"
        )
        report = dedent(
            f"""
        Reconciliation summary

        Left ({self.left.name}): {left_stats}
        Right ({self.right.name}): {right_stats}
        Relationship: {self.relationship}
        """
        )
        print(report)

    def to_xlsx(
        self, path: FilePath, recon_components: list[RECON_COMPONENTS], **kwargs
    ):
        df_dispatch: dict[str, Union[pd.Series, pd.DataFrame]] = {
            "left_commons": self.left_commons,
            "right_commons": self.right_commons,
            "left_uniques": self.left_uniques,
            "right_uniques": self.right_uniques,
            "commons": self.commons,
            "data_map": self.data_map,
            "left": self.left,
            "right": self.right,
        }

        write_list = (
            df_dispatch.keys() if "all" in recon_components else recon_components
        )

        with pd.ExcelWriter(path, **kwargs) as writer:
            for component in write_list:
                df_dispatch[component].to_excel(
                    writer, sheet_name=component, index_label="index"
                )
