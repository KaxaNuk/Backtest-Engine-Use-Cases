import logging

from kaxanuk.backtest_engine.backtest.pyarrow_backtester import PyArrowBacktester
from kaxanuk.backtest_engine.config_handlers.excel_configurator import ExcelConfigurator
from kaxanuk.backtest_engine.data_processors.data_pipeline_executor import execute_data_pipeline
from kaxanuk.backtest_engine.input_handlers.csv_input import CsvInput
from kaxanuk.backtest_engine.input_handlers.parquet_input import ParquetInput
from kaxanuk.backtest_engine.input_handlers.excel_portfolio_input_handler import ExcelPortfolioInputHandler
from kaxanuk.backtest_engine.input_handlers.csv_portfolio_input_handler import CsvPortfolioInputHandler
from kaxanuk.backtest_engine.services.config_logger import configure_logger
from kaxanuk.backtest_engine.exceptions import (
    BacktestError,
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
    logger_file=None,
)

load_config_env()

#%%

# -------------------------------------------------------------------
# 1) Read configuration from Excel
# -------------------------------------------------------------------
configurator = ExcelConfigurator(file_path="Config/backtest_engine_parameters.xlsx")

try:
    configuration = configurator.get_configuration()
except ConfigurationError as ex:
    logger.error("Configuration failed: %s", ex)
    raise

logger.info("Configuration loaded. Portfolio: %s", configuration.portfolio_name)

# -------------------------------------------------------------------
# 2) Choose input handlers according to the configuration
# -------------------------------------------------------------------
market_data_input_handlers = {
    "csv": CsvInput(input_dir=configuration.input_market_data_directory),
    "parquet": ParquetInput(input_dir=configuration.input_market_data_directory),
}

portfolio_input_handlers = {
    "csv": CsvPortfolioInputHandler(base_dir=configuration.input_portfolio_directory),
    "excel": ExcelPortfolioInputHandler(base_dir=configuration.input_portfolio_directory),
}

market_data_input_handler = market_data_input_handlers[configuration.market_data_input_format]
portfolio_input_handler = portfolio_input_handlers[configuration.portfolio_input_format]

logger.info(
    "Using market handler=%s, portfolio handler=%s",
    configuration.market_data_input_format,
    configuration.portfolio_input_format,
)

# -------------------------------------------------------------------
# 3) Run pipeline ONCE (read + validate + prepare tables)
# -------------------------------------------------------------------
try:
    pipeline_result = execute_data_pipeline(
        configuration=configuration,
        input_handlers=[market_data_input_handler],
        portfolio_handlers=[portfolio_input_handler],
    )
except DataPipelineError as ex:
    logger.error("Data pipeline failed: %s", ex)
    raise

logger.info("Pipeline OK. Creating backtester...")

#%%

# -------------------------------------------------------------------
# 4) Create backtester from pipeline_result (without modifying anything)
# -------------------------------------------------------------------
backtester = PyArrowBacktester.create_from_pipeline_result(
    configuration=configuration,
    pipeline_result=pipeline_result,
)

#%%

# -------------------------------------------------------------------
# 5) Run backtest
# -------------------------------------------------------------------
try:
    results = backtester.run_with_benchmark()
except BacktestError as ex:
    logger.error("Backtest failed: %s", ex)
    raise
