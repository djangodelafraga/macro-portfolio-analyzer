import os
import glob
import tomllib
import pandas as pd
import matplotlib.pyplot as plt
import json
from skfolio import Population
from skfolio.optimization import MeanRisk, ObjectiveFunction, EqualWeighted
from skfolio.measures import RiskMeasure
from skfolio.preprocessing import prices_to_returns

CONFIG_PATH = "config.toml"
DATA_PATH = "candles/macro/*.csv"
TICKERS_PATH = "tickers.json"


def load_config():
    with open(CONFIG_PATH, "rb") as f:
        config = tomllib.load(f)

    required_keys = [
        "analysis_frequency",
        "portfolio_goal",
        "risk_aversion",
        "min_weight",
        "max_weight",
        "use_all_assets",
        "include_assets",
        "exclude_assets",
        "train_size",
        "annualization_factor"
    ]

    missing = [k for k in required_keys if k not in config]
    if missing:
        raise ValueError(f"Missing config keys: {missing}")

    if config["analysis_frequency"] not in ["D", "W"]:
        raise ValueError("analysis_frequency must be 'D' or 'W'")

    if not (0 < config["train_size"] < 1):
        raise ValueError("train_size must be between 0 and 1")

    if not (0 <= config["min_weight"] <= 1):
        raise ValueError("min_weight must be between 0 and 1")

    if not (0 <= config["max_weight"] <= 1):
        raise ValueError("max_weight must be between 0 and 1")

    if config["min_weight"] > config["max_weight"]:
        raise ValueError("min_weight cannot be greater than max_weight")

    return config


def resolve_objective(goal):
    goal = goal.lower()

    mapping = {
        "max_sharpe": ObjectiveFunction.MAXIMIZE_RATIO,
        "max_ratio": ObjectiveFunction.MAXIMIZE_RATIO,
        "maximize_ratio": ObjectiveFunction.MAXIMIZE_RATIO,

        "min_risk": ObjectiveFunction.MINIMIZE_RISK,
        "minimize_risk": ObjectiveFunction.MINIMIZE_RISK,

        "max_return": ObjectiveFunction.MAXIMIZE_RETURN,
        "maximize_return": ObjectiveFunction.MAXIMIZE_RETURN,

        "max_utility": ObjectiveFunction.MAXIMIZE_UTILITY,
        "maximize_utility": ObjectiveFunction.MAXIMIZE_UTILITY,
    }

    if goal not in mapping:
        raise ValueError(f"Unsupported portfolio_goal: {goal}")

    return mapping[goal]

def resolve_risk_measure(name):
    name = name.lower()

    mapping = {
        "variance": RiskMeasure.VARIANCE,
        "standard_deviation": RiskMeasure.STANDARD_DEVIATION,
        "semi_variance": RiskMeasure.SEMI_VARIANCE,
        "annualized_variance": RiskMeasure.ANNUALIZED_VARIANCE,
    }

    if name not in mapping:
        raise ValueError(f"Unsupported risk_measure: {name}")

    return mapping[name]

def load_tickers() -> dict:
    if not os.path.exists(TICKERS_PATH):
        raise FileNotFoundError(f"{TICKERS_PATH} not found.")

    with open(TICKERS_PATH, "r") as f:
        tickers = json.load(f)

    if not isinstance(tickers, dict) or not tickers:
        raise ValueError("tickers.json must contain a non-empty dictionary.")

    return tickers


def load_resampled_data(config):
    frequency = config["analysis_frequency"]
    all_files = glob.glob(DATA_PATH)
    tickers = load_tickers()
    allowed_asset_names = set(tickers.values())

    if not all_files:
        print(f"Error: No CSV files found in {DATA_PATH}. Run get_macro_index.py first!")
        return pd.DataFrame()

    assets = []

    for filename in all_files:
        asset_name = os.path.basename(filename).replace("_1d.csv", "").replace(".csv", "")

        if asset_name not in allowed_asset_names:
            print(f"Skipping {filename}: not listed in tickers.json")
            continue

        df = pd.read_csv(filename)

        if "Datetime" not in df.columns or "Close" not in df.columns:
            print(f"Skipping {filename}: missing Datetime or Close column")
            continue

        df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True, errors="coerce")
        df = df.dropna(subset=["Datetime"])
        df = df.set_index("Datetime").sort_index()

        resampled = df["Close"].resample(frequency).last()
        resampled.name = asset_name
        assets.append(resampled)

    if not assets:
        print("Error: No valid asset series loaded.")
        return pd.DataFrame()

    master_prices = pd.concat(assets, axis=1).ffill().dropna()

    if not config.get("use_all_assets", True):
        include_assets = config.get("include_assets", [])
        master_prices = master_prices[[c for c in include_assets if c in master_prices.columns]]

    exclude_assets = set(config.get("exclude_assets", []))
    if exclude_assets:
        master_prices = master_prices[[c for c in master_prices.columns if c not in exclude_assets]]

    if master_prices.empty:
        print("Error: No assets left after include/exclude filtering.")
        return pd.DataFrame()

    print(f"✅ Loaded {len(master_prices.columns)} assets.")
    print(f"✅ Frequency: {frequency}")
    print(f"✅ Assets: {list(master_prices.columns)}")
    print(
        f"✅ Data Points: {len(master_prices)} "
        f"({master_prices.index.min().date()} to {master_prices.index.max().date()})"
    )

    return master_prices


