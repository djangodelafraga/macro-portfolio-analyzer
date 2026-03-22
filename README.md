# macro-portfolio-analyzer

A simple Python project for downloading macro market proxy data, running portfolio optimization, and generating portfolio charts.

## Overview

This project does two things:

1. Downloads macro ETF/index proxy data and stores it as CSV files.
2. Runs a portfolio analysis on those assets and creates charts.

The analysis is performed on **returns**, not on raw price levels.

## Project files

- `get_macro_index.py` — downloads and updates market data
- `analyze_portfolio.py` — runs the portfolio analysis and creates charts
- `config.toml` — configuration file for analysis settings
- `requirements.txt` — required Python packages

## Output

Running the analysis can create the following files:

- `1_backtest.png` — cumulative portfolio performance
- `2_weights.png` — portfolio allocation weights
- `3_risk.png` — risk contribution chart
- `4_asset_risk_reward.png` — asset risk vs reward scatter plot

## Requirements

You need:

- Python 3.10 or newer
- Internet connection
- Terminal / Command Prompt / PowerShell
- The project files in one folder

## Installation

Open Command Prompt or PowerShell in the project folder.
```text
cd C:\path\to\your\project

Create a virtual environment:
```text
python -m venv .venv

Activate it in Command Prompt:
```text
.venv\Scripts\activate

Install dependencies:
```text
python -m pip install -r requirements.txt


Configuration
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

Step 1: Download market data
Before running the analysis, download the CSV files.

```text
python get_macro_index.py

This creates data files inside: "candles/macro/"

Step 2: Run the analysis
After the data has been downloaded:

```text
python analyze_portfolio.py

The script will:
    load the downloaded CSV files
    resample prices to daily or weekly data
    convert prices into returns
    optimize the portfolio
    generate charts

Typical workflow

```text
cd C:\path\to\your\project
.venv\Scripts\activate
python get_macro_index.py
python analyze_portfolio.py

Notes
    Running the scripts again updates the data and overwrite existing chart files.
    The portfolio analysis uses returns, not absolute prices.
    If image export fails, reinstall the packages from requirements.txt.

Disclaimer
This project is for research and educational use only. It is not financial advice.
