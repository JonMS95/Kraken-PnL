import pandas as pd
import argparse
from pprint import pprint
import utils_csv
from extract_asset_data import clean_kraken_data
from gen_columns import gen_data
from apply_fifo import compute_fifo
from utils_log import DataLogger
from utils_fx import get_fx_rate
from logging import INFO, WARNING, ERROR, DEBUG, CRITICAL


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
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging"
    )

    return parser.parse_args()


def get_asset_yearly_pnl_from_df(df: pd.DataFrame, year: int) -> float:
    df["time"] = pd.to_datetime(df["time"])
    return df.loc[df["time"].dt.year == year, "pnl"].sum()


def extract_asset_events(df: pd.DataFrame, asset: str) -> pd.DataFrame:
    """
    Devuelve todas las filas del ledger relacionadas con un asset,
    incluyendo todas las líneas que comparten refid con ese asset.
    """

    df = df.copy()

    # Ensure type
    df["amount"] = pd.to_numeric(df["amount"])
    df["fee"] = pd.to_numeric(df["fee"])

    # Remove spare columns
    df = df.drop(columns=["txid", "subtype", "aclass", "wallet", "balance"])

    # Find refid's with target asset
    refids = set(df[df["asset"] == asset]["refid"].dropna().unique())

    # Bring all rows with same refid
    related = df[df["refid"].isin(refids)].copy()

    # Order by time
    related = related.sort_values("time")

    print(related)

    return related


def build_clean_events(df: pd.DataFrame) -> pd.DataFrame:

    rows = []
    processed = set()

    for _, row in df.iterrows():

        refid = row["refid"]
        t = row["type"]

        # -------------------------------------------------
        # 1. WITHDRAWAL
        # -------------------------------------------------
        if t == "withdrawal":
            rows.append({
                "refid": refid,
                "time": row["time"],
                "type": "withdrawal",
                "asset": row["asset"],
                "vol": abs(row["amount"]),
                "net_amount": None,
                "currency": ""
            })
            continue

        # -------------------------------------------------
        # 2. STAKING / EARN
        # -------------------------------------------------
        if t in {"staking", "earn"}:
            rows.append({
                "refid": refid,
                "time": row["time"],
                "type": "income",
                "asset": row["asset"],
                "vol": abs(row["amount"]),
                "net_amount": None,
                "currency": ""
            })
            continue

        # -------------------------------------------------
        # 3. TRADE (consolidado por refid)
        # -------------------------------------------------
        if t == "trade":

            if refid in processed:
                continue

            group = df[df["refid"] == refid]

            fiat = group[group["subclass"] == "fiat"]
            crypto = group[group["subclass"] == "crypto"]

            if fiat.empty or crypto.empty:
                continue

            fiat_row = fiat.iloc[0]
            crypto_row = crypto.iloc[0]

            # vol siempre positivo
            vol = abs(crypto_row["amount"])

            trade_type: str = ""
            net_amount: float = abs(fiat_row["amount"])

            if fiat_row["amount"] < 0:
                trade_type = "buy"
                net_amount += fiat_row["fee"]
            else:
                trade_type = "sell"
                net_amount -= fiat_row["fee"]

            rows.append({
                "refid": refid,
                "time": fiat_row["time"],
                "type": trade_type,
                "asset": crypto_row["asset"],
                "vol": vol,
                "net_amount": net_amount,
                "currency": fiat_row["asset"]
            })

            processed.add(refid)

    ret: pd.DataFrame = pd.DataFrame(rows)
    ret = ret.drop(columns=["refid"])
    
    return ret


def add_fx_conversion(df: pd.DataFrame, target_currency: str) -> pd.DataFrame:

    rows = []

    for _, row in df.iterrows():

        t = row["type"]
        time = row["time"]
        asset = row["asset"]
        vol = row["vol"]
        net_amount = row["net_amount"]
        currency = row["currency"]

        new_row = row.to_dict()

        # -------------------------------------------------
        # 1. TRADE (buy/sell)
        # -------------------------------------------------
        if t in {"buy", "sell"}:
            if currency != target_currency:
                fx = get_fx_rate(currency, target_currency, time)
                new_row["net_amount"] = net_amount * fx
            else:
                new_row["net_amount"] = net_amount

        # -------------------------------------------------
        # 2. STAKING / EARN
        # -------------------------------------------------
        elif t == "income":

            fx = get_fx_rate(asset, target_currency, time)
            new_row["net_amount"] = vol * fx

        # -------------------------------------------------
        # 3. WITHDRAWAL
        # -------------------------------------------------
        elif t == "withdrawal":
            pass  # no changes

        new_row["currency"] = target_currency
        new_row["real_unit_value"] = new_row["net_amount"] / new_row["vol"]

        rows.append(new_row)

    return pd.DataFrame(rows)


def get_asset_yearly_pnl(input_csv_path: str, asset: str, target_cur: str, year: int, output_csv_path: str) -> int:
    _dlog.log_inf(f"Computing yearly PnL")
    _dlog.log_inf(f"Input CSV: {input_csv_path}")
    _dlog.log_inf(f"Asset: {asset}")
    _dlog.log_inf(f"Currency: {target_cur}")
    _dlog.log_inf(f"Year: {year}")
    _dlog.log_inf(f"Output CSV: {output_csv_path or 'none'}")
    
    raw_df: pd.DataFrame = utils_csv.get_df_from_csv(input_csv_path)
    # print(sorted(raw_df["type"].unique()))
    
    asset_df: pd.DataFrame = extract_asset_events(raw_df, asset)
    utils_csv.write_df_to_csv(asset_df, "asset.csv")
    
    clean_df: pd.DataFrame = build_clean_events(asset_df)
    utils_csv.write_df_to_csv(clean_df, "clean.csv")

    converted_df: pd.DataFrame = add_fx_conversion(clean_df, target_cur)
    utils_csv.write_df_to_csv(converted_df, "converted.csv")
    return 0

    asset_data_df: pd.DataFrame     = gen_data(test_df)
    fifo_data_df: pd.DataFrame      = compute_fifo(asset_data_df, target_cur)
    
    if len(output_csv_path) > 0:
        utils_csv.write_df_to_csv(fifo_data_df, output_csv_path)

    pnl_asset_year: float = get_asset_yearly_pnl_from_df(fifo_data_df, int(year))
    
    return pnl_asset_year


def main() -> None:
    args = parse_args()
    _dlog.set_log_level(DEBUG if args.verbose == True else INFO)
    pnl_asset_year: float = 0.0

    pnl_asset_year = get_asset_yearly_pnl(args.input, args.asset, args.currency, args.year, args.output)

    # try:
    #   pnl_asset_year = get_asset_yearly_pnl(args.input, args.asset, args.currency, args.year, args.output)
    # except Exception as ex:
    #     _dlog.log_err(f"{ex}")
    # finally:
    #     _dlog.log_inf(f"PnL for {args.asset} in {args.year} (as {args.currency}): {pnl_asset_year}")

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
