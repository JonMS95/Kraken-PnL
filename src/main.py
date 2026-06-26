import pandas as pd
import argparse
from utils_csv import get_df_from_csv, write_df_to_csv
from utils_log import DataLogger
from utils_fx import init_fx_cache, save_fx_cache
from extract_asset_data import extract_asset_events, clean_kraken_data
from gen_columns import gen_clean_events, add_fx_conversion, gen_data
from apply_fifo import compute_fifo_pnl, compute_fifo
from logging import INFO, DEBUG#, WARNING, ERROR, CRITICAL


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

    parser.add_argument(
        "--fx-cache-path",
        "-f",
        required=False,
        default="cache/fx.csv",
        help="Input Kraken CSV file"
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging"
    )

    return parser.parse_args()


def get_asset_yearly_pnl_from_df(df: pd.DataFrame, year: int) -> float:
    df["time"] = pd.to_datetime(df["time"])
    return df.loc[df["time"].dt.year == year, "pnl"].sum()


def get_asset_yearly_pnl(input_csv_path: str, asset: str, target_cur: str, year: int, output_csv_path: str, fx_cache_path: str) -> int:
    _dlog.log_inf(f"Computing yearly PnL")
    _dlog.log_inf(f"Input CSV: {input_csv_path}")
    _dlog.log_inf(f"Asset: {asset}")
    _dlog.log_inf(f"Currency: {target_cur}")
    _dlog.log_inf(f"Year: {year}")
    _dlog.log_inf(f"Output CSV: {output_csv_path or 'none'}")
    _dlog.log_inf(f"Fx cache path: {fx_cache_path}")
    
    raw_df: pd.DataFrame = get_df_from_csv(input_csv_path)
    # print(sorted(raw_df["type"].unique()))
    
    asset_df: pd.DataFrame = extract_asset_events(raw_df, asset)
    # utils_csv.write_df_to_csv(asset_df, "asset.csv")
    
    clean_df: pd.DataFrame = gen_clean_events(asset_df)
    # utils_csv.write_df_to_csv(clean_df, "clean.csv")

    init_fx_cache(fx_cache_path)
 
    converted_df: pd.DataFrame = add_fx_conversion(clean_df, target_cur)
    # utils_csv.write_df_to_csv(converted_df, "converted.csv")

    save_fx_cache(fx_cache_path)

    fifo_df: pd.dataFrame = compute_fifo_pnl(converted_df)
    # utils_csv.write_df_to_csv(fifo_df, "pnl.csv")

    if len(output_csv_path) > 0:
        write_df_to_csv(fifo_df, output_csv_path)

    return get_asset_yearly_pnl_from_df(fifo_df, int(year))


def main() -> None:
    args = parse_args()
    _dlog.set_log_level(DEBUG if args.verbose == True else INFO)

    try:
      pnl_asset_year = get_asset_yearly_pnl(args.input, args.asset, args.currency, args.year, args.output, args.fx_cache_path)
    except Exception as ex:
        _dlog.log_err(f"{ex}")
    finally:
        _dlog.log_inf(f"PnL for {args.asset} in {args.year} (as {args.currency}): {pnl_asset_year}")

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
