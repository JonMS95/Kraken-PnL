import requests
from datetime import datetime
from typing import Union


# ---------------------------------------------------------
# 1. Time conversion
# ---------------------------------------------------------
def human_to_unix(time_str: str) -> int:
    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
    return int(dt.timestamp())


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
# 7. MAIN FX function (THIS is what you wanted)
# ---------------------------------------------------------
def get_fx_rate(base: str, quote: str, timestamp: Union[int, str]) -> float:
    pairs_db = load_kraken_pairs()

    pair, inverted = resolve_pair(base, quote, pairs_db)

    if not pair:
        raise Exception(f"No valid Kraken pair for {base} → {quote}")

    timestamp = normalize_timestamp(timestamp)

    trades = fetch_trades(pair, timestamp)

    trade = find_trade(trades, timestamp)

    if not trade:
        return None

    price = float(trade[0])

    if inverted:
        price = 1 / price

    # return {
    #     "base": base,
    #     "quote": quote,
    #     "pair_used": pair,
    #     "inverted": inverted,
    #     "price": price,
    #     "timestamp": timestamp,
    #     "trade_timestamp": float(trade[2]),
    # }
    return price


# ---------------------------------------------------------
# 8. MAIN TEST
# ---------------------------------------------------------
def main():
    print("=== Kraken FX Engine ===")

    ts: str = "2022-10-08 16:31:23.2879"

    print(f"\nTime: {ts}")

    base = "USD"
    quote = "EUR"

    print(f"\nQuerying {base} → {quote}")

    result = get_fx_rate(base, quote, ts)

    print("\nResult:")
    print(result)


if __name__ == "__main__":
    main()