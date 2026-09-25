# Module 2 theory — working with data in Pandas

## What Module 2 is about

Module 2 teaches how to turn raw market and web data into a clean analysis table.
The main workflow is:

1. Load data from an API or an HTML table.
2. Combine compatible tables into one DataFrame.
3. Inspect and correct data types.
4. Handle missing values deliberately.
5. Create dates, returns, growth rates, and other features.
6. Build future outcomes for a model without confusing them with available information.
7. Summarize and visualize the result.

Pandas is useful because it lets you perform these operations on whole columns at
once. The index and the data types are part of the meaning of a DataFrame, not
just implementation details.

## 1. DataFrames and columns

A DataFrame is a rectangular table with named columns and an index. A Series is
one labeled column. You can inspect a new table quickly with:

```python
df.head()
df.tail()
df.info()
df.shape
df.describe()
df.isnull().sum()
```

These checks answer different questions:

- `head()` and `tail()` show the actual values and boundaries.
- `info()` shows column types and non-null counts.
- `shape` gives the number of rows and columns.
- `describe()` summarizes numeric columns.
- `isnull().sum()` counts missing values in each column.

Do not assume that a column that looks numeric is numeric. A value such as
`"$25.00"`, `"12.4%"`, or `"-"` is text until it is converted.

## 2. Loading web data

The module uses `requests` and `pandas.read_html()` to retrieve IPO tables from
the web. A robust retrieval function should:

- construct the URL from an explicit year or other parameter;
- send a reasonable `User-Agent` when the site expects a browser-like request;
- set a timeout;
- call `raise_for_status()` so HTTP errors are not mistaken for valid data;
- check that a table was found;
- return an empty DataFrame or raise a clear error when retrieval fails.

Example shape:

```python
import pandas as pd
import requests
from io import StringIO

def get_table(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text))
    if not tables:
        raise ValueError("No HTML tables found")
    return tables[0]
```

Web data is less stable than an API. Keep the URL, retrieval date, and expected
column names so a changed page layout can be detected.

## 3. Stacking DataFrames with `concat`

When several tables have the same columns and represent more rows of the same
kind of data, stack them vertically with `pd.concat()`:

```python
ipos = pd.concat(
    [ipos_2026, ipos_2025, ipos_2024, ipos_2023],
    ignore_index=True,
)
```

This is similar to SQL `UNION ALL`. It preserves rows, including duplicates.
`ignore_index=True` gives the combined table a new sequential index instead of
keeping the old indexes from each source table.

Before concatenating, check that the tables have compatible column names and
meanings. Concatenation does not validate that `Current` means the same thing in
every input table.

## 4. Type conversion and missing values

Convert columns before calculating statistics. For example:

```python
ipos["IPO Date"] = pd.to_datetime(ipos["IPO Date"], format="mixed")
ipos["IPO Price"] = pd.to_numeric(
    ipos["IPO Price"].str.replace("$", "", regex=False),
    errors="coerce",
)
ipos["Return"] = pd.to_numeric(
    ipos["Return"].str.replace("%", "", regex=False),
    errors="coerce",
) / 100
```

`errors="coerce"` converts values that cannot be parsed into `NaN`. This is
often safer than stopping halfway through a data pipeline, but it does not solve
the data-quality problem. After conversion, inspect the rows that became
missing:

```python
ipos.isnull().sum()
ipos[ipos["Return"].isnull()]
```

Choose a policy based on the question:

- keep the row if the missing value is meaningful;
- exclude it from a calculation that needs that field;
- fill it only when a defensible value is known;
- investigate the source when missingness indicates a parsing failure.

Never silently replace an unknown financial value with zero. Zero means that a
real value was observed and was exactly zero.

## 5. Creating columns and simple analytics

Pandas applies arithmetic to a whole Series. A new column can therefore be a
direct expression:

```python
ipos["Price Increase"] = ipos["Current"] - ipos["IPO Price"]
```

For a more complex transformation, use a named function or a vectorized Pandas
operation. Prefer vectorized operations over row-by-row `apply()` when the
calculation can be expressed with column operations.

After creating a numeric column, common summaries include:

```python
ipos["Price Increase"].mean()
ipos["Return"].median()
ipos["Return"].quantile([0.25, 0.50, 0.75])
ipos.describe()
```

The mean can be strongly affected by a few extreme IPO outcomes. The median and
quantiles describe the typical observation and the spread more robustly.

## 6. Datetime indexes and OHLCV data

Market history returned by `yfinance` normally has a `DatetimeIndex` and columns
such as `Open`, `High`, `Low`, `Close`, `Adj Close`, and `Volume`:

```python
import yfinance as yf

nvo = yf.Ticker("NVO").history(period="max", interval="1d")
```

An index is useful for date filtering:

```python
nvo_2020 = nvo[nvo.index >= "2020-01-01"]
nvo_2024 = nvo[nvo.index >= "2024-01-01"]
```

You can extract calendar features from a datetime index:

```python
nvo["Ticker"] = "NVO"
nvo["Year"] = nvo.index.year
nvo["Month"] = nvo.index.month
nvo["Weekday"] = nvo.index.weekday
nvo["Date"] = nvo.index.date
```

