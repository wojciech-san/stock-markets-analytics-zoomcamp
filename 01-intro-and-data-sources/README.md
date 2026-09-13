# Module 1 — Introduction and data sources

Module 1 is about the first part of a data-driven trading workflow: finding trustworthy data, downloading it reproducibly, understanding what each observation means, and turning raw prices or economic series into comparable features.

The accompanying notebook is:
`[2026]_Module_01_Colab_Introduction_and_Data_Sources.ipynb`.

For a more direct, theory-focused explanation, see [Module 1 theory — explained simply](module-01-theory.md).

## 1. The mental model

A market-analysis project normally follows this sequence:

1. **Ask a precise question.** Define the asset, time window, frequency, metric, and comparison group before downloading anything.
2. **Choose a source.** A source may provide market prices, macroeconomic indicators, company fundamentals, or news. Record the ticker/series ID and the retrieval date.
3. **Inspect the data.** Check the index type and timezone, frequency, missing values, duplicate dates, units, currency, and whether the series is a price, return, level, or percentage.
4. **Transform it.** Align frequencies and dates, calculate returns or growth rates, and preserve the original columns so the transformation can be audited.
5. **Validate and visualize.** Look at the first/last rows, shape, summary statistics, and a chart. A chart often reveals gaps, regime changes, or an unexpected data adjustment.
6. **State the result with assumptions.** A number is only meaningful together with its dates, price field, data source, and calculation method.

The important distinction is between a **level** and a **change**. GDP, CPI, an index close, and market capitalization are levels. Year-over-year growth, daily return, drawdown, and earnings surprise are changes or relative measures. Levels from different assets are usually not directly comparable; returns often are.

## 2. Main data sources from the notebook

### FRED via `pandas_datareader`

FRED is useful for US macroeconomic time series. The notebook uses:

- `GDPPOT`: real potential GDP, quarterly.
- `CPILFESL`: core CPI, monthly.
- `FEDFUNDS`: effective federal funds rate, monthly.
- `DGS1`, `DGS5`, and related `DGS*` series: Treasury yields, generally daily.
- Additional examples include gold reserves, gold volatility, and crude oil.

The series ID is the contract with FRED. Always read the series page for units, frequency, seasonal adjustment, and revisions. Do not treat a revised macroeconomic history as if it were exactly what an investor knew at the time.

Typical retrieval:

```python
from pandas_datareader import data as pdr

series = pdr.DataReader("CPILFESL", "fred", start=start, end=end)
```

### Yahoo Finance via `yfinance`

Yahoo Finance supplies historical prices, indices, ETFs, corporate actions, earnings dates, and some financial statements:

```python
import yfinance as yf

prices = yf.Ticker("^GSPC").history(
    start="2020-01-01",
    end="2026-01-01",
    interval="1d",
)
```

Useful fields in an OHLCV table:

- **Open, High, Low, Close:** the trading session's prices.
- **Volume:** traded quantity; its meaning differs for indices and securities.
- **Dividends and Stock Splits:** corporate actions.
- **Adj Close:** a price adjusted for distributions and splits in data providers that expose it. Use an adjusted series for total-return-style comparisons, but document exactly which field was used.

An index ticker such as `^GSPC` is not the same thing as an ETF ticker such as `VOO`: they track related exposure but have different prices, trading calendars, dividends, fees, and histories. Tickers can also be exchange-specific (`EICHERMOT.NS`) and index values can be delayed.

### Paid and web-scraped sources

The notebook introduces Polygon.io and Alpha Vantage for paid/news/fundamental data, EDGAR-derived company reports through Yahoo Finance, and HTML scraping for company lists and macro indicators. These sources require extra care:

- Respect terms of service, rate limits, and robots rules.
- Keep the request URL, headers, retrieval timestamp, and raw response where reproducibility matters.
- Check that the expected HTML table still exists; websites change.
- Never assume a successful HTTP response means the table has the expected schema.

## 3. Time series calculations to remember

### Returns and growth

For a level \(x_t\), the one-period percentage change is:

```python
growth = x / x.shift(1) - 1
```

For a year-over-year comparison, use the number of observations in one year at that frequency:

```python
quarterly_yoy = gdp / gdp.shift(4) - 1
monthly_yoy = cpi / cpi.shift(12) - 1
daily_yoy = close / close.shift(252) - 1  # approximate trading year
```

The first shifted observations are necessarily missing. Do not fill them with zero: they do not represent zero growth.

For an interval from an initial close \(P_0\) to a final close \(P_1\):

```python
period_return = final_close / initial_close - 1
```

For a year-to-date comparison, define whether the starting value is the last available close on or before January 1 or the first close in the requested window. Use the same convention for every index.

### Drawdown and correction

The running all-time high is:

```python
running_high = close.cummax()
drawdown = close / running_high - 1
```

A drawdown of `-0.05` is a 5% decline from the previous peak. For Homework 1, a correction is an event reaching at least 5% below the most recent all-time high. Keep the peak date, trough date, recovery/end date if used, drawdown percentage, and duration as separate columns.

