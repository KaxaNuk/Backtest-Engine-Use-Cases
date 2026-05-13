# Backtest-Engine-Use-Cases

Runnable examples that teach how to use the **KaxaNuk Backtest Engine**
(`kaxanuk.backtest_engine`) — from a single-portfolio baseline run to
parameter sensitivity studies and multi-portfolio batch processing.

Each script in `backtest_use_cases/` is self-contained: open it, read the
comments, run it, inspect the Excel reports it writes to `Output/`.

**Engine documentation:** https://kaxanuk-backtest-engine.readthedocs-hosted.com/en/latest/

---

## What's inside

| Script | What it teaches | Complexity |
|---|---|---|
| [`backtest_use_cases/basic_single_backtest.py`](backtest_use_cases/basic_single_backtest.py) | Minimal end-to-end pipeline: load Excel config → execute data pipeline → run one backtest against a benchmark using `PyArrowBacktester`. **Start here.** | Beginner |
| [`backtest_use_cases/parameter_sensitivity_analysis.py`](backtest_use_cases/parameter_sensitivity_analysis.py) | Ten variation studies powered by `BacktestVariationRunner`: commission grids, capital scalability ($10k–$1M), cash-reserve sweeps (0–20%), parameter grid search, rolling-window walk-forward, bull-vs-bear regime comparison, auto-dating from rebalance dates. | Intermediate |
| [`backtest_use_cases/batch_inline_portfolios.py`](backtest_use_cases/batch_inline_portfolios.py) | Running several portfolios in one go with `MultiPortfolioBacktester`, with portfolios defined inline as Python dicts (no external portfolio files needed). Includes a cost-sensitivity variation. | Intermediate |
| [`backtest_use_cases/batch_directory_scan.py`](backtest_use_cases/batch_directory_scan.py) | Auto-discovering every CSV/Excel portfolio in `Input/Portfolios/` and batching them with auto-dated rebalance ranges. Comparative report ranked by Sharpe ratio. | Advanced |

---

## Repository layout

```
Backtest-Engine-Use-Cases/
├── Config/
│   ├── .env                                # KNBE_API_KEY_KAXANUK (not committed)
│   └── backtest_engine_parameters.xlsx     # Excel-driven backtest config (not committed)
├── Input/
│   ├── Data/                               # Market data: CSV or Parquet (not committed)
│   └── Portfolios/                         # Portfolio definitions: CSV or Excel (not committed)
├── Output/                                 # Generated Excel reports (not committed)
├── backtest_use_cases/
│   ├── basic_single_backtest.py
│   ├── parameter_sensitivity_analysis.py
│   ├── batch_inline_portfolios.py
│   └── batch_directory_scan.py
├── .gitignore
└── README.md
```

`Config/*.xlsx`, `Config/.env`, `Input/Data/*`, `Input/Portfolios/*`, and
`Output/*` are all gitignored — supply them locally.

---

## Requirements

- Python 3.10+
- The `kaxanuk.backtest_engine` package installed in your environment
- A valid `KNBE_API_KEY_KAXANUK` license key

---

## Setup

1. **Clone the repo** and open a shell at its root.
2. **Install the engine** in your Python environment (see the
   [engine documentation](https://kaxanuk-backtest-engine.readthedocs-hosted.com/en/latest/)
   for installation instructions).
3. **Initialize the project scaffolding** — creates `Config/`, `Input/Data/`,
   `Input/Portfolios/`, `Output/`, and a `__main__.py` entry point in one
   shot:
   ```bash
   kaxanuk.backtest_engine init excel
   ```
4. **Create `Config/.env`** with your license key:
   ```
   KNBE_API_KEY_KAXANUK=<your-key-here>
   ```
5. **Place the Excel configuration** at
   `Config/backtest_engine_parameters.xlsx`. This file drives the
   Excel-configured examples (`basic_single_backtest.py`,
   `parameter_sensitivity_analysis.py`).
6. **Drop market-data files** in `Input/Data/` (CSV or Parquet, depending
   on what your Excel config selects).
7. **Drop portfolio definition files** in `Input/Portfolios/` (CSV or
   Excel). Required by `batch_directory_scan.py`; optional for the inline
   batch script.

---

## Running the examples

Run every script from the **repository root** so the relative paths resolve
correctly.

```bash
# 1. Basic single backtest (uses Config/backtest_engine_parameters.xlsx)
python backtest_use_cases/basic_single_backtest.py

# 2. Sensitivity / variation studies (uses Config/backtest_engine_parameters.xlsx)
python backtest_use_cases/parameter_sensitivity_analysis.py

# 3. Batch with inline portfolios (no portfolio files needed)
python backtest_use_cases/batch_inline_portfolios.py

# 4. Batch with directory scanning (requires files in Input/Portfolios/)
python backtest_use_cases/batch_directory_scan.py
```

Reports land under `Output/<example_name>/` as Excel files — one per
portfolio plus a comparative summary for the batch runs.

---

## Configuration

There are **two configuration styles** in this repo:

- **Excel-driven** (`basic_single_backtest.py`,
  `parameter_sensitivity_analysis.py`): every parameter — dates, capital,
  commission, benchmark, input format, column mappings — lives in
  `Config/backtest_engine_parameters.xlsx`. Edit the spreadsheet, re-run.
- **Inline Python constants** (`batch_inline_portfolios.py`,
  `batch_directory_scan.py`): parameters are defined as `UPPER_SNAKE_CASE`
  constants at the top of the script. Edit the file, re-run.

The defaults assume CSV inputs and a SPY benchmark; adjust the constants
or the Excel config to match your data.

---

## Optional: interactive dashboard

The `kaxanuk.backtest_engine init excel` command generates a local
`__main__.py` (gitignored on purpose) that launches the engine's
interactive dashboard:

```bash
python -m Backtest-Engine-Use-Cases
```

It loads `Config/backtest_engine_parameters.xlsx` and serves the dashboard
on the port configured there. Useful for visually exploring results
without writing code.

---

## Notes

- All file paths in the example scripts are **relative to the repo root**.
- Re-running an example overwrites the previous Excel reports under
  `Output/`.
- For the rationale behind each variation study, read the inline comments
  inside `parameter_sensitivity_analysis.py` — every example block has a
  header explaining what it demonstrates.
