# Module 4 theory — trading strategy simulations

## What Module 4 is about

Module 4 connects model predictions to simulated trading results. A prediction by
itself is not a strategy. A strategy must define:

1. When to enter a position.
2. What to buy or sell.
3. How much capital to allocate.
4. When to exit.
5. How fees, slippage, and liquidity affect the result.
6. How profit, risk, and portfolio value are measured.

The key question changes from:

```text
Was the prediction correct?
```

to:

```text
What would have happened if I had traded on that prediction?
```

A simulation is still only a model of reality. Good results can disappear when
trading costs, delayed execution, position limits, or market impact are included.

## 1. From predictions to trades

The Module 3 predictions can be used as trading signals. For example:

```python
signal = new_df["pred5_clf_10"] == 1
```

A signal is not automatically an order. Define a trading rule explicitly:

- A positive prediction may open a long position.
- A negative prediction may mean no trade, or it may open a short position.
- The position may be held for a fixed number of days or until an exit condition.
- A position may be closed when the prediction changes.

A simple long-only rule can be represented as:

```python
position = signal.astype(int)
```

For a one-period strategy return, a signal known at time $t$ must be multiplied
by a return that occurs after $t$:

```python
strategy_return = position * future_return
```

Never use the closing price or prediction from the end of a period to assume an
execution at the beginning of that same period. That creates look-ahead bias.

## 2. Timing and execution assumptions

The simulation must state when information becomes available and when the trade
is executed. Common choices are:

- Generate a signal after the close and trade at the next day's open.
- Generate a signal after the close and trade at the next day's close.
- Generate a signal before the close and trade at that close, if the data was
  actually available before the close.

A practical one-day lag is:

```python
next_day_return = close.shift(-1) / close - 1
strategy_return = signal.astype(int) * next_day_return
```

The exact formula depends on the price used for entry and exit. Document whether
the simulation uses `Open`, `Close`, or an adjusted price, and use the same
convention for every asset.

## 3. Position sizing

Position sizing determines how much money each signal controls. Examples include:

### Fixed amount

Invest the same amount in every trade:

```python
capital_per_trade = 1000
profit = capital_per_trade * strategy_return
```

This is easy to understand, but many simultaneous signals may require more cash
than the portfolio has.

### Equal-weight portfolio

If $N$ assets have active signals, allocate:

$$
\text{weight}_i = \frac{1}{N}
$$

for each active asset. Rebalance when signals change or at a fixed schedule.

### Volatility-aware sizing

Give smaller positions to more volatile assets. A basic version is:

$$
\text{raw weight}_i = \frac{1}{\text{volatility}_i}
$$

Then normalize the weights so their absolute sum is one. Add maximum position
limits so one unusually stable or incorrectly measured asset cannot dominate the
portfolio.

## 4. Long, short, and market-neutral strategies

### Long-only

Buy assets with positive signals and hold cash otherwise. The portfolio exposure
is between zero and one if weights are normalized.

### Long-short

Buy assets with positive signals and short assets with negative signals. A simple
market-neutral version gives equal total long and short exposure:

```text
long exposure  = +50%
short exposure = -50%
net exposure   = 0%
```

Shorting introduces borrowing costs, margin requirements, borrow availability,
and potentially unlimited losses. A backtest must include these assumptions.

### Market-relative strategies

A signal can be applied to the asset's return relative to a benchmark. This helps
separate a stock-specific prediction from a broad market move, but it does not
remove all portfolio risk.

## 5. Transaction costs and slippage

Every change in position can create costs. A simple proportional cost model is:

```python
turnover = abs(position.diff()).fillna(abs(position))
cost = turnover * fee_rate
net_strategy_return = gross_strategy_return - cost
```

For a portfolio, turnover is usually the sum of absolute changes in weights:

$$
\text{turnover}_t = \sum_i |w_{i,t} - w_{i,t-1}|
$$

Include both entry and exit costs when the position changes. Slippage can be
modeled as an additional percentage or as a function of volume and spread.

A strategy that is profitable before costs but negative after costs is not
profitable in the stated market conditions.

## 6. Portfolio value and compounding

Daily strategy returns can be compounded into an equity curve:

