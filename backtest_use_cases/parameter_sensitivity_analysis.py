"""
Advanced Backtester Usage Examples

This module demonstrates advanced usage patterns for PyArrowBacktester,
including direct pipeline result usage, BacktestVariationRunner for multiple variations,
and comparative reporting.

Key patterns demonstrated:
- Using Configuration.with_overrides() for creating variations
- BacktestVariationRunner for efficient multi-backtest execution
- Comparative report generation for side-by-side analysis
"""

import datetime
import logging
from dataclasses import dataclass

from kaxanuk.backtest_engine.entities.configuration import Configuration
from kaxanuk.backtest_engine.input_handlers.input_handler_interface import (
    InputHandlerInterface,
)
from kaxanuk.backtest_engine.input_handlers.portfolio_input_handler_interface import (
    PortfolioInputHandlerInterface,
)

from kaxanuk.backtest_engine.config_handlers.excel_configurator import ExcelConfigurator
from kaxanuk.backtest_engine.data_processors.data_pipeline_executor import execute_data_pipeline
from kaxanuk.backtest_engine.backtest.orchestrators.backtest_results_summary import (
    get_summary_dataframe,
)
from kaxanuk.backtest_engine.input_handlers.csv_input import CsvInput
from kaxanuk.backtest_engine.input_handlers.parquet_input import ParquetInput
from kaxanuk.backtest_engine.input_handlers.excel_portfolio_input_handler import (
    ExcelPortfolioInputHandler
)
from kaxanuk.backtest_engine.input_handlers.csv_portfolio_input_handler import (
    CsvPortfolioInputHandler
)
from kaxanuk.backtest_engine.services.config_logger import configure_logger
from kaxanuk.backtest_engine.backtest import BacktestVariationRunner
from kaxanuk.backtest_engine.modules.comparative_report import (
    generate_comparative_excel_report
)
from kaxanuk.backtest_engine.exceptions import (
    DataPipelineError,
    ConfigurationError,
)
from kaxanuk.backtest_engine.services.env_loader import load_config_env

LOGGER_NAME = "myAppLogger"
LOGGER_LEVEL = logging.INFO
LOGGER_FORMAT = "[%(levelname)s] %(message)s"

logger = configure_logger(
    logger_name=LOGGER_NAME,
    logger_level=LOGGER_LEVEL,
    logger_format=LOGGER_FORMAT,
    logger_file=None
)

load_config_env()

#%%

# =============================================================================
# HELPER: Load configuration and create input handlers
# =============================================================================

@dataclass
class BacktestSetup:
    """
    Container for backtest configuration and input handlers.
    """

    configuration: Configuration
    market_data_handler: InputHandlerInterface
    portfolio_handler: PortfolioInputHandlerInterface


def _load_configuration_and_handlers() -> BacktestSetup:
    """
    Load configuration and create input handlers.

    Returns
    -------
    BacktestSetup
        Dataclass containing configuration and input handlers.
    """
    configurator = ExcelConfigurator(
        file_path='Config/backtest_engine_parameters.xlsx'
    )
    configuration = configurator.get_configuration()

    market_data_input_handlers = {
        'csv': CsvInput(
            input_dir=configuration.input_market_data_directory
        ),
        'parquet': ParquetInput(
            input_dir=configuration.input_market_data_directory
        ),
    }

    portfolio_input_handlers = {
        'csv': CsvPortfolioInputHandler(
            base_dir=configuration.input_portfolio_directory
        ),
        'excel': ExcelPortfolioInputHandler(
            base_dir=configuration.input_portfolio_directory
        )
    }

    market_data_handler = market_data_input_handlers[configuration.market_data_input_format]
    portfolio_handler = portfolio_input_handlers[configuration.portfolio_input_format]

    return BacktestSetup(
        configuration=configuration,
        market_data_handler=market_data_handler,
        portfolio_handler=portfolio_handler,
    )

#%%

# =============================================================================
# EXAMPLE 3: BacktestVariationRunner for efficient multi-backtest execution
# =============================================================================

