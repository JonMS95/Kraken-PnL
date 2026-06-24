import pandas as pd
import argparse
import os

def parse_args():
    parser = argparse.ArgumentParser(description="Kraken FIFO rent calculator")

    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input Kraken CSV file"
    )

    return parser.parse_args()


def build_output_filename(input_file: str, pair: str) -> str:
    base, ext = os.path.splitext(os.path.basename(input_file))
    pair_clean = pair.replace("/", "_")
    return f"{base}_{pair_clean}_rent{ext}"


def calculate_net_amount(row):
    tx_type = row["type"].strip().lower()

    if tx_type == "buy":
        return row["cost"] + row["fee"]

    if tx_type == "sell":
        return row["cost"] - row["fee"]

    raise ValueError(f"Unsupported type: {row['type']}")


def gen_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches asset-level dataset (NOT pair-level).
    """

    required = ["time", "pair", "type", "vol", "cost", "fee"]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df.sort_values(by="time")

    # net amount (still valid)
    df["net_amount"] = df.apply(calculate_net_amount, axis=1)

    # real unit price
    df["real_unit_price"] = df["net_amount"] / df["vol"]


    return df
