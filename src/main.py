import pandas as pd
import argparse
from pprint import pprint
import utils_csv
from extract_asset_data import clean_kraken_data
from gen_columns import gen_data
from apply_fifo import compute_fifo

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
        "--asset",
        "-a",
        required=True,
        help="Target asset to be inspected"
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pprint(vars(args))

    raw_df: pd.DataFrame = utils_csv.get_df_from_csv(args.input)
    clean_asset_df: pd.DataFrame = clean_kraken_data(raw_df, args.asset)
    
    # utils_csv.write_df_to_csv(clean_asset_df, args.output)
    # return
    
    asset_data_df: pd.DataFrame = gen_data(clean_asset_df)
    
    utils_csv.write_df_to_csv(asset_data_df, args.output)
    
    # Add an additional input parameter here, such as target currency (EUR)
    fifo_data_df: pd.DataFrame = compute_fifo(asset_data_df)
    # utils_csv.write_df_to_csv(fifo_data_df, args.output)

if __name__ == "__main__":
    main()