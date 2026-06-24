import pandas as pd
from collections import deque

'''
Add an additional input parameter here, such as target_currency (EUR).
Also, do the following when "muhney" != target_currency: convert to target_currency using (mult by) get_fx_rate(muhney, target_currency, row_timestamp)
If buying, then simply do it and add it. If selling, it's yet to be decided what to do although it does not affect our current trades.
'''
def compute_fifo(df: pd.DataFrame) -> pd.DataFrame:

    fifo = deque()
    results = []

    for _, row in df.iterrows():

        tx_type = row["type"].strip().lower()
        print(f"row_num: {_}, asset: {row['pair'].split('/')[0]}, muhney: {row['pair'].split('/')[1]}")
        continue
        # BUY → add lot
        if tx_type == "buy":
            fifo.append({
                "remaining_vol": row["vol"],
                "unit_cost": row["real_unit_price"]
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
            pnl = revenue - fifo_cost

            results.append({
                "time": row["time"],
                "sold_vol": row["vol"],
                "revenue": revenue,
                "fifo_cost": fifo_cost,
                "pnl": pnl
            })

            continue

        raise ValueError(f"Unsupported type: {row['type']}")

    return pd.DataFrame(results)
