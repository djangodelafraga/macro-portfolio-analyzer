import os
import time
from datetime import timedelta

import pandas as pd
import yfinance as yf

# --- Configuration ---
# This ensures data is saved in your project folder under 'candles/macro'
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SRC_DIR, "candles", "macro")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Using tradeable ETF proxies for macro indices
MACRO_TICKERS = {
    "SPY": "S&P500",
    "QQQ": "NASDAQ",
    "IWM": "RUSSELL2000",
    "VGK": "EUROPE_STOCKS",
    "GLD": "GOLD",
    "TLT": "LONG_TREASURY",
    "UUP": "US_DOLLAR",
    "DBC": "COMMODITIES",
    "HYG": "HIGH_YIELD_BOND"
}

# Constants
INTERVAL = "1h"
PERIOD = "730d"  # Yahoo/yfinance hourly history is limited; keep as fallback
ROLLING_DAYS = 150  # Fetch a recent window each run, then merge/dedup locally
OVERLAP_HOURS = 6  # Re-fetch last few hours to handle revisions/partial candle
DELAY_SECONDS = 2

def csv_path(name: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, f"{name}_{INTERVAL}.csv")

def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    # yfinance can return MultiIndex columns; flatten to single level (OHLCV)
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [c[0] for c in df.columns]
    return df

def normalize_datetime_col(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # If datetime is in index, bring it out
    if not isinstance(df.index, pd.RangeIndex):
        df = df.reset_index()

    # Normalize possible names
    if "Datetime" in df.columns:
        dt_col = "Datetime"
    elif "Date" in df.columns:
        dt_col = "Date"
    elif "index" in df.columns:
        dt_col = "index"
    else:
        raise ValueError(f"Cannot find datetime column. Columns={list(df.columns)}")

    df = df.rename(columns={dt_col: "Datetime"})
    df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True, errors="coerce")
    df = df.dropna(subset=["Datetime"])
    return df

def load_existing(name: str) -> pd.DataFrame | None:
    path = csv_path(name)
    if not os.path.exists(path):
        return None

    # First attempt: normal read
    df = pd.read_csv(path)

    # Detect and remove the broken "ticker header row" like: ",A,A,A,A,A"
    if len(df) > 0 and "Datetime" in df.columns:
        first_dt = str(df.loc[0, "Datetime"]).strip()
        if first_dt in ("", "nan", "NaT"):
            df = pd.read_csv(path, skiprows=[1])

    df = normalize_datetime_col(df)
    
    # Ensure numeric columns are numeric
    for c in ["Open", "High", "Low", "Close", "Volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            
    df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
    df = df.sort_values("Datetime")
    return df

def download_yfinance(symbol: str, name: str, start=None, period=None) -> pd.DataFrame | None:
    print(f"📥 Downloading {name} ({symbol}) (Interval: {INTERVAL})...")

    df = yf.download(
        tickers=symbol,
        start=start,
        period=period,
        interval=INTERVAL,
        auto_adjust=True,
        progress=False,
    )

    if df is None or df.empty:
        return None

    df = flatten_columns(df)
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df = normalize_datetime_col(df)
                
    df = df.sort_values("Datetime")
    return df

def merge_dedup(old_df: pd.DataFrame | None, new_df: pd.DataFrame) -> pd.DataFrame:
    if old_df is None or old_df.empty:
        out = new_df.copy()
    else:
        out = pd.concat([old_df, new_df], ignore_index=True)

    out = out.sort_values("Datetime")
    out = out.drop_duplicates(subset=["Datetime"], keep="last")
    return out

def sync_symbol(symbol: str, name: str):
    old = load_existing(name)

    if old is None or old.empty:
        new = download_yfinance(symbol, name, period=PERIOD)
        if new is None or new.empty:
            print(f"[x] No data returned for {name}.")
            return
        out = new
    else:
        last_ts = old["Datetime"].max()
        start = (last_ts - timedelta(hours=OVERLAP_HOURS)).to_pydatetime()

        # Use start-based download first
        new = download_yfinance(symbol, name, start=start)
        if new is None or new.empty:
            # Fallback: rolling window if start-based returns empty
            new = download_yfinance(symbol, name, period=f"{ROLLING_DAYS}d")

        if new is None or new.empty:
            print(f"[x] No new data returned for {name}.")
            return

        out = merge_dedup(old, new)

    out.to_csv(csv_path(name), index=False)
    print(f"[✓] Synced & saved {name} -> {csv_path(name)} (rows={len(out)})")

if __name__ == "__main__":
    print(f"\n🚀 Starting sync for {len(MACRO_TICKERS)} macro indicators...")

    for i, (symbol, name) in enumerate(MACRO_TICKERS.items()):
        print(f"\n--- Processing {i+1}/{len(MACRO_TICKERS)}: {name} ({symbol}) ---")
        try:
            sync_symbol(symbol, name)
        except Exception as e:
            print(f"[!] {name} failed: {e}")
        
        time.sleep(DELAY_SECONDS)

    print("\n🎉 All macro syncs complete!")
