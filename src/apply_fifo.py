import pandas as pd
from collections import deque
from utils_fx import get_fx_rate
from utils_log import DataLogger


_dlog : DataLogger = DataLogger()


def compute_fifo(df: pd.DataFrame, target_currency: str) -> pd.DataFrame:

    fifo = deque()
    results = []
    payment_currency = ""
    unit_cost = 0.0
    asset = df["pair"].iloc[0].split("/")[0]

    _dlog.log_inf(f"Computing FIFO: asset: {asset}, currency: {target_currency}")

    for _, row in df.iterrows():
        tx_type = row["type"].strip().lower()
        payment_currency = row['pair'].split('/')[1]
        
        # BUY → add lot
        if tx_type == "buy":
            unit_cost = row["real_unit_price"]
            
            _dlog.log_dbg(f"Buy op: vol: {row['vol']}, cur: {payment_currency}, date: {row['time']}")

            if payment_currency != target_currency:
                old_unit_cost: float = unit_cost
                unit_cost *= get_fx_rate(payment_currency, target_currency, row["time"])
                _dlog.log_dbg(f"Non-target currency-based payment op spotted: vol: {row['vol']}, unit_cost: {old_unit_cost} -> {unit_cost}")

            fifo.append({
                "remaining_vol": row["vol"],
                "unit_cost": unit_cost
            })
            
            continue

        # SELL → consume FIFO
        if tx_type == "sell":
            remaining = row["vol"]
            fifo_cost = 0.0

            while remaining > 0:

                if not fifo:
                    raise ValueError("FIFO empty")

                lot = fifo[0]

                consumed = min(remaining, lot["remaining_vol"])

                fifo_cost += consumed * lot["unit_cost"]

                lot["remaining_vol"] -= consumed
                remaining -= consumed

                if lot["remaining_vol"] == 0:
                    fifo.popleft()

            revenue = row["net_amount"]
            
            if payment_currency != target_currency:
                revenue *= get_fx_rate(payment_currency, target_currency, row["time"])

            pnl = revenue - fifo_cost

            results.append({
                "time": row["time"],
                "asset": asset,
                "sold_vol": row["vol"],
                "base_currency": target_currency,
                "revenue": revenue,
                "fifo_cost": fifo_cost,
                "pnl": pnl
            })

            continue

        raise ValueError(f"Unsupported type: {row['type']}")

    return pd.DataFrame(results)
