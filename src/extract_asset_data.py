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


def clean_kraken_data(df: pd.DataFrame, pair_filter: str) -> pd.DataFrame:
    """
    Reads dataframe and generates a cleaned CSV filtered by pair:
    time, pair, type, vol, cost, fee
    """

    required_cols = ["time", "pair", "type", "vol", "cost", "fee"]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns found: {missing}")

    # Filter by pair
    df = df[df["pair"] == pair_filter]

    df = df[required_cols].copy()

    # Order by date
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


def main():
    args = parse_args()

    output_file = build_output_filename(args.input, args.pair)

    try:
        df: pd.DataFrame = utils_csv.get_df_from_csv(args.input)
        df_clean: pd.DataFrame = clean_kraken_data(df, args.pair)
        utils_csv.write_df_to_csv(df_clean, output_file)
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()