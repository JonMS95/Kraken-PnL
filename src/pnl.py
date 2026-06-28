import pandas as pd
from utils_log import DataLogger
from utils_csv import get_df_from_csv, write_df_to_csv
from utils_fx import init_fx_cache, save_fx_cache
from extract_asset_data import clean_asset_data, clean_asset_data_from_trades
from gen_columns import gen_data, gen_data_from_trades
from apply_fifo import compute_fifo, compute_fifo_from_trades


_dlog : DataLogger = DataLogger()


def calc_pnl_from_df(df: pd.DataFrame, year: int) -> float:
    df["time"] = pd.to_datetime(df["time"])
    return df.loc[df["time"].dt.year == year, "pnl"].sum()


def get_pnl_df(df: pd.DataFrame, asset: str, target_cur: str, target_year: int, fx_cache_path: str, debug_dir: str) -> pd.DataFrame:
    gen_debug_files: bool = True if len(debug_dir) else False
    
    df = clean_asset_data(df, asset, target_year)
    if gen_debug_files:
        write_df_to_csv(df, debug_dir + "/clean_asset_data.csv")

    df = gen_data(df, target_cur, fx_cache_path)
    if gen_debug_files:
        write_df_to_csv(df, debug_dir + "/gen_data.csv")

    df = compute_fifo(df)
    if gen_debug_files:
        write_df_to_csv(df, debug_dir + "/compute_fifo.csv")
    
    return df


def get_pnl_df_from_trades(df: pd.DataFrame, asset: str, target_cur: str, fx_cache_path: str, debug_dir: str) -> pd.DataFrame:
    gen_debug_files: bool = True if len(debug_dir) else False
    
    df = clean_asset_data_from_trades(df, asset)
    if gen_debug_files:
        write_df_to_csv(df, debug_dir + "/clean_asset_data_from_trades.csv")

    df = gen_data_from_trades(df)
    if gen_debug_files:
        write_df_to_csv(df, debug_dir + "/gen_data_from_trades.csv")

    df = compute_fifo_from_trades(df, target_cur, fx_cache_path)
    if gen_debug_files:
        write_df_to_csv(df, debug_dir + "/compute_fifo_from_trades.csv")

    return df


def get_pnl(input_csv_path: str, asset: str, target_cur: str, year: int, output_csv_path: str, fx_cache_path: str, use_trades: bool, debug_dir: str) -> int:
    _dlog.log_dbg(f"Computing PnL")

    init_fx_cache(fx_cache_path)

    df: pd.DataFrame = get_df_from_csv(input_csv_path)

    if use_trades:
        df = get_pnl_df_from_trades(df, asset, target_cur, fx_cache_path, debug_dir)
    else:
        df = get_pnl_df(df, asset, target_cur, year, fx_cache_path, debug_dir)

    if len(output_csv_path) > 0:
        write_df_to_csv(df, output_csv_path)
    
    save_fx_cache(fx_cache_path)

    return calc_pnl_from_df(df, int(year))
