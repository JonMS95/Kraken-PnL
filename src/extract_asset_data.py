import pandas as pd
import argparse
import os
from utils_log import DataLogger


_dlog : DataLogger = DataLogger()


def clean_asset_data(df: pd.DataFrame, asset: str, target_year: int) -> pd.DataFrame:
    """
    Returns all the rows related to a given asset as well as the
    ones they share their refid with (buy/sell ops are paired).
    It removes all spare columns, leaving only these:
    refid,time,type,subclass,asset,amount,fee
    Also, those rows which dates belong to a year greater than
    target are removed.

    Example:
    
    For the input below (data is fully made up and it might not be consistent with real data):

    "txid","refid","time","type","subtype","aclass","subclass","asset","wallet","amount","fee","balance"
    "ABCDEF-GHIJK-LMNOPQ","XXXXXX-YYYYY-ZZZZZZ","2020-01-02 09:16:27","deposit","","currency","fiat","EUR","spot / main",500.0000,0,300.0000
    "RSTUVW-XYZ12-345678","AAAAAA-BBBBB-CCCCCC","2020-01-02 16:31:23","trade","tradespot","currency","fiat","EUR","spot / main",-499.2220,0.7780,0.0000
    "9ABCDE-FGHIJ-KLMNOP","AAAAAA-BBBBB-CCCCCC","2020-03-04 16:31:23","trade","tradespot","currency","crypto","BTC","spot / main",0.0150609600,0,0.0100609600
    
    It would return a dataframe like the following:

    refid,time,type,subclass,asset,amount,fee
    AAAAAA-BBBBB-CCCCCC,AAAAAA-BBBBB-CCCCCC,2020-01-02 16:31:23,trade,fiat,EUR,-499.222,0.778
    AAAAAA-BBBBB-CCCCCC,AAAAAA-BBBBB-CCCCCC,2020-03-04 16:31:23,trade,crypto,BTC,0.01506096,0.0
    """

    _dlog.log_dbg(f"Extracting data for asset: {asset}")

    df = df.copy()

    # Ensure type
    df["amount"] = pd.to_numeric(df["amount"])
    df["fee"] = pd.to_numeric(df["fee"])
    df["time"] = pd.to_datetime(df["time"])

    # Remove spare columns
    df = df.drop(columns=["txid", "subtype", "aclass", "wallet", "balance"])

    # Preserve only the rows for which year within time value is lower or equal than expected
    df = df[df["time"].dt.year <= target_year]

    # Find refid's with target asset (including staking asset)
    # Example, ADA and ADA.S.
    staking_asset: str = f"{asset}.S"
    refids = set(df[df["asset"].isin([asset, staking_asset])]["refid"].dropna().unique())

    # Bring all rows with same refid
    # This pairs buy/selll ops components (such as fiat/crypto transactions)
    related = df[df["refid"].isin(refids)].copy()

    # Replace all staking asset tickers by the original asset's
    related["asset"] = related["asset"].replace(staking_asset, asset)

    # Order by time
    related = related.sort_values("time")

    return related


def clean_asset_data_from_trades(df: pd.DataFrame, asset: str, target_year: int) -> pd.DataFrame:
    """
    Reads dataframe and generates a cleaned DataFrame filtered by base asset:
    time, pair, type, vol, cost, fee

    Also, removes rows with a year greater than provided.

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

    # Preserve only the rows for which year within time value is lower or equal than expected
    df["time"] = pd.to_datetime(df["time"])
    df = df[df["time"].dt.year <= target_year]

    # Order by time (FIFO consistency)
    df = df.sort_values(by="time")

    return df