Be explicit about the event definition. A correction is not automatically a bear market, and consecutive new highs can make naive “one row per new high” logic double-count a decline. Validate the largest events against the homework's supplied historical examples.

### Earnings reaction

For three consecutive trading closes \(P_1, P_2, P_3\), the homework's two-day reaction is:

```python
two_day_return = close.shift(-2) / close - 1
```

The earnings announcement is treated as the middle day, so align the earnings date to the correct trading session before joining. A positive earnings surprise is a positive `Surprise %`; exclude the future earnings row with no reported EPS/surprise. Correlation measures association, not causation, and a small sample can produce an unstable result.

## 4. Data-quality checklist

Before trusting a result, check:

- **Dates:** timezone, sort order, duplicate rows, weekends/holidays, and inclusive/exclusive `start`/`end` behavior.
- **Frequency:** do not compare monthly CPI directly with daily prices without a documented resampling rule.
- **Missing values:** inspect them before using `shift`, joins, correlations, or quantiles.
- **Price field:** use `Close` or an adjusted field consistently; do not mix adjusted and unadjusted prices.
- **Corporate actions:** dividends and splits can create apparent jumps in raw prices.
- **Units:** rates may be stored as `5.25` (percent points) or `0.0525` (decimal); convert only once.
- **Look-ahead bias:** do not use information published after the date at which a simulated decision would have been made.
- **Reproducibility:** save the ticker/series ID, parameters, retrieval date, and code that produced the answer.

## 5. What to be able to explain after Module 1

You should be able to explain:

1. Why a level and a return answer different questions.
2. Why CPI uses a 12-period lag, GDP uses a 4-period lag, and daily data commonly uses about 252 observations per trading year.
3. Why adjusted prices matter for dividend-paying securities.
4. Why different indices can have different calendars, currencies, delayed quotes, and ticker symbols.
5. How a running maximum identifies a peak and how drawdown is measured from it.
6. Why missing values at the beginning of a shifted series are expected.
7. Why a correlation or median describes the sample and does not by itself prove an investment strategy works.

## 6. Homework 1 — what to do

The official assignment is [`cohorts/2026/homework1.md`](https://github.com/DataTalksClub/stock-markets-analytics-zoomcamp/blob/main/cohorts/2026/homework1.md). Submit answers through the [Module 1 homework form](https://courses.datatalks.club/sma-zoomcamp-2026/homework/hw01). Work in a notebook or script and keep the intermediate tables/plots so each answer can be checked.

### Required questions

#### 1. S&P 500 additions since 2020

- Scrape Wikipedia's S&P 500 companies table with `requests` and `pandas.read_html`.
- Keep ticker, company name, and date added.
- Parse the addition date and extract the calendar year.
- Filter to years from 2020 onward, count additions, and report the year with the largest count.
- **Additional:** count current constituents whose addition date is more than 20 years ago.
- Check date parsing and explain how blank/unknown addition dates were handled.

#### 2. YTD returns for 11 world indices

- Download daily `Close` values for the listed index tickers, from `2026-01-01` through `2026-08-21`.
- Calculate one comparable return per index using the same start/end convention.
- Compare each result with `^GSPC` and count how many performed better.
- **Additional:** repeat the comparison over 3-, 5-, and 10-year windows and say whether the pattern is consistent.
- Ignore currency conversion as instructed, but mention that this limits the economic interpretation.

#### 3. S&P 500 corrections

- Download daily S&P 500 history from 1950 to the present.
- Identify peaks, troughs between consecutive peaks, and drawdowns.
- Keep only events with drawdown of at least 5%.
- Calculate correction duration and report the 25th, 50th (median), and 75th percentiles for both duration and drawdown.
- Compare your largest events with the ten reference events in the assignment.
- State whether duration means calendar days or trading rows and use that definition consistently.

#### 4. Amazon earnings surprises

- Load `AMZN.get_earnings_dates()` and remove the future row without reported surprise data.
- Download complete daily price history.
- Align each earnings announcement to the relevant trading date.
- Compute the return from the close before the announcement through the close two trading days later, following the assignment's three-day definition.
- Filter to positive surprises, report the median two-day return, and calculate correlation between surprise magnitude and return.
- **Additional:** discuss bull/bear segmentation only after defining the market regime and acknowledging the small sample size.

### Optional questions

5. Propose a specific capstone idea: asset/country/sector, prediction or analysis target, horizon, candidate features, and how success would be measured.

6. Explore a few additional metrics from FRED, Yahoo Finance, news, or another permitted source. For each metric, record its identifier, frequency, units, why it could help the capstone, and how you would retrieve it in Python.

### Suggested completion order

1. Set up imports and a date/configuration section.
2. Solve Question 1 and save the scraped table.
3. Build one reusable function for index downloads and period returns, then solve Question 2.
4. Implement and plot the running-high/drawdown logic for Question 3 before calculating percentiles.
5. Join earnings dates to prices and manually inspect several rows for Question 4.
6. Write the optional answers last, based on what the data made easy or difficult.
7. Run the notebook from a clean kernel and record the exact answers, assumptions, and retrieval date in the submission form.
