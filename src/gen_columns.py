import pandas as pd
import argparse
import os
from utils_log import DataLogger
from utils_fx import init_fx_cache, get_fx_rate, save_fx_cache


_dlog : DataLogger = DataLogger()


def gen_clean_events(df: pd.DataFrame) -> pd.DataFrame:

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
                "currency": "",
                "net_amount": None
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
                "currency": "",
                "net_amount": None
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
                "currency": fiat_row["asset"],
                "net_amount": net_amount
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
        new_row["currency"] = target_currency

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

        new_row["real_unit_value"] = new_row["net_amount"] / new_row["vol"]

        rows.append(new_row)

    return pd.DataFrame(rows)


def gen_data(df: pd.DataFrame, target_cur: str, fx_cache_path: str) -> pd.DataFrame:
    df = gen_clean_events(df)
    
    init_fx_cache(fx_cache_path)
    df = add_fx_conversion(df, target_cur)
    save_fx_cache(fx_cache_path)

    return df


def calculate_net_amount(row):
    tx_type = row["type"].strip().lower()

    if tx_type == "buy":
        return row["cost"] + row["fee"]

    if tx_type == "sell":
        return row["cost"] - row["fee"]

    raise ValueError(f"Unsupported type: {row['type']}")


def gen_data_from_trades(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches asset-level dataset (NOT pair-level).
    """

    _dlog.log_inf(f"Generating \'net_amount\' and \'real_unit_price\' columns")

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
