import pandas as pd
import argparse
import os
from collections import deque

def parse_args():
    parser = argparse.ArgumentParser(description="Kraken FIFO rent calculator")

    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input Kraken CSV file"
    )

    return parser.parse_args()


def extract_pair(df: pd.DataFrame) -> str:
    if "pair" not in df.columns:
        raise ValueError("Column 'pair' not found")

    unique_pairs = df["pair"].dropna().unique()

    if len(unique_pairs) != 1:
        raise ValueError(f"Expected 1 pair, found: {unique_pairs}")

    return unique_pairs[0]


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
    required = ["time", "pair", "type", "vol", "cost", "fee"]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # extract pair BEFORE dropping
    pair = extract_pair(df)

    df = df.sort_values(by="time")

    # net amount
    df["net_amount"] = df.apply(calculate_net_amount, axis=1)

    # real unit price
    df["real_unit_price"] = df["net_amount"] / df["vol"]

    # remove metadata
    df = df.drop(columns=["pair"])

    print("[OK] FIFO completed")

    return df


def main():
    args = parse_args()
    gen_data(args.input)


if __name__ == "__main__":
    main()