def example_3_backtest_suite_commission_grid():
    """
    Example 3: Using BacktestVariationRunner for commission grid analysis.

    BacktestVariationRunner provides:
    - Named variations for easy identification
    - Automatic progress tracking
    - Structured results with summary DataFrame
    - Built-in helpers for common variation patterns
    - Generates comparative Excel report
    """
    try:
        setup = _load_configuration_and_handlers()
    except ConfigurationError as ex:
        logger.error("Configuration failed: %s", ex)
        return None

    try:
        logger.info("Executing data pipeline...")
        pipeline_result = execute_data_pipeline(
            configuration=setup.configuration,
            input_handlers=[setup.market_data_handler],
            portfolio_handlers=[setup.portfolio_handler]
        )
        logger.info("Data pipeline completed.\n")
    except DataPipelineError as ex:
        logger.error("Data pipeline failed: %s", ex)
        return None

    # Create BacktestVariationRunner
    suite = BacktestVariationRunner(
        base_config=setup.configuration,
        pipeline_result=pipeline_result,
    )

    # Add commission grid variations using helper method
    suite.add_commission_grid(
        commission_values=[0.0, 0.01, 0.02, 0.03, 0.05],
        name_prefix="commission",
    )

    # Run all backtests
    logger.info("Running %d backtest variations...", len(suite.variations))
    results = suite.run_all()

    # Get summary DataFrame
    summary_df = get_summary_dataframe(results)
    logger.info("\n=== Summary ===")
    logger.info("\n%s", summary_df[["name", "final_value", "sharpe_ratio", "annualized_return", "max_drawdown"]])

    # Generate comparative Excel report
    report_path = generate_comparative_excel_report(
        suite_results=results,
        output_directory=setup.configuration.backtest_results_output_directory,
        report_name="commission_grid_analysis",
        ranking_metric="sharpe_ratio",
    )
    logger.info("\nComparative Excel report saved to: %s", report_path)

    return results, report_path


# =============================================================================
# EXAMPLE 4: BacktestVariationRunner with multiple variation types
# =============================================================================

def example_4_backtest_suite_mixed_variations():
    """
    Example 4: BacktestVariationRunner with multiple variation types.

    Demonstrates combining different types of variations:
    - Commission variations
    - Cash reserve variations
    - Custom named variations
    """
    try:
        setup = _load_configuration_and_handlers()
    except ConfigurationError as ex:
        logger.error("Configuration failed: %s", ex)
        return None

    try:
        logger.info("Executing data pipeline...")
        pipeline_result = execute_data_pipeline(
            configuration=setup.configuration,
            input_handlers=[setup.market_data_handler],
            portfolio_handlers=[setup.portfolio_handler]
        )
        logger.info("Data pipeline completed.\n")
    except DataPipelineError as ex:
        logger.error("Data pipeline failed: %s", ex)
        return None

    # Create suite and add variations
    suite = BacktestVariationRunner(
        base_config=setup.configuration,
        pipeline_result=pipeline_result,
    )

    # Add individual variations with descriptive names
    suite.add_variation("baseline", commission_cents=0.01, cash_reserve_percentage=0.05)
    suite.add_variation("low_cost", commission_cents=0.005, cash_reserve_percentage=0.05)
    suite.add_variation("high_reserve", commission_cents=0.01, cash_reserve_percentage=0.15)
    suite.add_variation("aggressive", commission_cents=0.005, cash_reserve_percentage=0.02)

    # Progress callback for tracking
    def on_progress(done: int, total: int, name: str):
        logger.info("[%d/%d] Completed: %s", done, total, name)

    # Run with progress tracking
    results = suite.run_all(progress_callback=on_progress)

    # Analyze results
    summary = get_summary_dataframe(results)

    logger.info("\n=== Results Summary ===")
    for _, row in summary.iterrows():
        if row["success"]:
            logger.info(
                "%s: Final=%.2f, Sharpe=%.4f, Commissions=%.2f",
                row["name"],
                row["final_value"],
                row["sharpe_ratio"],
                row["total_commissions"],
            )

    return results


# =============================================================================
# EXAMPLE 5: Generate comparative Excel report
# =============================================================================

