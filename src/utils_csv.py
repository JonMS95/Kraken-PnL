import pandas as pd
from pathlib import Path


def get_df_from_csv(input_file: str) -> pd.DataFrame:
    try:
        df: pd.DataFrame = pd.read_csv(input_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find input file: {input_file}")
    except Exception as e:
        raise RuntimeError(f"An error occurred while reading CSV file: {e}")
    
    return df


def write_df_to_csv(df: pd.DataFrame, output_file: str) -> None:
    try:
        # Create conatiner directory in case it doesn't exist beforehand 
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
    except Exception as e:
        raise RuntimeError(f"Error processing CSV file: {e}")
