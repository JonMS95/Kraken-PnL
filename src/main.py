import pandas as pd
import argparse
from pprint import pprint
import utils_csv
from extract_asset_data import clean_kraken_data
from gen_columns import gen_data
from apply_fifo import compute_fifo
from utils_log import DataLogger


_dlog : DataLogger = DataLogger()


def parse_args():
    parser = argparse.ArgumentParser(description="Kraken FIFO rent calculator")

    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input Kraken CSV file"
    )

    parser.add_argument(
        "--asset",
        "-a",
        required=True,
        help="Target asset to be inspected"
    )

    parser.add_argument(
        "--year",
        "-y",
        required=True,
        type=int,
        help="Target year to obtain PnL for"
    )

    parser.add_argument(
        "--currency",
        "-c",
        required=True,
        help="Target currency"
    )

    parser.add_argument(
        "--output",
        "-o",
        required=False,
        default="",
        help="Input Kraken CSV file"
    )

    return parser.parse_args()


def get_asset_yearly_pnl_from_df(df: pd.DataFrame, year: int) -> float:
    df["time"] = pd.to_datetime(df["time"])
    return df.loc[df["time"].dt.year == year, "pnl"].sum()


def get_asset_yearly_pnl(input_csv_path: str, asset: str, target_cur: str, year: int, output_csv_path: str) -> int:
    raw_df: pd.DataFrame = utils_csv.get_df_from_csv(input_csv_path)
    
    clean_asset_df: pd.DataFrame    = clean_kraken_data(raw_df, asset)
    asset_data_df: pd.DataFrame     = gen_data(clean_asset_df)
    fifo_data_df: pd.DataFrame      = compute_fifo(asset_data_df, target_cur)
    
    if len(output_csv_path) > 0:
        utils_csv.write_df_to_csv(fifo_data_df, output_csv_path)

    pnl_asset_year: float = get_asset_yearly_pnl_from_df(fifo_data_df, int(year))

    _dlog.log_inf(f"PnL for {asset} in {year} (as {target_cur}): {pnl_asset_year}")
    
    return pnl_asset_year


def main() -> None:
    args = parse_args()
    get_asset_yearly_pnl(args.input, args.asset, args.currency, args.year, args.output)

if __name__ == "__main__":
    main()

'''
Usage examples:

python3 src/main.py -i dat/kraken_spot_trades_2021-04-12-2026-06-11.csv -a BTC -y 2025 -c EUR

for asset in BTC ETH ADA
do
    python3 src/main.py -i dat/kraken_spot_trades_2021-04-12-2026-06-11.csv -a ${asset} -y 2025 -c EUR -o dat/PnL_2025_${asset}.csv
done
'''
