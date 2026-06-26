import pandas as pd
from utils_log import DataLogger
from utils_fx import init_fx_cache, save_fx_cache
from utils_csv import get_df_from_csv, write_df_to_csv
from extract_asset_data import extract_asset_events
from gen_columns import gen_clean_events, add_fx_conversion
from apply_fifo import compute_fifo


_dlog : DataLogger = DataLogger()


def calc_pnl_from_df(df: pd.DataFrame, year: int) -> float:
    df["time"] = pd.to_datetime(df["time"])
    return df.loc[df["time"].dt.year == year, "pnl"].sum()


def get_pnl_df(df: pd.DataFrame, asset: str, target_cur: str, year: int, output_csv_path: str, fx_cache_path: str) -> pd.DataFrame:
    df = extract_asset_events(df, asset)    
    df = gen_clean_events(df)
    
    init_fx_cache(fx_cache_path)
    df = add_fx_conversion(df, target_cur)
    save_fx_cache(fx_cache_path)
    
    df = compute_fifo(df)
    
    return df


def get_pnl(input_csv_path: str, asset: str, target_cur: str, year: int, output_csv_path: str, fx_cache_path: str) -> int:
    _dlog.log_dbg(f"Computing PnL")
    
    df: pd.DataFrame = get_df_from_csv(input_csv_path)

    df = get_pnl_df(df, asset, target_cur, year, output_csv_path, fx_cache_path)

    if len(output_csv_path) > 0:
        write_df_to_csv(df, output_csv_path)
    
    return calc_pnl_from_df(df, int(year))