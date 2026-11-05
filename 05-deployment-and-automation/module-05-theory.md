# Module 5 theory - deployment and automation

## What Module 5 is about

Modules 1-4 build the research workflow: collect data, create features, fit a
model, and simulate a strategy. Module 5 asks what happens after the notebook
works once. A useful system must be repeatable, observable, and explicit about
what it is allowed to do.

The 2026 lesson combines advanced strategy simulation with the practical steps
needed to automate a daily prediction pipeline. The goal is not to place a live
trade during the course. The goal is to understand the boundary between a
research notebook and a controlled, testable process.

## 1. From notebook to pipeline

A notebook is excellent for exploration, but it often hides state in executed
cells and depends on the current working directory. A deployable pipeline makes
each step explicit:

```text
fetch -> validate -> transform -> train/load model -> predict -> rank -> report
```

Keep the steps in small functions with clear inputs and outputs. A typical daily
run should be possible from a clean process, without relying on variables left
over from an earlier notebook cell.

```python
def run_pipeline(run_date):
    raw = fetch_prices(run_date)
    clean = validate_and_transform(raw)
    model = load_or_train_model(clean)
    predictions = make_predictions(model, clean)
    save_predictions(predictions, run_date)
    return predictions
```

The function names are illustrative. In real work, also record the data source,
model version, feature configuration, and execution timestamp.

## 2. Reproducible data and storage

The latest API response is not necessarily the same data tomorrow. Save enough
information to reproduce a run:

- retrieval timestamp and requested date range;
- ticker universe and provider;
- raw or immutable input data when permitted;
- cleaned feature data or the transformation version;
- model parameters and training cutoff;
- predictions, decisions, and run status.

Files such as Parquet are convenient for tabular historical data. SQLite is
useful when the pipeline needs a small local database for run metadata,
predictions, orders, or portfolio snapshots. A minimal prediction table might
contain `run_id`, `as_of_date`, `ticker`, `prediction`, `signal`, `model_version`,
and `created_at`.

Do not silently overwrite prior results. A unique run identifier and an
`as_of_date` make it possible to audit what the system knew at the time.

## 3. Simulation realism and advanced strategies

Module 4 introduced returns, costs, positions, and drawdown. Module 5 extends
the simulation to decisions made across a universe of assets:

- rank assets by predicted return or probability;
- select the top or bottom group with a documented tie rule;
- cap position sizes and total exposure;
- rebalance only when the target portfolio changes;
- charge entry, exit, spread, and slippage costs;
- compare with buy-and-hold and a simple benchmark;
- evaluate out-of-sample results with the same rules used in training.

For weights $w_{i,t}$, portfolio return is approximately:

$$
r_{p,t} = \sum_i w_{i,t-1} r_{i,t} - c \sum_i |w_{i,t} - w_{i,t-1}|
$$

Using the previous day's weights makes the execution timing explicit. The
turnover term charges for changes in the portfolio rather than for a signal that
does not result in a position change.

## 4. Model training and inference

Training and inference should be separate decisions. A daily job may load a
versioned model trained through a fixed cutoff, while a scheduled weekly job
re-trains it. Never let today's incomplete data enter a model that claims to
predict today's close.

At minimum, log:

- the training start and end dates;
- features and target definition;
- model class and hyperparameters;
- validation metrics and baseline metrics;
- the prediction timestamp;
- missing or rejected tickers.

If a model cannot be loaded, the process should fail clearly or produce a
documented no-trade result. Falling back silently to a different model makes the
output difficult to trust.

## 5. Scheduling and automation

Cron can run a Python script on a schedule. A cron command should use absolute
paths, change to the project directory, and redirect logs:

```cron
0 21 * * 1-5 cd /absolute/path/to/project && /absolute/path/to/venv/bin/python main.py >> /absolute/path/to/project/cron.log 2>&1
```

The schedule is not the whole system. The script must handle market holidays,
provider delays, retries, and duplicate runs. For larger workflows, an
orchestrator such as Airflow can represent task dependencies, retries, and run
history more clearly than a single cron entry.

Use a dry-run or paper-trading mode before connecting an execution API. The
automation should first produce a report of intended orders and require a human
or a separate approval step before real execution.

## 6. Reliability and safety checks

Useful checks before producing a signal include:

1. The input date is newer than the last successful run, or the run is explicitly
   marked as a replay.
2. Required columns exist and have plausible ranges.
3. The number of valid tickers is above a minimum threshold.
4. No future data was used in features or model fitting.
5. Position limits, cash limits, and maximum turnover are respected.
6. The output contains no duplicate ticker/date decisions.
7. A failed data fetch cannot be mistaken for a zero return.

Make jobs idempotent where possible: running the same input twice should not
create duplicate trades or corrupt the portfolio. Store a run status such as
`started`, `succeeded`, or `failed`, and include the exception in the log.

## 7. Monitoring and evaluation

Monitoring is more than checking whether the Python process exited successfully.
Track data freshness, row counts, missing values, prediction distributions,
turnover, exposure, realized returns, and drawdown. Compare live behavior with
the backtest assumptions.

An alert should answer: what failed, when did it fail, which run was affected,
and whether the system took any action. Email notifications can be useful for a
small project, but notifications should summarize a logged run rather than be
the only record of it.

## 8. Research ideas are the deployment starting point

The 2026 Homework 5 is exploratory and asks for three different stock research
ideas. A strong idea is specific enough to become a pipeline later:

```text
opportunity -> thesis -> observable data -> signal/test -> decision -> risks
```

"Use machine learning to predict stocks" is not a testable idea. Specify the
market, horizon, outcome, information source, benchmark, and evidence that would
make you reject the hypothesis. Distinct ideas should differ in their economic
mechanism, data source, market, or horizon, not only in ticker or algorithm.

## 9. Practical checklist

Before calling a strategy automated, confirm that you can answer:

- What data did the system know at the decision time?
- Where is each input and output stored?
- How is the model version identified?
- What happens when data is missing or stale?
- How are fees, slippage, liquidity, and position limits modeled?
- Can the run be repeated without duplicate actions?
- Can a person inspect and approve the intended action?
- Which benchmark and rejection criteria determine whether the idea survives?

Automation makes a flawed assumption run faster. Validation, logging, and a
well-defined no-trade path are part of the strategy, not afterthoughts.
