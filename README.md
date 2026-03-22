# Macro Portfolio Analyzer

Download macro ETF/index data, build a portfolio, and generate performance charts.

## Files

- `get_macro_index.py` — download/update market data
- `analyze_portfolio.py` — run portfolio analysis and save charts
- `config.toml` — analysis settings (frequency, goals, weights, assets)
- `tickers.json` — list of tickers and friendly names
- `requirements.txt` — Python dependencies
- `installation.py` — automated setup script (Windows)
- `install_and_run.bat` — one-click installer for Windows
- `run_analysis.bat` — one-click analysis for Windows

---

## Windows usage (for non-technical users)

### 1. Install Python

1. Download Python 3.10+ from:  
   https://www.python.org/downloads/
2. During install, check **“Add Python to PATH”**.

### 2. Install the app

1. Unzip the project folder (e.g. `macro-portfolio-analyzer`).
2. Open the folder.
3. Double‑click `install_and_run.bat`.
4. Wait until it finishes (it will:
   - create a virtual environment,
   - install dependencies,
   - run `get_macro_index.py` once).

### 3. Run the analysis

After installation:

1. Double‑click `run_analysis.bat`.
2. When it finishes, you should see:

   - `1_backtest.png`
   - `2_weights.png`
   - `3_risk.png`
   - `4_asset_risk_reward.png`

   in the project folder.

---

## Linux usage (for technical users)

    In a terminal, from the project folder:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    python3 -m pip install -r requirements.txt
    python3 get_macro_index.py
    python3 analyze_portfolio.py
    ---

## Configuration

Edit config.toml before running the analysis.
Main settings
    analysis_frequency
        "D" = daily
        "W" = weekly
    portfolio_goal
        "max_sharpe"
        "max_ratio"
        "min_risk"
        "max_return"
        "max_utility"
    risk_aversion
        used only for max_utility
    min_weight / max_weight
        minimum and maximum portfolio allocation per asset
    use_all_assets
        true = use all downloaded assets
        false = only use include_assets
    include_assets
        list of assets to include when use_all_assets = false
    exclude_assets
        list of assets to remove from the final analysis
    train_size
        fraction of the dataset used for training

## Notes
    Running the scripts again updates the data and overwrite existing chart files.
    The portfolio analysis uses returns, not absolute prices.
    If image export fails, reinstall the packages from requirements.txt.

## Disclaimer
    This project is for research and educational use only. It is not financial advice.