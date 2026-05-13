"""
Batch backtesting with portfolios defined inline.

Defines a handful of portfolios as Python dicts (no external files needed)
and runs them through `MultiPortfolioBacktester`. Useful as a self-contained
example of the batch workflow and for ad-hoc cost-sensitivity comparisons.

Run from the project root:
    python backtest_use_cases/batch_inline_portfolios.py
"""
import logging
from kaxanuk.backtest_engine.backtest.orchestrators.multi_portfolio_runner import MultiPortfolioBacktester
from kaxanuk.backtest_engine.config_handlers.multi_backtest_parser import BatchConfigParser
from kaxanuk.backtest_engine.input_handlers.csv_input import CsvInput
from kaxanuk.backtest_engine.input_handlers.csv_portfolio_input_handler import CsvPortfolioInputHandler
# from kaxanuk.backtest_engine.services.config_logger import configure_logger
from kaxanuk.backtest_engine.services.env_loader import load_config_env
from kaxanuk.backtest_engine.backtest.orchestrators.backtest_results_summary import (
    get_summary_dataframe,
)

# ---- Date range ----
START_DATE = "2020-01-02"
END_DATE = "2024-12-31"

# ---- Capital & costs ----
INITIAL_CAPITAL = 100000
COMMISSION_CENTS = 0.01
CASH_RESERVE_PERCENTAGE = 0.05

# ---- Benchmark & execution ----
BENCHMARK_FILE_NAME = "SPY"
EXECUTION_PRICE = "c_vwap_dividend_and_split_adjusted"

# ---- Input/Output paths (relative to repo root) ----
INPUT_MARKET_DATA_DIR = "./Input/Data"
INPUT_PORTFOLIO_DIR = "./Input/Portfolios"
OUTPUT_DIR = "./Output/batch_inline_portfolios"

# ---- Input formats ----
MARKET_DATA_INPUT_FORMAT = "csv"
PORTFOLIO_INPUT_FORMAT = "csv"

# ---- User column mappings ----
USER_COLUMN_COMMISSION_PRICE = "c_vwap"
USER_COLUMN_TRADE_EXECUTION_PRICE = "c_vwap_dividend_and_split_adjusted"
USER_COLUMN_MARK_TO_MARKET_PRICE = "m_close_dividend_and_split_adjusted"
USER_COLUMN_DATE = "m_date"

load_config_env()

#%%

batch_config = BatchConfigParser.parse_dict({
    "global_defaults": {
        "start_date": START_DATE,
        "end_date": END_DATE,
        "benchmark_file_name": BENCHMARK_FILE_NAME,
        "commission_cents": COMMISSION_CENTS,
        "cash_reserve_percentage": CASH_RESERVE_PERCENTAGE,
        "initial_capital": INITIAL_CAPITAL,
        "execution_price": EXECUTION_PRICE,
        "market_data_input_format": MARKET_DATA_INPUT_FORMAT,
        "portfolio_input_format": PORTFOLIO_INPUT_FORMAT,
        "input_market_data_directory": INPUT_MARKET_DATA_DIR,
        "input_portfolio_directory": INPUT_PORTFOLIO_DIR,
        "backtest_results_output_directory": OUTPUT_DIR,
        "user_column_commission_price": USER_COLUMN_COMMISSION_PRICE,
        "user_column_trade_execution_price": USER_COLUMN_TRADE_EXECUTION_PRICE,
        "user_column_mark_to_market_price": USER_COLUMN_MARK_TO_MARKET_PRICE,
        "user_column_date": USER_COLUMN_DATE,
    },
    "portfolios": [
        # Inline portfolio #1: AAPL + MSFT (needs 2+ rebalance dates)
        {
            "name": "aapl_msft_60_40",
            "inline_weights": {
                "2020-01-02": {"AAPL": 0.60, "MSFT": 0.40},
                "2022-01-03": {"AAPL": 0.55, "MSFT": 0.45},
            },
        },
        # Inline portfolio #2: NVDA heavy
        {
            "name": "nvda_heavy",
            "inline_weights": {
                "2020-01-02": {"NVDA": 0.50, "AAPL": 0.30, "MSFT": 0.20},
                "2022-01-03": {"NVDA": 0.40, "AAPL": 0.35, "MSFT": 0.25},
            },
        },
        # Inline portfolio #3 with variations (cost sensitivity)
        {
            "name": "googl_meta",
            "inline_weights": {
                "2020-01-02": {"GOOGL": 0.50, "META": 0.50},
                "2022-01-03": {"GOOGL": 0.60, "META": 0.40},
            },
            "variations": [
                {"name": "low_cost", "commission_cents": 0.005},
                {"name": "high_cost", "commission_cents": 0.05},
            ],
        },
    ],
    "output": {
        "directory": OUTPUT_DIR,
        "batch_name": "integration_test",
        "ranking_metric": "sharpe_ratio",
    },
})

backtester = MultiPortfolioBacktester(
    input_handlers=[CsvInput(input_dir=INPUT_MARKET_DATA_DIR)],
    portfolio_handlers=[CsvPortfolioInputHandler(base_dir=INPUT_PORTFOLIO_DIR)],
)

progress_logger = logging.getLogger("kaxanuk")

results = backtester.run(
    batch_config=batch_config,
    progress_callback=lambda done, total, name: progress_logger.info(">>> [%s/%s] Completed: %s", done, total, name),
)

# Print summary
summary = get_summary_dataframe(results=results)
cols = ["name", "success", "sharpe_ratio", "annualized_return", "max_drawdown", "final_value"]
available_cols = [c for c in cols if c in summary.columns]

# Generate comparative report
report_path = backtester.generate_report(results, batch_config)

# Generate individual Excel reports per portfolio
individual_paths = backtester.generate_individual_reports(results, batch_config)