def example_5_comparative_report():
    """
    Example 5: Generate comparative Excel report from BacktestVariationRunner results.

    Produces an Excel file with:
    - Summary sheet comparing all backtests
    - Ranking sheet sorted by Sharpe ratio
    - Charts visualizing key metrics
    """
    try:
        setup = _load_configuration_and_handlers()
    except ConfigurationError as ex:
        logger.error("Configuration failed: %s", ex)
        return None

    try:
        logger.info("Executing data pipeline...")
        pipeline_result = execute_data_pipeline(
            configuration=setup.configuration,
            input_handlers=[setup.market_data_handler],
            portfolio_handlers=[setup.portfolio_handler]
        )
        logger.info("Data pipeline completed.\n")
    except DataPipelineError as ex:
        logger.error("Data pipeline failed: %s", ex)
        return None

    # Create suite with multiple variations
    suite = BacktestVariationRunner(
        base_config=setup.configuration,
        pipeline_result=pipeline_result,
    )

    suite.add_variation("baseline", commission_cents=0.01)
    suite.add_variation("low_cost", commission_cents=0.005)
    suite.add_variation("medium_cost", commission_cents=0.02)
    suite.add_variation("high_cost", commission_cents=0.03)
    suite.add_variation("high_reserve", commission_cents=0.01, cash_reserve_percentage=0.15)

    # Run all variations
    results = suite.run_all()

    # Generate comparative report
    report_path = generate_comparative_excel_report(
        suite_results=results,
        output_directory=setup.configuration.backtest_results_output_directory,
        report_name="commission_comparison",
        ranking_metric="sharpe_ratio",
    )

    logger.info("Comparative report generated: %s", report_path)

    return results, report_path


# =============================================================================
# EXAMPLE 6: Rolling window analysis with BacktestVariationRunner
# =============================================================================

def example_6_rolling_window_analysis():
    """
    Example 6: Rolling window analysis for robustness testing.

    Uses BacktestVariationRunner.add_rolling_window_variations() to create
    overlapping backtest windows for walk-forward analysis.
    """
    try:
        setup = _load_configuration_and_handlers()
    except ConfigurationError as ex:
        logger.error("Configuration failed: %s", ex)
        return None

    try:
        logger.info("Executing data pipeline...")
        pipeline_result = execute_data_pipeline(
            configuration=setup.configuration,
            input_handlers=[setup.market_data_handler],
            portfolio_handlers=[setup.portfolio_handler]
        )
        logger.info("Data pipeline completed.\n")
    except DataPipelineError as ex:
        logger.error("Data pipeline failed: %s", ex)
        return None

    # Create suite
    suite = BacktestVariationRunner(
        base_config=setup.configuration,
        pipeline_result=pipeline_result,
    )

    # Add rolling window variations (12-month windows, 6-month steps)
    # Note: Adjust dates based on your available data
    suite.add_rolling_window_variations(
        start_date=datetime.date(2020, 1, 2),
        end_date=datetime.date(2025, 12, 31),
        window_months=12,
        step_months=6,
        name_prefix="rolling",
    )

    logger.info("Created %d rolling window variations", len(suite.variations))

    # Run all
    results = suite.run_all()

    # Analyze consistency across windows
    summary = get_summary_dataframe(results)
    successful = summary[summary["success"] == True]  # noqa: E712

    if not successful.empty:
        logger.info("\n=== Rolling Window Analysis ===")
        logger.info("Windows analyzed: %d", len(successful))
        logger.info("Avg Sharpe: %.4f", successful["sharpe_ratio"].mean())
        logger.info("Sharpe Std Dev: %.4f", successful["sharpe_ratio"].std())
        logger.info("Min Sharpe: %.4f", successful["sharpe_ratio"].min())
        logger.info("Max Sharpe: %.4f", successful["sharpe_ratio"].max())

    # Generate report
    report_path = generate_comparative_excel_report(
        suite_results=results,
        output_directory=setup.configuration.backtest_results_output_directory,
        report_name="rolling_window_analysis",
        ranking_metric="sharpe_ratio",
    )

    logger.info("Rolling window report: %s", report_path)

    return results

# =============================================================================
# EXAMPLE 8: Different initial capital amounts
# =============================================================================

