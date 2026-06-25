# Kraken PnL Calculator

Tool to compute Profit & Loss (PnL) from Kraken spot trades using FIFO accounting, including historical FX conversion to a target currency.

---

## Features

- FIFO-based PnL calculation for crypto trades
- Multi-pair support (BTC/EUR, BTC/USD, etc.)
- Asset-level filtering (e.g. BTC across multiple pairs)
- Historical FX conversion using Kraken OHLC data
- Multi-currency support with explicit target currency
- Year-based filtering for PnL reporting
- Fee-aware cost basis calculation
- Verbose logging mode for debugging pipeline steps

---

## Project Structure
 - src/
 - main.py: Entry point (CLI orchestration)
 - apply_fifo.py: FIFO accounting logic
 - extract_asset_data.py: Asset data retrieval
 - gen_columns.py: Feature engineering / enrichment
 - utils_csv.py: CSV <-> DataFrame utilities
 - utils_fx.py: FX rate retrieval (Kraken OHLC)

---

## Usage

Run the script via CLI:

```bash
python3 src/main.py -i <input_csv> -o <output_csv> -a <asset> -c <currency> -y <year> -v
