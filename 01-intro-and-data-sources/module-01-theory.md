# Module 1 theory — explained simply

## What Module 1 is about

Module 1 teaches the first part of a data-driven trading workflow:

1. Find the right financial or economic data.
2. Understand what each value means.
3. Download and inspect the data.
4. Calculate useful changes such as returns and growth rates.
5. Check that the result is not misleading.

Before building a trading model, you need to know what data you are using and how it was created.

## 1. Economic data and market data

### Economic data

Economic data describes the condition of an economy. Examples include:

- **GDP:** how much an economy produces.
- **CPI:** how prices are changing; it is commonly used to measure inflation.
- **Interest rates:** the cost of borrowing money.
- **Treasury yields:** interest rates paid by government bonds.
- **Oil prices:** an important cost for many businesses.
- **Volatility indexes:** how uncertain or nervous the market is.

The module mainly uses **FRED**, the Federal Reserve Economic Data platform. Each series has an identifier, such as:

- `GDPPOT`: potential GDP.
- `CPILFESL`: core CPI.
- `FEDFUNDS`: federal funds rate.

These series have different frequencies:

- GDP is usually quarterly.
- CPI is usually monthly.
- Some interest rates are daily or monthly.
- Stock prices are usually daily.

You must understand the frequency before comparing two series.

## 2. A number by itself is not enough

Suppose the S&P 500 is at 6,000. This is only a **level**. It does not tell you whether the market is performing well.

To understand performance, you need a **change**, for example:

- The index increased by 5% this year.
- It fell by 10% from its recent high.
- It is 20% higher than one year ago.

This is why financial analysis usually compares returns and growth rates rather than raw levels.

## 3. Growth rates

The basic percentage-change formula is:

```python
growth = current_value / previous_value - 1
```

If a value increases from 100 to 105:

```text
105 / 100 - 1 = 0.05 = 5%
```

### Year-over-year growth

To compare a value with the same period one year earlier, use the number of observations in one year:

```python
quarterly_yoy = gdp / gdp.shift(4) - 1
monthly_yoy = cpi / cpi.shift(12) - 1
daily_yoy = close / close.shift(252) - 1
```

The lag is:

- `4` for quarterly data because there are four quarters in a year.
- `12` for monthly data because there are twelve months in a year.
- Approximately `252` for daily stock data because there are about 252 trading days in a year.

The first values are missing because there is not enough previous data for comparison. That is expected. Do not replace them with zero.

## 4. Stock price data: OHLCV

Yahoo Finance provides daily market data. The main columns are:

- **Open:** price at the beginning of the trading session.
- **High:** highest price during the session.
- **Low:** lowest price during the session.
- **Close:** price at the end of the session.
- **Volume:** amount traded.
- **Dividends:** cash distributions paid to shareholders.
- **Stock splits:** changes to the number of shares.

The first five fields are known as **OHLCV**:

```text
Open, High, Low, Close, Volume
```

Example:

```python
import yfinance as yf

data = yf.Ticker("^GSPC").history(
    start="2020-01-01",
    end="2026-01-01",
)
```

The closing price is often used because it represents the final market price for the day.

## 5. Stocks, indexes, and ETFs

### Individual stock

```text
NVDA
```

This represents one company.

### Market index

```text
^GSPC
```

This represents the S&P 500 index, which tracks a group of large US companies.

Other examples include:

```text
^GDAXI  — German DAX
^N225   — Japanese Nikkei 225
^FTSE   — UK FTSE 100
^GSPTSE — Canadian TSX
```

### ETF

```text
VOO
```

VOO is an exchange-traded fund designed to track the S&P 500.

An index and an ETF may provide similar market exposure, but they are not identical:

- An index is a calculated benchmark.
- An ETF is an actual traded security.
- An ETF can pay dividends.
- An ETF charges management fees.
- They can have different prices, trading calendars, and histories.

## 6. Close price and adjusted price

When a company pays a dividend, its raw stock price can fall because money leaves the company and is paid to shareholders. Looking only at the raw closing price may therefore make the investor's total result look worse than it really was.

An adjusted price attempts to account for events such as:

- Dividends.
- Stock splits.
- Other corporate actions.

Adjusted prices are often more useful for long-term performance comparisons. Always document which price field you used.

The important rule is:

> Do not mix adjusted and unadjusted prices in one calculation.

## 7. Simple return

If an asset starts at \(P_0\) and ends at \(P_1\):

```python
return_value = P1 / P0 - 1
```

Example:

```text
Buy at 100
Sell at 110
Return = 110 / 100 - 1 = 10%
```

