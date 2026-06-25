import pandas as pd
import argparse
import os
from utils_log import DataLogger


_dlog : DataLogger = DataLogger()


def clean_kraken_data(df: pd.DataFrame, asset: str) -> pd.DataFrame:
    """
    Reads dataframe and generates a cleaned DataFrame filtered by base asset:
    time, pair, type, vol, cost, fee

    Example:
        asset = "BTC"
        keeps BTC/EUR, BTC/USD, BTC/USDT, etc.
    """

    _dlog.log_inf(f"Extracting data for asset: {asset}")

    required_cols = ["time", "pair", "type", "vol", "cost", "fee"]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns found: {missing}")

    # Extract base asset from pair (e.g. BTC/EUR -> BTC)
    base_asset = df["pair"].str.split("/").str[0]

    # Filter by asset
    df = df[base_asset == asset].copy()

    # Keep only required columns
    df = df[required_cols]

    # Order by time (FIFO consistency)
    df = df.sort_values(by="time")

    return df
