import pandas as pd
from collections import deque
from utils_fx import init_fx_cache, get_fx_rate, save_fx_cache
from utils_log import DataLogger


_dlog : DataLogger = DataLogger()


def compute_fifo(df: pd.DataFrame) -> pd.DataFrame:

    # -------------------------------------------------
    # 0. Orden temporal (NO asumir input ordenado)
    # -------------------------------------------------
    df = df.sort_values("time").reset_index(drop=True)

    # -------------------------------------------------
    # 1. Validación de asset único
    # -------------------------------------------------
    assets = df["asset"].unique()
    if len(assets) != 1:
        raise ValueError(f"Se esperaba un único asset, encontrados: {assets}")

    asset = assets[0]

    # -------------------------------------------------
    # 2. FIFO structure
    # -------------------------------------------------
    fifo = deque()

    results = []

    # -------------------------------------------------
    # 3. Iteración principal
    # -------------------------------------------------
    for _, row in df.iterrows():

        t = row["type"]

        # =================================================
        # BUY → añade lote a FIFO
        # =================================================
        if t == "buy":

            fifo.append({
                "remaining_vol": row["vol"],
                "unit_cost": row["real_unit_value"]
            })

            continue

        # =================================================
        # SELL → consume FIFO
        # =================================================
        if t == "sell":

            sell_vol = row["vol"]
            fifo_cost = 0.0

            while sell_vol > 0:

                if not fifo:
                    raise RuntimeError(
                        f"FIFO vacío vendiendo {asset} en {row['time']}"
                    )

                lot = fifo[0]

                consumed = min(sell_vol, lot["remaining_vol"])

                sell_vol -= consumed
                lot["remaining_vol"] -= consumed

                fifo_cost += consumed * lot["unit_cost"]

                if lot["remaining_vol"] == 0:
                    fifo.popleft()

            revenue = row["net_amount"]
            pnl = revenue - fifo_cost

            results.append({
                "time": row["time"],
                "asset": asset,
                "vol": row["vol"],
                "revenue": revenue,
                "fifo_cost": fifo_cost,
                "pnl": pnl
            })

            continue

        # =================================================
        # otros tipos (por ahora ignorados)
        # =================================================
        continue

    return pd.DataFrame(results)


def compute_fifo_from_trades(df: pd.DataFrame, target_currency: str, fx_cache_path: str) -> pd.DataFrame:

    fifo = deque()
    results = []
    payment_currency = ""
    unit_cost = 0.0
    asset = df["pair"].iloc[0].split("/")[0]

    init_fx_cache(fx_cache_path)

    _dlog.log_inf(f"Computing FIFO: asset: {asset}, currency: {target_currency}")

    for _, row in df.iterrows():
        tx_type = row["type"].strip().lower()
        payment_currency = row['pair'].split('/')[1]
        
        # BUY → add lot
        if tx_type == "buy":
            unit_cost = row["real_unit_price"]
            
            _dlog.log_dbg(f"Buy op: asset: {asset}, vol: {row['vol']}, cur: {payment_currency}, net_amount: {row['net_amount']}, date: {row['time']}")

            if payment_currency != target_currency:
                old_unit_cost: float = unit_cost
                unit_cost *= get_fx_rate(payment_currency, target_currency, row["time"])
                _dlog.log_dbg(f"Non-target currency-based payment op spotted: unit_cost: {old_unit_cost} -> {unit_cost}")

            fifo.append({
                "remaining_vol": row["vol"],
                "unit_cost": unit_cost
            })
            
            continue

        # SELL → consume FIFO
        if tx_type == "sell":
            remaining = row["vol"]
            fifo_cost = 0.0

            _dlog.log_dbg(f"Sell op: asset: {asset}, vol: {row['vol']}, cur: {payment_currency}, net_amount: {row['net_amount']}, date: {row['time']}")

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
                old_revenue: float = revenue
                revenue *= get_fx_rate(payment_currency, target_currency, row["time"])
                _dlog.log_dbg(f"Non-target currency-based payment op spotted: unit_cost: {old_revenue} -> {revenue}")

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
    
    save_fx_cache(fx_cache_path)

    return pd.DataFrame(results)
