import requests
from datetime import datetime
from typing import Union
import pandas as pd
import time
from pathlib import Path
from utils_log import DataLogger


_fx_cache_df: pd.DataFrame = None
_dlog : DataLogger = DataLogger()
_asset_normalizer: dict[str, str] = {
    "BTC"   : "XBT",
    "DOGE"  : "XDG",
}


# ---------------------------------------------------------
# 0. Time conversion
# ---------------------------------------------------------
def init_fx_cache(path: str):
    global _fx_cache_df

    try:
        _fx_cache_df = pd.read_csv(path)
    except FileNotFoundError:
        _fx_cache_df = pd.DataFrame(columns=[
            "base", "quote", "timestamp", "fx"
        ])


# ---------------------------------------------------------
# 1. Time conversion
# ---------------------------------------------------------
def human_to_unix(time_str: str) -> int:
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(time_str, fmt)
            return int(dt.timestamp())
        except ValueError:
            pass

    raise ValueError(f"Unrecognized datetime format: {time_str}")


# ---------------------------------------------------------
# 2. Load Kraken asset pairs once (IMPORTANT)
# ---------------------------------------------------------
def load_kraken_pairs():
    url = "https://api.kraken.com/0/public/AssetPairs"
    r = requests.get(url).json()

    if r.get("error"):
        raise Exception(r["error"])

    return r["result"]


# ---------------------------------------------------------
# 3. Resolve pair with fallback logic
# ---------------------------------------------------------
def resolve_pair(base: str, quote: str, pairs_db: dict):
    """
    Returns:
        (kraken_pair, inverted: bool)

    Logic:
        1. base+quote
        2. quote+base
        3. None
    """

    direct = base + quote
    inverse = quote + base

    for k, v in pairs_db.items():
        alt = v.get("altname")

        if alt == direct:
            return k, False

        if alt == inverse:
            return k, True

    return None, None


# ---------------------------------------------------------
# 4. Fetch trades
# ---------------------------------------------------------
def fetch_trades(pair: str, timestamp: int):
    url = "https://api.kraken.com/0/public/Trades"

    since = timestamp - 60 * 60 * 24
    all_trades = []

    while True:
        params = {"pair": pair, "since": since}
        r = requests.get(url, params=params).json()

        if r.get("error"):
            raise Exception(r["error"])

        result = r["result"]

        pair_key = [k for k in result.keys() if k != "last"][0]
        trades = result[pair_key]

        if not trades:
            break

        all_trades.extend(trades)

        new_since = int(result["last"])

        if new_since <= since:
            break

        since = new_since

        if since > timestamp + 60 * 60 * 24:
            break

    return all_trades


# ---------------------------------------------------------
# 5. Find closest trade before timestamp
# ---------------------------------------------------------
def find_trade(trades, timestamp):
    best = None
    best_diff = float("inf")

    for t in trades:
        t_time = float(t[2])

        if t_time <= timestamp:
            diff = timestamp - t_time

            if diff < best_diff:
                best_diff = diff
                best = t

    return best


# ---------------------------------------------------------
# 6. Get timestamp from either integer or string
# ---------------------------------------------------------
def normalize_timestamp(timestamp: Union[int, str]) -> int:
    """
    Accepts:
    - int → returns as-is
    - str → converts to unix timestamp
    """
    if isinstance(timestamp, int):
        return timestamp

    if isinstance(timestamp, str):
        return human_to_unix(timestamp)

    raise TypeError("timestamp must be int or str")


# ---------------------------------------------------------
# 7. MAIN FX function
# ---------------------------------------------------------
def get_fx_rate(base: str, quote: str, timestamp: Union[int, str]) -> float:
    unix_time: int = normalize_timestamp(timestamp)
    
    query_base: str = base
    query_quote: str = quote

    if base in _asset_normalizer.keys():
        query_base = _asset_normalizer[base]
    
    if quote in _asset_normalizer.keys():
        query_quote = _asset_normalizer[quote]

    # Try to retrieve a match from fx cache first
    match = _fx_cache_df[
        (_fx_cache_df["base"] == query_base) &
        (_fx_cache_df["quote"] == query_quote) &
        (_fx_cache_df["timestamp"] == unix_time)
    ]

    # If a match was found, then return it immediately
    if not match.empty:
        return float(match.iloc[0]["fx"])
    
    pairs_db = load_kraken_pairs()

    pair, inverted = resolve_pair(query_base, query_quote, pairs_db)

    if not pair:
        raise Exception(f"No valid Kraken pair for {base} → {quote}")

    retry_sleep_time = 2

    while True:
        try:
            trades = fetch_trades(pair, unix_time)
            break
        except Exception as e:
            if "Too many requests" in str(e):
                time.sleep(retry_sleep_time)
                retry_sleep_time *= 2 # Exponentially increment sleep time
                continue
            raise

    trade = find_trade(trades, unix_time)

    if not trade:
        return None

    price = float(trade[0])

    if inverted:
        price = 1 / price

    append_fx_cache(base, quote, unix_time, price)

    _dlog.log_dbg(f"Added FX: base: {base}, quote: {quote}, time: {timestamp}, price: {price}")

    return price


# ---------------------------------------------------------
# 9. Add register to FX cache
# ---------------------------------------------------------
def append_fx_cache(base: str, quote: str, timestamp, fx: float):
    global _fx_cache_df

    new_row = {
        "base": base,
        "quote": quote,
        "timestamp": timestamp,
        "fx": fx
    }

    _fx_cache_df.loc[len(_fx_cache_df)] = new_row


# ---------------------------------------------------------
# 10. Save FX chache
# ---------------------------------------------------------
def save_fx_cache(path: str):
    """
    Persists the in-memory FX cache DataFrame to disk.
    Overwrites the previous cache file.
    """
    global _fx_cache_df

    if _fx_cache_df is None:
        return

    # Create conatiner directory in case it doesn't exist beforehand 
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    _fx_cache_df.to_csv(path, index=False)


# ---------------------------------------------------------
# 12. MAIN TEST
# ---------------------------------------------------------
def main():
    print("=== Kraken FX Engine ===")

    ts: str = "2022-10-08 16:31:23.2879"

    print(f"\nTime: {ts}")

    base = "USD"
    quote = "EUR"

    print(f"\nQuerying {base} → {quote}")

    fx_cache_path: str = "cache/test_utils_fx.csv"

    init_fx_cache(fx_cache_path)
    result = get_fx_rate(base, quote, ts)
    save_fx_cache(fx_cache_path)

    print("\nResult:")
    print(result)


if __name__ == "__main__":
    main()