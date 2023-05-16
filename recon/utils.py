from typing import Literal, Union

import pandas as pd


def ensure_df(
    data: Union[pd.Series, pd.DataFrame],
    position: Literal["left", "right"],
):
    if isinstance(data, pd.Series):
        return data.to_frame(name=position)
    if isinstance(data, pd.DataFrame):
        return data
    raise ValueError("Object is not a pandas Series or DataFrame.")