Use the same price field throughout a calculation. `Close` is the observed
closing price; an adjusted field is intended to account for corporate actions.
Mixing them can create artificial returns.

## 7. `shift()` and historical growth

`shift(1)` moves the previous row's value onto the current row. For a closing
price $P_t$, a one-day growth factor is:

$$
g_t = \frac{P_t}{P_{t-1}}
$$

In Pandas:

```python
nvo["growth_1d"] = nvo["Close"] / nvo["Close"].shift(1)
nvo["growth_30d"] = nvo["Close"] / nvo["Close"].shift(30)
```

These are growth factors. A factor of `1.02` means a 2% return. To store the
return directly, subtract one:

```python
nvo["return_1d"] = nvo["Close"] / nvo["Close"].shift(1) - 1
```

The first row, or first 30 rows for a 30-row lag, has no prior observation and
must be missing. That is expected and should not be filled with zero.

The lag is a number of rows, not automatically a number of calendar days. With
daily trading data, `shift(30)` means 30 trading observations, which may span
more than 30 calendar days because of weekends and holidays.

## 8. Future growth and prediction targets

`shift(-1)` moves the next row's value onto the current row. This creates a
future outcome:

```python
nvo["growth_future_1d"] = nvo["Close"].shift(-1) / nvo["Close"]
nvo["growth_future_30d"] = nvo["Close"].shift(-30) / nvo["Close"]
```

The final row, or final 30 rows for a 30-row horizon, has no future observation.
Those rows cannot be used as complete labels.

Future growth is appropriate as a **target** for supervised learning, but it is
not available at prediction time. Do not include `growth_future_1d` as an input
feature for a model that is supposed to predict it. That would be look-ahead
bias: the model would be given information from the future.

The safe conceptual split is:

- **Features:** values known at the decision time, such as past returns, volume,
  calendar fields, and technical indicators.
- **Target:** the outcome after the decision time, such as the next-day return.

## 9. Regression and binary classification targets

A regression target keeps the numeric future outcome:

```python
nvo["target_return_1d"] = nvo["growth_future_1d"] - 1
```

A binary target turns it into a category. The notebook uses `1` for positive
future growth and `0` otherwise:

```python
nvo["is_positive_growth_1d_future"] = (
    nvo["growth_future_1d"] > 1
).astype(int)
```

Check the class balance before interpreting a classifier:

```python
nvo["is_positive_growth_1d_future"].value_counts(normalize=True)
```

If 60% of observations are positive, a model that always predicts positive is
already 60% accurate. Accuracy alone is therefore not enough; compare against a
simple baseline and use an appropriate out-of-sample evaluation.

## 10. Grouping and time-based summaries

Once calendar columns exist, they can be used to summarize observations by
month, year, or another category. For example, monthly IPO counts can be built
by converting each date to a month and counting rows:

```python
ipos["Date_monthly"] = (
    ipos["IPO Date"].dt.to_period("M").dt.to_timestamp()
)
monthly_deals = (
    ipos["Date_monthly"].value_counts()
    .rename_axis("Date_monthly")
    .reset_index(name="Number of Deals")
    .sort_values("Date_monthly")
)
```

The sort is important for a time-series chart. `value_counts()` otherwise orders
the result by frequency, not by time.

## 11. A practical validation checklist

Before trusting a transformed DataFrame, check:

1. The row count before and after concatenation.
2. Column names, dtypes, and non-null counts after conversion.
3. Duplicate dates or duplicate securities where uniqueness is expected.
4. The first and last rows after every `shift()` transformation.
5. Whether the calculation uses a growth factor or a return.
6. Whether a lag is measured in trading observations or calendar time.
7. Whether future columns are targets only and excluded from model features.
8. Whether missing values at the edges are expected.
9. Whether the result is plausible when plotted or summarized.

## 12. What to be able to explain after Module 2

You should be able to explain:

1. When to use `pd.concat()` and why `ignore_index=True` is useful.
2. Why strings containing `$`, `%`, or `-` need cleaning before numeric analysis.
3. Why `errors="coerce"` must be followed by a missing-value check.
4. How a `DatetimeIndex` supports filtering and feature creation.
5. The difference between `shift(1)` for historical values and `shift(-1)` for future values.
6. The difference between a growth factor such as `1.03` and a return such as `0.03`.
7. Why future growth belongs in a target column, not in the feature set.
8. Why edge rows are missing after lagged and forward-looking calculations.
9. Why median, quantiles, plots, and out-of-sample checks are useful alongside means.

## 13. Homework 2 connection

The official assignment is in the yearly `cohorts` folder and is linked from the
[Module 2 README](https://github.com/DataTalksClub/stock-markets-analytics-zoomcamp/tree/main/02-dataframe-analysis).

The notebook's IPO example prepares the central homework pattern: collect data
for several years, stack it, clean its types, derive a holding-period return,
compare horizons, and evaluate the result on another year's data. Keep the
intermediate DataFrames and document:

- the source URL and retrieval date;
- the exact price field used;
- the holding-period convention;
- how missing or incomplete IPO rows were handled;
- whether the chosen horizon was selected in-sample and then tested out-of-sample.

An attractive average return in the training period is not enough to establish a
strategy. Inspect the distribution, median, quantiles, losing cases, and
performance on a different period before drawing a conclusion.