If the price falls to 90:

```text
Return = 90 / 100 - 1 = -10%
```

This calculation is used for YTD returns, monthly returns, yearly performance, and comparisons between indexes.

## 8. Drawdown

A drawdown measures how far an asset has fallen from its previous highest price.

If the price moves:

```text
100 → 120 → 108
```

The previous high is 120:

```text
Drawdown = 108 / 120 - 1 = -10%
```

The asset is therefore 10% below its previous peak.

In Python:

```python
running_high = close.cummax()
drawdown = close / running_high - 1
```

`cummax()` stores the highest value observed up to each date.

For Homework 1, a correction is an event where the drawdown reaches at least 5%.

Keep these concepts separate:

- **Drawdown:** the decline from a previous peak.
- **Correction:** a drawdown reaching a chosen threshold, such as 5%.
- **Bear market:** usually a much larger decline, often defined as approximately 20% or more.

## 9. Economic indicators and markets

The module compares economic indicators with market behavior. For example:

- Rising inflation can influence interest rates.
- Higher interest rates can make borrowing more expensive.
- Higher bond yields can make bonds more attractive compared with stocks.
- Higher oil prices can help energy companies but hurt companies with high fuel costs.
- Higher volatility often indicates greater market uncertainty.

The module does not say that one indicator automatically predicts prices. Relationships are complicated because:

- Markets anticipate future events.
- Several factors change at the same time.
- The same event can help one industry and hurt another.
- Economic data can be revised.
- Correlation does not prove causation.

## 10. APIs and web scraping

The module introduces several ways to obtain data:

- Yahoo Finance.
- FRED.
- Polygon.io.
- Alpha Vantage.
- Wikipedia tables.
- Company websites.
- EDGAR-derived financial reports.

An API gives structured data directly. Web scraping means downloading a webpage and extracting information from its HTML.

A basic scraping workflow is:

1. Send a request to the website.
2. Check the HTTP response.
3. Parse the HTML.
4. Find the required table or elements.
5. Convert the result into a DataFrame.
6. Check that the columns and values are correct.

Websites can change, block automated requests, or use different date formats. Always inspect scraped data instead of trusting it automatically.

## 11. Company financial data and earnings surprises

The module also introduces:

- Income statements.
- Balance sheets.
- Market capitalization.
- Earnings dates.
- Earnings surprises.

An earnings surprise measures the difference between reported earnings and analyst expectations.

Example:

```text
Expected EPS: 1.00
Reported EPS: 1.10
```

The company beat expectations. The stock may rise, but this is not guaranteed. Investors may already have expected the good result.

The reaction can also depend on:

- Future guidance.
- Revenue growth.
- Profit margins.
- Management comments.
- The overall market environment.
- Whether the result was already reflected in the share price.

## 12. Earnings reaction

For Homework 1, you examine Amazon earnings announcements:

1. Find the earnings announcement date.
2. Match it to the correct trading day.
3. Look at prices before and after the announcement.
4. Calculate the two-day reaction.
5. Compare the reaction with the earnings surprise.

For three consecutive closing prices:

```text
Day 1 → Day 2 → Day 3
```

The assignment uses:

```python
two_day_return = close_day_3 / close_day_1 - 1
```

Then ask whether larger positive earnings surprises tend to produce larger positive returns.

Correlation can describe the relationship, but it does not prove that earnings surprises caused the price movement.

## 13. Practical lessons to remember

### A price is not a return

A price of 500 does not mean an asset performed better than an asset priced at 100. Compare percentage returns.

### Frequency matters

Monthly CPI, quarterly GDP, and daily stock prices cannot be compared without deciding how to align them.

### Dates matter

Markets close on weekends and holidays. An economic release date may not match a trading date.

### Missing values matter

Missing values can occur because:

- The market was closed.
- A series did not exist yet.
- A shifted calculation needs earlier observations.
- An API failed to return data.

Do not automatically replace missing values with zero.

### Corporate actions matter

Dividends and stock splits can make raw prices misleading.

### Sources can disagree

Different providers may use different time zones, adjustments, trading calendars, and revision policies.

### Historical data can be revised

Macroeconomic data may be updated after its original release. Using today's revised history can create **look-ahead bias** if you are trying to reproduce what an investor knew at the time.

## The simplest summary

Module 1 answers this question:

> Given a financial or economic question, how do I obtain the correct data, transform it properly, and calculate a result I can trust?

The complete workflow is:

```text
Question
→ Data source
→ Download
→ Inspect
→ Clean
→ Calculate
→ Visualize
→ Check assumptions
→ Explain the result
```

