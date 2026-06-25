import pandas as pd


def get_df_from_csv(input_file: str) -> pd.DataFrame:
    try:
        df: pd.DataFrame = pd.read_csv(input_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not fine input file: {input_file}")
    except Exception as e:
        raise RuntimeError(f"An error occurred while reading CSV file: {e}")
    
    return df


def write_df_to_csv(df: pd.DataFrame, output_file: str) -> None:
    try:
        df.to_csv(output_file, index=False)
        print(f"Clean CSV was properly generated: {output_file}")

    except Exception as e:
        raise RuntimeError(f"Error processing CSV file: {e}")
