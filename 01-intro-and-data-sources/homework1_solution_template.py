# %% [markdown]
# Module 1 Homework 1 — runnable solution template
#
# Run this file as notebook cells in Jupyter/VS Code, or copy the cells into
# homework1.ipynb. The printed tables and answers are the values to submit.
# Data from Yahoo Finance and Wikipedia can change, so record the run date.

# %%
# If needed, run once in a notebook:
# %pip install -q pandas numpy requests yfinance lxml

from datetime import date
import numpy as np
import pandas as pd
import requests
import yfinance as yf

pd.set_option("display.max_columns", 30)
pd.set_option("display.float_format", lambda value: f"{value:,.4f}")

AS_OF = pd.Timestamp("2026-08-21")


def close_series(ticker, start, end):
    """Download one index/security and return a clean daily Close Series."""
    data = yf.download(
        ticker,
        start=pd.Timestamp(start).strftime("%Y-%m-%d"),
        # yfinance's end date is exclusive, so add one day for an inclusive end.
        end=(pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
        auto_adjust=False,
        progress=False,
    )
    if data.empty:
        raise ValueError(f"No data returned for {ticker}")
    close = data["Close"]
    if isinstance(close, pd.DataFrame):  # compatible with recent yfinance versions
        close = close.iloc[:, 0]
    close = close.dropna().sort_index()
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close


def period_return(ticker, start, end):
    close = close_series(ticker, start, end)
    return close.iloc[-1] / close.iloc[0] - 1


# %% [markdown]
# ## Question 1 — S&P 500 stocks added to the index

# %%
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
headers = {"User-Agent": "Mozilla/5.0 (compatible; SMA-Zoomcamp/2026)"}
response = requests.get(url, headers=headers, timeout=30)
response.raise_for_status()

tables = pd.read_html(response.text)
sp500 = tables[0].copy()
sp500.columns = [str(column).strip() for column in sp500.columns]
sp500 = sp500.rename(
    columns={
        "Symbol": "ticker",
        "Security": "company",
        "Date added": "date_added",
    }
)
sp500["date_added"] = pd.to_datetime(sp500["date_added"], errors="coerce")
sp500["addition_year"] = sp500["date_added"].dt.year

additions_since_2020 = (
    sp500.loc[sp500["addition_year"].ge(2020), "addition_year"]
    .value_counts()
    .sort_index()
    .rename_axis("year")
    .rename("additions")
    .to_frame()
)
print(additions_since_2020)
print(
    "Q1 answer — year with most additions since 2020:",
    additions_since_2020["additions"].idxmax(),
)

# "More than 20 years" means added before the date 20 years before today.
twenty_year_cutoff = pd.Timestamp.today().normalize() - pd.DateOffset(years=20)
print(
    "Additional — current constituents added more than 20 years ago:",
    int(sp500["date_added"].lt(twenty_year_cutoff).sum()),
)

# %% [markdown]
# ## Question 2 — YTD returns for world indexes
#
# The assignment lists 11 indexes (the question says "out of 10", but the list
# contains 11). This uses the first available close on/after January 1 and the
# last available close on/before August 21 for every ticker.

# %%
tickers = {
    "United States S&P 500": "^GSPC",
    "China Shanghai Composite": "000001.SS",
    "Hong Kong Hang Seng": "^HSI",
    "Australia ASX 200": "^AXJO",
    "India Nifty 50": "^NSEI",
    "Canada TSX Composite": "^GSPTSE",
    "Germany DAX": "^GDAXI",
    "United Kingdom FTSE 100": "^FTSE",
    "Japan Nikkei 225": "^N225",
    "Mexico IPC Mexico": "^MXX",
    "Brazil Ibovespa": "^BVSP",
}

ytd_rows = []
for name, ticker in tickers.items():
    close = close_series(ticker, "2026-01-01", AS_OF)
    ytd_rows.append(
        {
            "index": name,
            "ticker": ticker,
            "first_date": close.index[0],
            "last_date": close.index[-1],
            "start_close": close.iloc[0],
            "end_close": close.iloc[-1],
            "ytd_return": close.iloc[-1] / close.iloc[0] - 1,
        }
    )

ytd = pd.DataFrame(ytd_rows).sort_values("ytd_return", ascending=False)
us_return = ytd.loc[ytd["ticker"].eq("^GSPC"), "ytd_return"].iloc[0]
ytd["better_than_us"] = ytd["ytd_return"] > us_return
print(ytd)
print("Q2 answer — US S&P 500 YTD return:", us_return)
print("Q2 answer — indexes better than S&P 500:", int(ytd["better_than_us"].sum()))

# Additional: compare performance over 3, 5, and 10 years ending on AS_OF.
periods = {"3_year": AS_OF - pd.DateOffset(years=3),
           "5_year": AS_OF - pd.DateOffset(years=5),
           "10_year": AS_OF - pd.DateOffset(years=10)}
long_term = []
for period_name, start in periods.items():
    for name, ticker in tickers.items():
        long_term.append(
            {
                "period": period_name,
                "index": name,
                "ticker": ticker,
                "return": period_return(ticker, start, AS_OF),
            }
        )
long_term = pd.DataFrame(long_term)
us_long_term = long_term[long_term["ticker"].eq("^GSPC")].set_index("period")["return"]
long_term["better_than_us"] = long_term.apply(
    lambda row: row["return"] > us_long_term.loc[row["period"]], axis=1
)
print(long_term.pivot(index="index", columns="period", values="return"))
print(long_term.groupby("period")["better_than_us"].sum())

# %% [markdown]
# ## Question 3 — S&P 500 corrections
#
# A correction is represented as one drawdown episode: it starts after a
# previous all-time high and ends when the index reaches a new high. Duration
# below is calendar days from the peak to the trough.

# %%
spx = close_series("^GSPC", "1950-01-01", AS_OF).rename("close").to_frame()
spx["running_high"] = spx["close"].cummax()
spx["drawdown"] = spx["close"] / spx["running_high"] - 1
spx["in_drawdown"] = spx["drawdown"] < 0

# A new group begins whenever the market switches between recovery and decline.
spx["episode"] = spx["in_drawdown"].ne(spx["in_drawdown"].shift()).cumsum()
corrections = []
for _, episode in spx[spx["in_drawdown"]].groupby("episode"):
    trough_date = episode["close"].idxmin()
    before_episode = spx.loc[:episode.index[0]].iloc[:-1]
    peak_close = before_episode["running_high"].iloc[-1]
    peak_date = before_episode.index[before_episode["close"].eq(peak_close)][-1]
    trough_close = episode.loc[trough_date, "close"]
    episode_end_position = spx.index.get_loc(episode.index[-1])
    recovery_date = (
        spx.index[episode_end_position + 1]
        if episode_end_position + 1 < len(spx)
        else pd.NaT
    )
    corrections.append(
        {
            "peak_date": peak_date,
            "trough_date": trough_date,
            "recovery_date": recovery_date,
            "peak_close": peak_close,
            "trough_close": trough_close,
            "drawdown": trough_close / peak_close - 1,
            "duration_calendar_days": (trough_date - peak_date).days,
        }
    )

corrections = pd.DataFrame(corrections)
corrections = corrections[corrections["drawdown"] <= -0.05].copy()
corrections = corrections.sort_values("drawdown")
print(corrections.head(10))
print(
    "Q3 answer — drawdown percentiles:",
    corrections["drawdown"].abs().quantile([0.25, 0.50, 0.75]).to_dict(),
)
print(
    "Q3 answer — duration percentiles:",
    corrections["duration_calendar_days"].quantile([0.25, 0.50, 0.75]).to_dict(),
)

# %% [markdown]
# ## Question 4 — Amazon earnings surprises

# %%
amazon = yf.Ticker("AMZN")
earnings = amazon.get_earnings_dates().reset_index()
earnings = earnings.rename(columns={earnings.columns[0]: "earnings_date"})
earnings["earnings_date"] = pd.to_datetime(earnings["earnings_date"]).dt.tz_localize(None)
earnings["Surprise %"] = pd.to_numeric(earnings["Surprise %"], errors="coerce")
earnings = earnings.dropna(subset=["Surprise %"]).copy()

amzn_close = close_series("AMZN", "2019-01-01", pd.Timestamp.today()).rename("close")
events = []
for _, row in earnings.iterrows():
    announcement_date = row["earnings_date"].normalize()
    # Use the announcement date if it is a trading day; otherwise use the next one.
    announcement_position = amzn_close.index.searchsorted(announcement_date, side="left")
    if announcement_position < 1 or announcement_position + 1 >= len(amzn_close):
        continue
    day1 = amzn_close.index[announcement_position - 1]
    day2 = amzn_close.index[announcement_position]
    day3 = amzn_close.index[announcement_position + 1]
    events.append(
        {
            "earnings_date": row["earnings_date"],
            "trading_day": day2,
            "surprise_pct": row["Surprise %"],
            "two_day_return": amzn_close.loc[day3] / amzn_close.loc[day1] - 1,
        }
    )

events = pd.DataFrame(events).drop_duplicates("earnings_date")
positive = events[events["surprise_pct"] > 0].copy()
print(events.sort_values("earnings_date", ascending=False))
print("Q4 answer — positive-surprise median two-day return:",
      positive["two_day_return"].median())
print("Q4 answer — surprise/return correlation:",
      positive[["surprise_pct", "two_day_return"]].corr().loc[
          "surprise_pct", "two_day_return"
      ])

# %% [markdown]
# ## Optional Question 5 — capstone idea
#
# Replace this example with your own project idea in the homework form.

# %%
capstone_idea = """
I want to test whether macroeconomic conditions and market momentum can help
predict the one-month forward return of a diversified ETF. I will combine
price-based features (momentum, volatility, drawdown) with FRED indicators
(inflation, interest rates, and unemployment). I will use a time-ordered
train/validation/test split and compare the model with a buy-and-hold
benchmark, including transaction costs.
"""
print(capstone_idea)

# %% [markdown]
# ## Optional Question 6 — additional metrics
#
# Example metrics to investigate:
#
# - `DFF` (FRED): daily effective federal funds rate; useful for rate-regime features.
# - `VIXCLS` (FRED): daily VIX close; useful as a market-stress feature.
# - `DCOILWTICO` (FRED): daily WTI oil price; useful for inflation and sector analysis.
#
# For each metric, record its source ID, frequency, units, reason for using it,
# and the Python request that retrieves it.