def example_8_initial_capital_variations():
    """
    Example 8: Test strategy scalability with different initial capital amounts.

    Demonstrates how transaction costs and market impact may affect
    performance at different portfolio sizes.
    """
    try:
        setup = _load_configuration_and_handlers()
    except ConfigurationError as ex:
        logger.error("Configuration failed: %s", ex)
        return None

    try:
        logger.info("Executing data pipeline...")
        pipeline_result = execute_data_pipeline(
            configuration=setup.configuration,
            input_handlers=[setup.market_data_handler],
            portfolio_handlers=[setup.portfolio_handler]
        )
        logger.info("Data pipeline completed.\n")
    except DataPipelineError as ex:
        logger.error("Data pipeline failed: %s", ex)
        return None

    # Create suite
    suite = BacktestVariationRunner(
        base_config=setup.configuration,
        pipeline_result=pipeline_result,
    )

    # Test different capital amounts
    capital_amounts = [
        ("small_10k", 10_000),
        ("medium_50k", 50_000),
        ("standard_100k", 100_000),
        ("large_500k", 500_000),
        ("xlarge_1m", 1_000_000),
    ]

    for name, capital in capital_amounts:
        suite.add_variation(
            name=name,
            initial_capital=capital,
        )

    logger.info("Running %d capital variations...", len(suite.variations))
    results = suite.run_all()

    # Analyze scalability
    summary = get_summary_dataframe(results)
    successful = summary[summary["success"] == True]  # noqa: E712

    if not successful.empty:
        logger.info("\n=== Capital Scalability Analysis ===")
        for _, row in successful.iterrows():
            # Calculate commission as percentage of final value
            comm_pct = (row["total_commissions"] / row["final_value"]) * 100
            logger.info(
                "%s: Return=%.2f%%, Commissions=%.2f (%.4f%% of final)",
                row["name"],
                row["annualized_return"] * 100,
                row["total_commissions"],
                comm_pct,
            )

    # Generate report
    report_path = generate_comparative_excel_report(
        suite_results=results,
        output_directory=setup.configuration.backtest_results_output_directory,
        report_name="capital_scalability_analysis",
        ranking_metric="sharpe_ratio",
    )

    logger.info("\nCapital scalability report: %s", report_path)

    return results, report_path


# =============================================================================
# EXAMPLE 9: Different cash reserve percentages
# =============================================================================

def example_9_cash_reserve_variations():
    """
    Example 9: Test different cash reserve percentages.

    Cash reserve affects how much capital is held in cash vs invested.
    Higher reserves provide a buffer for rebalancing but reduce market exposure.
    """
    try:
        setup = _load_configuration_and_handlers()
    except ConfigurationError as ex:
        logger.error("Configuration failed: %s", ex)
        return None

    try:
        logger.info("Executing data pipeline...")
        pipeline_result = execute_data_pipeline(
            configuration=setup.configuration,
            input_handlers=[setup.market_data_handler],
            portfolio_handlers=[setup.portfolio_handler]
        )
        logger.info("Data pipeline completed.\n")
    except DataPipelineError as ex:
        logger.error("Data pipeline failed: %s", ex)
        return None

    # Create suite
    suite = BacktestVariationRunner(
        base_config=setup.configuration,
        pipeline_result=pipeline_result,
    )

    # Test different cash reserve levels
    # Note: Valid range is 0.0 to 0.50 (0% to 50%)
    cash_reserves = [
        ("no_reserve_0pct", 0.00),
        ("minimal_2pct", 0.02),
        ("standard_5pct", 0.05),
        ("moderate_10pct", 0.10),
        ("high_15pct", 0.15),
        ("conservative_20pct", 0.20),
    ]

    for name, reserve_pct in cash_reserves:
        suite.add_variation(
            name=name,
            cash_reserve_percentage=reserve_pct,
        )

    logger.info("Running %d cash reserve variations...", len(suite.variations))
    results = suite.run_all()

    # Analyze impact of cash reserves
    summary = get_summary_dataframe(results)
    successful = summary[summary["success"] == True]  # noqa: E712

    if not successful.empty:
        logger.info("\n=== Cash Reserve Impact Analysis ===")
        for _, row in successful.iterrows():
            logger.info(
                "%s: Return=%.2f%%, Sharpe=%.4f, MaxDD=%.2f%%",
                row["name"],
                row["annualized_return"] * 100,
                row["sharpe_ratio"],
                row["max_drawdown"] * 100,
            )

    # Generate report
    report_path = generate_comparative_excel_report(
        suite_results=results,
        output_directory=setup.configuration.backtest_results_output_directory,
        report_name="cash_reserve_analysis",
        ranking_metric="sharpe_ratio",
    )

    logger.info("\nCash reserve analysis report: %s", report_path)

    return results, report_path


