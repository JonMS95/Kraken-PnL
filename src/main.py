import pandas as pd
import argparse
from pprint import pprint
import utils_csv
from extract_asset_data import clean_kraken_data
from gen_columns import gen_data

def parse_args():
    parser = argparse.ArgumentParser(description="Kraken FIFO rent calculator")

    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input Kraken CSV file"
    )

    parser.add_argument(
        "--output",
        "-o",
        required=False,
        default="",
        help="Input Kraken CSV file"
    )

    parser.add_argument(
        "--pair",
        "-p",
        required=True,
        help="Target pair to be inspected"
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pprint(vars(args))

    raw_df: pd.DataFrame = utils_csv.get_df_from_csv(args.input)
    clean_pair_df: pd.DataFrame = clean_kraken_data(raw_df, pair_filter = args.pair)
    pair_data_df: pd.DataFrame = gen_data(clean_pair_df)
    utils_csv.write_df_to_csv(pair_data_df, args.output)
    return
    fifo_data_df: pd.DataFrame = compute_fifo(pair_data_df)
    fifo_data.to_csv(output)

if __name__ == "__main__":
    main()