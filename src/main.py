import pandas as pd
import argparse
from utils_log import DataLogger
from logging import INFO, DEBUG
from pnl import get_pnl


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
        "-t",
        "--trades",
        action="store_true",
        default=False,
        help="Use trades file instead of ledger file (not recommended, always prefer ledger files)"
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging"
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _dlog.set_log_level(DEBUG if args.verbose == True else INFO)

    _dlog.log_inf(f"Input CSV: {args.input}")
    _dlog.log_inf(f"Asset: {args.asset}")
    _dlog.log_inf(f"Year: {args.year}")
    _dlog.log_inf(f"Currency: {args.currency}")
    _dlog.log_inf(f"Output CSV: {args.output or 'none'}")
    _dlog.log_inf(f"Fx cache path: {args.fx_cache_path}")
    _dlog.log_inf(f"Use trades file: {args.trades}")

    try:
        pnl_asset_year = get_pnl(args.input, args.asset, args.currency, args.year, args.output, args.fx_cache_path, args.trades)
    except Exception as ex:
        _dlog.log_err(f"{ex}")
    finally:
        _dlog.log_inf(f"PnL for {args.asset} in {args.year} (as {args.currency}): {pnl_asset_year: .2f}")

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
