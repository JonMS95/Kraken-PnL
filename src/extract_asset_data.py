import pandas as pd
import argparse
import os
import utils_csv


def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Clean Kraken CSV for FIFO processing")

    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input Kraken CSV file"
    )

    parser.add_argument(
        "--pair",
        "-p",
        required=True,
        help="Trading pair filter (e.g. BTC/EUR)"
    )

    return parser.parse_args()


def clean_kraken_data(df: pd.DataFrame, asset: str) -> pd.DataFrame:
    """
    Reads dataframe and generates a cleaned DataFrame filtered by base asset:
    time, pair, type, vol, cost, fee

    Example:
        asset = "BTC"
        keeps BTC/EUR, BTC/USD, BTC/USDT, etc.
    """

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


def build_output_filename(input_file: str, pair: str) -> str:
    """
    Builds output filename like:
    kraken_2026_yo_BTC_EUR_clean.csv
    while preserving original extension.
    """

    base_name, ext = os.path.splitext(os.path.basename(input_file))
    pair_clean = pair.replace("/", "_")

    return f"{base_name}_{pair_clean}_clean{ext}"