# =============================================================================
# EXAMPLE 10: Parameter grid search (commission x cash reserve)
# =============================================================================

def example_10_parameter_grid_search():
    """
    Example 10: Grid search over multiple parameters.

    Demonstrates systematic exploration of parameter combinations
    to find optimal settings for commission and cash reserve.
    """
    try:
        setup = _load_configuration_and_handlers()
    except ConfigurationError as ex:
        logger.error("Configuration failed: %s", ex)
        return None

    try:
        logger.info("Executing data pipeline...")
        pipeline_result = execute_data_pipeline(
            configuration=setup.configuration,
            input_handlers=[setup.market_data_handler],
            portfolio_handlers=[setup.portfolio_handler]
        )
        logger.info("Data pipeline completed.\n")
    except DataPipelineError as ex:
        logger.error("Data pipeline failed: %s", ex)
        return None

    # Create suite
    suite = BacktestVariationRunner(
        base_config=setup.configuration,
        pipeline_result=pipeline_result,
    )

    # Define parameter grids
    commission_values = [0.005, 0.01, 0.02, 0.03]
    cash_reserve_values = [0.02, 0.05, 0.10]

    # Create all combinations
    for comm in commission_values:
        for reserve in cash_reserve_values:
            name = f"comm_{comm:.3f}_reserve_{reserve:.2f}"
            suite.add_variation(
                name=name,
                commission_cents=comm,
                cash_reserve_percentage=reserve,
            )

    logger.info(
        "Running %d parameter combinations (commission x cash_reserve)...",
        len(suite.variations)
    )

    # Run with progress tracking
    def on_progress(done: int, total: int, name: str):
        logger.info("[%d/%d] Completed: %s", done, total, name)

    results = suite.run_all(progress_callback=on_progress)

    # Find best configuration
    summary = get_summary_dataframe(results)
    successful = summary[summary["success"] == True]  # noqa: E712

    if not successful.empty:
        # Sort by Sharpe ratio
        best = successful.sort_values("sharpe_ratio", ascending=False).iloc[0]

        logger.info("\n=== Grid Search Results ===")
        logger.info("Total combinations tested: %d", len(successful))
        logger.info("\nBest configuration (by Sharpe ratio):")
        logger.info("  Name: %s", best["name"])
        logger.info("  Sharpe Ratio: %.4f", best["sharpe_ratio"])
        logger.info("  Annualized Return: %.2f%%", best["annualized_return"] * 100)
        logger.info("  Max Drawdown: %.2f%%", best["max_drawdown"] * 100)
        logger.info("  Total Commissions: %.2f", best["total_commissions"])

    # Generate report
    report_path = generate_comparative_excel_report(
        suite_results=results,
        output_directory=setup.configuration.backtest_results_output_directory,
        report_name="parameter_grid_search",
        ranking_metric="sharpe_ratio",
    )

    logger.info("\nGrid search report: %s", report_path)

    return results, report_path


# =============================================================================
# EXAMPLE 11: Commission sensitivity analysis
# =============================================================================

