"""
Batch backtesting — directory scanning mode.

Automatically discovers and backtests ALL portfolio files
(CSV/Excel) found in the given directory. Date ranges are auto-derived
from each portfolio's rebalance dates.

Run from the project root:
    python backtest_use_cases/batch_directory_scan.py
"""
import logging

from kaxanuk.backtest_engine.backtest.orchestrators import backtest_results_summary
from kaxanuk.backtest_engine.backtest.orchestrators.multi_portfolio_runner import MultiPortfolioBacktester
from kaxanuk.backtest_engine.config_handlers.multi_backtest_parser import BatchConfigParser
from kaxanuk.backtest_engine.exceptions import NoPortfoliosDiscoveredError
from kaxanuk.backtest_engine.input_handlers.csv_input import CsvInput
from kaxanuk.backtest_engine.input_handlers.csv_portfolio_input_handler import CsvPortfolioInputHandler
from kaxanuk.backtest_engine.services.config_logger import configure_logger
from kaxanuk.backtest_engine.services.env_loader import load_config_env

# --- Paths (relative to repo root) ----------------------------------------
INPUT_MARKET_DATA_DIR = "./Input/Data"
INPUT_PORTFOLIOS_DIR = "./Input/Portfolios"
OUTPUT_DIR = "./Output/batch_directory_scan"

# --- Backtest parameters --------------------------------------------------
BENCHMARK_FILE_NAME = "SPY"
COMMISSION_CENTS = 0.01
CASH_RESERVE_PERCENTAGE = 0.05
INITIAL_CAPITAL = 100000
USER_COLUMN_COMMISSION_PRICE = "c_vwap"
USER_COLUMN_TRADE_EXECUTION_PRICE = "c_vwap_dividend_and_split_adjusted"
USER_COLUMN_MARK_TO_MARKET_PRICE = "m_close_dividend_and_split_adjusted"
USER_COLUMN_DATE = "m_date"
MARKET_DATA_INPUT_FORMAT = "csv"
PORTFOLIO_INPUT_FORMAT = "csv"

# --- Output ---------------------------------------------------------------
BATCH_NAME = "directory_scan"
RANKING_METRIC = "sharpe_ratio"

#%%

configure_logger(
    logger_name="kaxanuk.backtest_engine",
    logger_level=logging.INFO,
    logger_format="%(levelname)s | %(message)s",
    logger_file=None,
)

load_config_env()

#%%

batch_config = BatchConfigParser.parse_dict({
    "global_defaults": {
        "start_date": "auto",
        "end_date": "auto",
        "benchmark_file_name": BENCHMARK_FILE_NAME,
        "commission_cents": COMMISSION_CENTS,
        "cash_reserve_percentage": CASH_RESERVE_PERCENTAGE,
        "initial_capital": INITIAL_CAPITAL,
        # "execution_price": USER_COLUMN_TRADE_EXECUTION_PRICE,
        "market_data_input_format": MARKET_DATA_INPUT_FORMAT,
        "portfolio_input_format": PORTFOLIO_INPUT_FORMAT,
        "input_market_data_directory": INPUT_MARKET_DATA_DIR,
        "input_portfolio_directory": INPUT_PORTFOLIOS_DIR,
        "backtest_results_output_directory": OUTPUT_DIR,
        "user_column_commission_price": USER_COLUMN_COMMISSION_PRICE,
        "user_column_trade_execution_price": USER_COLUMN_TRADE_EXECUTION_PRICE,
        "user_column_mark_to_market_price": USER_COLUMN_MARK_TO_MARKET_PRICE,
        "user_column_date": USER_COLUMN_DATE,
    },
    # All CSV/Excel files in this directory become portfolios automatically
    "portfolio_directory": INPUT_PORTFOLIOS_DIR,
    "output": {
        "directory": OUTPUT_DIR,
        "batch_name": BATCH_NAME,
        "ranking_metric": RANKING_METRIC,
    },
})

#%%

backtester = MultiPortfolioBacktester(
    input_handlers=[CsvInput(input_dir=INPUT_MARKET_DATA_DIR)],
    portfolio_handlers=[CsvPortfolioInputHandler(base_dir=INPUT_PORTFOLIOS_DIR)],
)

try:
    results = backtester.run(
        batch_config,
        progress_callback=lambda done, total, name: print(  # noqa: T201
            f"\n>>> [{done}/{total}] Completed: {name}\n"
        ),
    )
except NoPortfoliosDiscoveredError:
    results = None

#%%

if results is not None:
    # Print summary
    summary = backtest_results_summary.get_summary_dataframe(results=results)
    cols = [
        "name",
        "success",
        "sharpe_ratio",
        "annualized_return",
        "max_drawdown",
        "final_value",
    ]
    available_cols = [c for c in cols if c in summary.columns]

    # Generate comparative report
    report_path = backtester.generate_report(
        results=results,
        batch_config=batch_config,
    )

    # Generate individual Excel reports per portfolio
    individual_paths = backtester.generate_individual_reports(
        results=results,
        batch_config=batch_config,
    )