```python
portfolio_value = initial_capital * (1 + net_strategy_return).cumprod()
```

For a starting capital of $10,000, a return of 2% followed by -1% produces:

$$
10{,}000 \times 1.02 \times 0.99 = 10{,}098
$$

Do not add percentage returns directly when returns are compounded. The product
of growth factors determines the portfolio value.

Useful outputs include:

- Final portfolio value.
- Total return.
- Annualized return.
- Daily or monthly volatility.
- Maximum drawdown.
- Sharpe ratio.
- Number of trades.
- Average profit per trade.
- Win rate and average win/loss.

## 7. Drawdown and risk

For an equity curve $V_t$, the running peak and drawdown are:

```python
running_peak = portfolio_value.cummax()
drawdown = portfolio_value / running_peak - 1
maximum_drawdown = drawdown.min()
```

Maximum drawdown measures the largest decline from a previous portfolio high. It
is different from volatility: a strategy can have moderate daily volatility and
still experience a long drawdown.

A strategy comparison should include both return and risk. A higher final value
is not automatically better if it required much larger drawdowns or leverage.

## 8. Sharpe ratio for a strategy

A simplified annualized Sharpe ratio is:

$$
\text{Sharpe} =
\frac{\overline{r} - r_f}{\sigma_r}\sqrt{252}
$$

where:

- $\overline{r}$ is the average daily strategy return.
- $r_f$ is the daily risk-free rate, or a consistently defined annual rate.
- $\sigma_r$ is daily return volatility.
- $252$ is an approximate number of trading days per year.

Use a consistent risk-free-rate convention. Subtracting an annual rate from a
daily return without conversion produces a misleading result.

Sharpe ratio is sensitive to the sample period, outliers, non-normal returns, and
serial correlation. Report it together with the equity curve and drawdown.

## 9. Backtesting with train, validation, and test periods

Keep the chronological split from Module 3:

```text
oldest data                    newest data
|----------- train -----------|-- validation --|---- test ----|
```

Use the training period to fit the model or define thresholds. Use validation to
choose among reasonable strategy settings. Use the test period once for final
evaluation.

Do not select the best holding period, cost assumption, indicator threshold, or
model after repeatedly inspecting test performance. That turns the test period
into part of the strategy design and overstates expected performance.

## 10. Common strategy examples

### Single-stock investment

Buy and hold one asset for a defined period. This is a useful baseline because
many active strategies should be compared with simply holding the benchmark.

### Diversified long portfolio

Rank assets by predicted return, buy the top group, and rebalance on a schedule.
Important choices include the number of holdings, equal or risk-adjusted weights,
turnover limits, and benchmark.

### Long-short portfolio

Long the strongest predictions and short the weakest predictions. Keep track of
gross exposure, net exposure, leverage, short costs, and whether the assets can
actually be borrowed.

### Mean reversion

Trade after an unusually large move with the expectation that price will move
back toward a reference value. Define the entry threshold, holding period, exit
rule, and maximum loss before evaluating the idea.

### Event or technical strategy

Use an event such as earnings, an RSI threshold, or a moving-average crossover.
The event timestamp and the earliest tradable price are essential. Do not trade
on a value that was only published after the assumed entry.

## 11. A minimum simulation checklist

Before trusting a backtest, check:

1. Signal timing and the execution price.
2. The exact return formula and price adjustment choice.
3. Whether future information enters the signal.
4. Position size and total capital required.
5. Fees, spread, slippage, and shorting costs.
6. Missing prices, delisted assets, and survivorship bias.
7. Portfolio turnover and number of trades.
8. Compounded portfolio value and maximum drawdown.
9. Comparison with a passive benchmark and a simple baseline.
10. Results on an untouched test period.

## 12. What to be able to explain after Module 4

You should be able to explain:

1. How a prediction becomes an entry and exit rule.
2. Why signal timing matters for avoiding look-ahead bias.
3. The difference between fixed-amount, equal-weight, and volatility-aware sizing.
4. How turnover creates transaction costs.
5. How daily strategy returns become a compounded equity curve.
6. Why maximum drawdown should be reported with total return.
7. How long-only, long-short, and market-neutral exposure differ.
8. Why a backtest must be compared with a baseline and evaluated out of sample.