def example_11_commission_sensitivity():
    """
    Example 11: Fine-grained commission sensitivity analysis.

    Tests a wide range of commission rates to understand the
    break-even point where commissions erode returns significantly.
    """
    try:
        setup = _load_configuration_and_handlers()
    except ConfigurationError as ex:
        logger.error("Configuration failed: %s", ex)
        return None

    try:
        logger.info("Executing data pipeline...")
        pipeline_result = execute_data_pipeline(
            configuration=setup.configuration,
            input_handlers=[setup.market_data_handler],
            portfolio_handlers=[setup.portfolio_handler]
        )
        logger.info("Data pipeline completed.\n")
    except DataPipelineError as ex:
        logger.error("Data pipeline failed: %s", ex)
        return None

    # Create suite
    suite = BacktestVariationRunner(
        base_config=setup.configuration,
        pipeline_result=pipeline_result,
    )

    # Fine-grained commission grid (0 to 10 cents, steps of 0.5 cents)
    # Note: Valid range is 0.0 to 0.10
    commission_values = [
        0.000,  # No commission
        0.005,  # 0.5 cents
        0.010,  # 1.0 cent
        0.015,  # 1.5 cents
        0.020,  # 2.0 cents
        0.025,  # 2.5 cents
        0.030,  # 3.0 cents
        0.040,  # 4.0 cents
        0.050,  # 5.0 cents
        0.075,  # 7.5 cents
        0.100,  # 10.0 cents (max)
    ]

    suite.add_commission_grid(
        commission_values=commission_values,
        name_prefix="sens",
    )

    logger.info("Running %d commission sensitivity tests...", len(suite.variations))
    results = suite.run_all()

    # Analyze sensitivity
    summary = get_summary_dataframe(results)
    successful = summary[summary["success"] == True]  # noqa: E712

    if not successful.empty:
        logger.info("\n=== Commission Sensitivity Analysis ===")
        baseline_return = successful.iloc[0]["annualized_return"]

        for _, row in successful.iterrows():
            return_diff = (row["annualized_return"] - baseline_return) * 100
            logger.info(
                "%s: Return=%.2f%% (Δ%.2f%%), Commissions=%.2f",
                row["name"],
                row["annualized_return"] * 100,
                return_diff,
                row["total_commissions"],
            )

    # Generate report
    report_path = generate_comparative_excel_report(
        suite_results=results,
        output_directory=setup.configuration.backtest_results_output_directory,
        report_name="commission_sensitivity",
        ranking_metric="annualized_return",
    )

    logger.info("\nCommission sensitivity report: %s", report_path)

    return results, report_path


# =============================================================================
# EXAMPLE 13: Bull vs Bear market comparison
# =============================================================================

def example_13_market_regime_analysis():
    """
    Example 13: Compare strategy performance in different market regimes.

    Demonstrates testing strategy robustness across bull and bear markets.
    Note: Adjust dates based on actual market conditions in your data.
    """
    try:
        setup = _load_configuration_and_handlers()
    except ConfigurationError as ex:
        logger.error("Configuration failed: %s", ex)
        return None

    try:
        logger.info("Executing data pipeline...")
        pipeline_result = execute_data_pipeline(
            configuration=setup.configuration,
            input_handlers=[setup.market_data_handler],
            portfolio_handlers=[setup.portfolio_handler]
        )
        logger.info("Data pipeline completed.\n")
    except DataPipelineError as ex:
        logger.error("Data pipeline failed: %s", ex)
        return None

    # Create suite
    suite = BacktestVariationRunner(
        base_config=setup.configuration,
        pipeline_result=pipeline_result,
    )

    # Define market regime periods (example dates - adjust based on your data)
    market_regimes = [
        # COVID crash and recovery
        ("covid_crash_2020", datetime.date(2020, 2, 19), datetime.date(2020, 3, 23)),
        ("covid_recovery_2020", datetime.date(2020, 3, 24), datetime.date(2020, 8, 31)),
        # 2021 bull market
        ("bull_2021_h1", datetime.date(2021, 1, 1), datetime.date(2021, 6, 30)),
        ("bull_2021_h2", datetime.date(2021, 7, 1), datetime.date(2021, 12, 31)),
        # 2022 bear market
        ("bear_2022_h1", datetime.date(2022, 1, 1), datetime.date(2022, 6, 30)),
        ("bear_2022_h2", datetime.date(2022, 7, 1), datetime.date(2022, 12, 31)),
        # 2023 mixed/recovery
        ("recovery_2023", datetime.date(2023, 1, 1), datetime.date(2023, 12, 31)),
    ]

    for regime_name, start, end in market_regimes:
        suite.add_variation(
            name=regime_name,
            start_date=start,
            end_date=end,
        )

    logger.info("Running %d market regime backtests...", len(suite.variations))
    results = suite.run_all()

    # Analyze regime performance
    summary = get_summary_dataframe(results)
    successful = summary[summary["success"] == True]  # noqa: E712

    if not successful.empty:
        logger.info("\n=== Market Regime Analysis ===")

        # Categorize results
        bull_results = successful[
            successful["name"].str.contains("bull|recovery", case=False)
        ]
        bear_results = successful[
            successful["name"].str.contains("bear|crash", case=False)
        ]

        if not bull_results.empty:
            logger.info(
                "Bull Markets: Avg Return=%.2f%%, Avg Sharpe=%.4f",
                bull_results["annualized_return"].mean() * 100,
                bull_results["sharpe_ratio"].mean()
            )

        if not bear_results.empty:
            logger.info(
                "Bear Markets: Avg Return=%.2f%%, Avg Sharpe=%.4f",
                bear_results["annualized_return"].mean() * 100,
                bear_results["sharpe_ratio"].mean()
            )

    # Generate report
    report_path = generate_comparative_excel_report(
        suite_results=results,
        output_directory=setup.configuration.backtest_results_output_directory,
        report_name="market_regime_analysis",
        ranking_metric="sharpe_ratio",
    )

    logger.info("\nMarket regime analysis report: %s", report_path)

    return results, report_path

