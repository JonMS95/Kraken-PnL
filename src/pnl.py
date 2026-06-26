import pandas as pd
from utils_log import DataLogger
from utils_csv import get_df_from_csv, write_df_to_csv
from extract_asset_data import clean_asset_data, clean_asset_data_from_trades
from gen_columns import gen_data, gen_data_from_trades
from apply_fifo import compute_fifo, compute_fifo_from_trades


_dlog : DataLogger = DataLogger()


def calc_pnl_from_df(df: pd.DataFrame, year: int) -> float:
    df["time"] = pd.to_datetime(df["time"])
    return df.loc[df["time"].dt.year == year, "pnl"].sum()


def get_pnl_df(df: pd.DataFrame, asset: str, target_cur: str, fx_cache_path: str) -> pd.DataFrame:
    df = clean_asset_data(df, asset)
    df = gen_data(df, target_cur, fx_cache_path)
    df = compute_fifo(df)
    
    return df


def get_pnl_df_from_trades(df: pd.DataFrame, asset: str, target_cur: str, fx_cache_path: str) -> pd.DataFrame:
    df = clean_asset_data_from_trades(df, asset)
    df = gen_data_from_trades(df)
    df = compute_fifo_from_trades(df, target_cur, fx_cache_path)
    
    return df


def get_pnl(input_csv_path: str, asset: str, target_cur: str, year: int, output_csv_path: str, fx_cache_path: str, use_trades: bool) -> int:
    _dlog.log_dbg(f"Computing PnL")
    
    df: pd.DataFrame = get_df_from_csv(input_csv_path)

    if use_trades:
        df = get_pnl_df_from_trades(df, asset, target_cur, fx_cache_path)
    else:
        df = get_pnl_df(df, asset, target_cur, fx_cache_path)

    if len(output_csv_path) > 0:
        write_df_to_csv(df, output_csv_path)
    
    return calc_pnl_from_df(df, int(year))