def run_skfolio_analysis(prices_df, config):
    returns = prices_to_returns(prices_df)

    if returns.empty:
        print("Error: returns dataframe is empty.")
        return

    split_idx = int(len(returns) * config["train_size"])
    X_train = returns.iloc[:split_idx]
    X_test = returns.iloc[split_idx:]

    if X_train.empty or X_test.empty:
        print("Error: train/test split produced an empty set.")
        return

    objective = resolve_objective(config["portfolio_goal"])
    risk_measure = resolve_risk_measure(config["risk_measure"])

    model = MeanRisk(
        risk_measure=risk_measure,
        objective_function=objective,
        risk_aversion=config.get("risk_aversion", 1.0),
        min_weights=config["min_weight"],
        max_weights=config["max_weight"]
    )

    model.fit(X_train)
    portfolio_opt = model.predict(X_test)
    portfolio_opt.name = "Optimized"

    bench_model = EqualWeighted()
    bench_model.fit(X_train)
    portfolio_equal = bench_model.predict(X_test)
    portfolio_equal.name = "Benchmark (Equal)"

    population = Population([portfolio_opt, portfolio_equal])

    weights = pd.Series(model.weights_, index=X_train.columns).sort_values(ascending=False)

    print("\n" + "=" * 40)
    print(" SUGGESTED WEIGHTS")
    print("=" * 40)
    for asset, w in weights.items():
        print(f"{asset:18}: {w * 100:>6.2f}%")
    print("=" * 40)

    ann_factor = config["annualization_factor"].get(config["analysis_frequency"], 252)

    asset_stats = pd.DataFrame({
        "Return": X_train.mean() * ann_factor,
        "Risk": X_train.std() * (ann_factor ** 0.5),
        "Weight": pd.Series(model.weights_, index=X_train.columns)
    }).sort_values("Weight", ascending=False)

    print("\n🎨 Saving graphs...")
    try:
        population.plot_cumulative_returns().write_image("1_backtest.png")
        portfolio_opt.plot_composition().write_image("2_weights.png")
        portfolio_opt.plot_contribution(
            measure=RiskMeasure.ANNUALIZED_VARIANCE
        ).write_image("3_risk.png")

        plt.figure(figsize=(10, 7))
        plt.scatter(
            asset_stats["Risk"],
            asset_stats["Return"],
            s=80 + asset_stats["Weight"] * 1200,
            alpha=0.75
        )

        for asset, row in asset_stats.iterrows():
            plt.annotate(
                asset,
                (row["Risk"], row["Return"]),
                fontsize=6,
                xytext=(5, 5),
                textcoords="offset points"
            )

        # Suggested portfolio (optimized)
        port_ret = (X_train @ model.weights_).mean() * ann_factor
        port_risk = (X_train @ model.weights_).std() * (ann_factor ** 0.5)

        plt.scatter(
            port_risk,
            port_ret,
            s=180,
            c="red",
            marker="X",
            label="Optimized portfolio"
        )
        plt.annotate(
            "Portfolio",
            (port_risk, port_ret),
            fontsize=10,
            fontweight="bold",
            xytext=(6, -10),
            textcoords="offset points"
        )

        plt.xlabel("Annualized Risk (Volatility)")
        plt.ylabel("Annualized Return")
        plt.title("Asset Risk/Reward Scatter")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig("4_asset_risk_reward.png", dpi=200)
        plt.close()

        print("✨ DONE! Check:")
        print("  - 1_backtest.png")
        print("  - 2_weights.png")
        print("  - 3_risk.png")
        print("  - 4_asset_risk_reward.png")

    except Exception as e:
        print(f"❌ Image Error: {e}")


if __name__ == "__main__":
    config = load_config()
    prices = load_resampled_data(config)

    if not prices.empty:
        run_skfolio_analysis(prices, config)