# =============================================================================
# EXAMPLE 15: Using "auto" dates from portfolio
# =============================================================================

def example_15_auto_dates_from_portfolio():
    """
    Example 15: Using "auto" dates derived from portfolio rebalancing dates.

    When start_date or end_date is set to "auto", the backtest engine
    automatically derives dates from the first and last rebalancing
    dates in the portfolio file.
    """
    try:
        setup = _load_configuration_and_handlers()
    except ConfigurationError as ex:
        logger.error("Configuration failed: %s", ex)
        return None

    try:
        logger.info("Executing data pipeline...")
        pipeline_result = execute_data_pipeline(
            configuration=setup.configuration,
            input_handlers=[setup.market_data_handler],
            portfolio_handlers=[setup.portfolio_handler]
        )
        logger.info("Data pipeline completed.\n")
    except DataPipelineError as ex:
        logger.error("Data pipeline failed: %s", ex)
        return None

    # Create suite
    suite = BacktestVariationRunner(
        base_config=setup.configuration,
        pipeline_result=pipeline_result,
    )

    # Variation 1: Full auto dates (both derived from portfolio)
    suite.add_variation(
        name="2020-01-02_2025-09-26",
        start_date="auto",
        end_date="auto",
    )

    # Variation 2: Auto start with fixed end
    suite.add_variation(
        name="2020-01-02_2022-12-31",
        start_date="auto",
        end_date=datetime.date(2022, 12, 31),
    )

    # Variation 3: Fixed start with auto end
    suite.add_variation(
        name="2022-01-01_2025-09-26",
        start_date=datetime.date(2022, 1, 1),
        end_date="auto",
    )

    # Variation 4: Explicit dates for comparison
    suite.add_variation(
        name="2020-01-01_2024-12-31",
        start_date=datetime.date(2020, 1, 1),
        end_date=datetime.date(2024, 12, 31),
    )

    logger.info("Running %d date configuration variations...", len(suite.variations))
    results = suite.run_all()

    # Analyze results
    summary = get_summary_dataframe(results)
    successful = summary[summary["success"] == True]  # noqa: E712

    if not successful.empty:
        logger.info("\n=== Auto Date Configuration Results ===")
        for _, row in successful.iterrows():
            logger.info(
                "%s: Return=%.2f%%, Sharpe=%.4f, Final=%.2f",
                row["name"],
                row["annualized_return"] * 100,
                row["sharpe_ratio"],
                row["final_value"],
            )

    # Generate comparative Excel report
    report_path = generate_comparative_excel_report(
        suite_results=results,
        output_directory=setup.configuration.backtest_results_output_directory,
        report_name="auto_dates_analysis",
        ranking_metric="sharpe_ratio",
    )
    logger.info("Report saved to: %s", report_path)

    return results, report_path


# =============================================================================
# Main execution
# =============================================================================
#%%

results_15, report_path_15 = example_15_auto_dates_from_portfolio()
