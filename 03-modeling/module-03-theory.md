# Module 3 theory — time series modeling

## What Module 3 is about

Module 3 moves from preparing market data to making predictions. The basic workflow is:

1. Define a target clearly.
2. Choose features that would have been known at the decision time.
3. Split the data in chronological order.
4. Start with simple hand rules as a baseline.
5. Try statistical or machine-learning models.
6. Evaluate predictions on later data.
7. Check whether the result is useful for a decision, not only whether it looks accurate.

A model that fits historical data is not automatically a useful trading model. Financial data changes over time, and the future must remain separate from the past during training and evaluation.

## 1. Features and targets

A **feature** is an input used to make a prediction. Examples from the course include:

- Previous returns such as `growth_1d` and `growth_30d`.
- Technical indicators such as RSI, CCI, MACD, ATR, and moving averages.
- Volatility and log volume.
- Macro indicators such as interest rates, CPI, GDP growth, and Treasury yields.
- Calendar information such as month, weekday, ticker, and ticker type.

A **target** is what the model tries to predict. Examples include:

```python
# Numeric target for regression
df["growth_future_30d"]

# Binary target for classification
df["is_positive_growth_30d_future"]
```

Future growth can be created with a negative shift:

```python
df["growth_future_30d"] = (
    df.groupby("Ticker")["Close"].shift(-30) / df["Close"]
)
```

This is valid as a target because it describes the outcome after the current row. It must not be used as a feature. Including it, or any information derived from it, creates **look-ahead bias**.

## 2. Preparing a modeling dataset

The Module 3 notebook starts with a combined daily dataset for many stocks. It separates columns into groups:

```python
GROWTH = [column for column in df.columns
          if column.startswith("growth_")
          and "future" not in column]

CATEGORICAL = ["Month", "Weekday", "Ticker", "ticker_type"]

TO_PREDICT = [column for column in df.columns
              if "future" in column]
```

This makes it easier to decide what belongs in the feature matrix and what belongs in the target.

When volume is heavily skewed, a logarithm can make it easier for a model to use:

```python
df["ln_volume"] = np.log(
    df["Volume"].replace(0, np.nan).fillna(1e-9)
)
```

The small replacement prevents `log(0)`. It is still important to understand how many zero or missing volume values were changed.

## 3. Categorical variables and dummy variables

Most models need numeric inputs. A category such as `Ticker` or `Weekday` cannot usually be passed directly as text. One-hot encoding creates a separate indicator column for each category:

```python
df["Weekday"] = df["Weekday"].astype(str)
df["Month"] = df["Month"].dt.month.astype(str)

dummies = pd.get_dummies(
    df[["Month", "Weekday", "Ticker", "ticker_type"]],
    dtype="int32",
)

df_with_dummies = pd.concat([df, dummies], axis=1)
```

For example, a weekday value can become columns such as `Weekday_0`, `Weekday_1`, and so on. Each row has a `1` for its category and `0` for the others.

Be careful with categories that only exist in one period. In a production workflow, the encoding used for new data must have the same columns as the encoding used during training.

## 4. Correlation is an initial check

Correlation can help identify variables worth investigating:

```python
columns = NUMERICAL + DUMMIES + TO_PREDICT
correlations = df_with_dummies[columns].corr()

future_corr = correlations["growth_future_30d"]
future_corr.sort_values().head()
future_corr.sort_values().tail()
```

Correlation is only a first approximation. It does not prove causation, does not automatically measure nonlinear relationships, and can be distorted by outliers or time trends. A feature with a high historical correlation can still fail on future data.

## 5. Temporal train, validation, and test splits

Randomly shuffling market observations can leak information from the future into the training set. A time-series split keeps the order:

```text
oldest data                    newest data
|----------- train -----------|-- validation --|---- test ----|
```

A simple date-based split can be created from the minimum and maximum dates:

```python
train_end = min_date + (max_date - min_date) * 0.70
val_end = train_end + (max_date - min_date) * 0.15

train = df[df["Date"] <= train_end]
validation = df[
    (df["Date"] > train_end) & (df["Date"] <= val_end)
]
test = df[df["Date"] > val_end]
```

The test set should be used at the end. Do not repeatedly adjust the model after looking at test performance; that turns the test set into another training set.

For one stock, the notebook also demonstrates an ordered 80/10/10 split with `.iloc`. The exact percentages matter less than preserving chronological order and clearly documenting the dates.

## 6. Inspect the target distributions

Before modeling, compare target distributions across train, validation, and test periods:

```python
df.groupby("split")["growth_future_30d"].describe()
```

Histograms are useful for spotting:

- Different market regimes.
- Outliers.
- Class imbalance.
- A test period that does not resemble training data.
- Missing or incorrectly calculated targets.

If the distributions change substantially, a model can lose accuracy even when the code is correct. This is a form of distribution shift.

## 7. Hand rules are useful baselines

A hand rule is a simple prediction built from domain knowledge. Examples include:

```python
new_df["pred_manual_cci"] = (new_df["cci"] > 200).astype(int)
new_df["pred_manual_growth"] = (new_df["growth_30d"] > 1).astype(int)
new_df["pred_manual_market"] = (
    (new_df["growth_30d"] > 1)
    & (new_df["growth_snp500_30d"] > 1)
).astype(int)
```

These rules are valuable because they provide a benchmark. A complicated model should beat a simple rule on the same untouched test period, after considering costs and risk.

A hand rule can be wrong and still be useful. The point is to measure its behavior rather than assume that an indicator automatically creates a profitable strategy.

## 8. Classification evaluation

For a binary target, compare the prediction with the actual result:

```python
new_df["is_correct"] = (
    new_df["prediction"]
    == new_df["is_positive_growth_30d_future"]
).astype(int)
```

If the strategy only acts when it predicts positive growth, **precision** is often more relevant than overall accuracy:

$$
\text{precision} =
\frac{\text{true positive predictions}}
{\text{all positive predictions}}
$$

In Pandas, restrict the calculation to the test period and predicted-positive rows:

```python
selected = (
    (new_df["split"] == "test")
    & (new_df["prediction"] == 1)
)
precision = new_df.loc[selected, "is_correct"].mean()
```

Also report the number of predictions. A strategy that makes two trades with 100% precision is not automatically better than one that makes thousands of trades with 55% precision.

Useful classification metrics can include precision, recall, F1 score, confusion matrix, and the positive class rate. For investing, connect the predictions to returns, fees, and position sizing as well.

## 9. Regression versus classification

### Regression

Regression predicts a numeric value such as a future growth factor or return. It can answer:

```text
How large might the future move be?
```

Common regression evaluation metrics include mean absolute error, root mean squared error, and rank correlation. Large outliers can strongly affect squared-error metrics.

### Classification

Classification predicts a category such as positive or non-positive growth. It can answer:

```text
Is the future growth likely to be positive?
```

Classification is easier to connect to a yes/no trading rule, but it loses information about the size of the return. A prediction of a 0.1% gain and a 30% gain can both be class `1`.

## 10. Time-series decomposition

A time series can be viewed as a combination of:

- **Trend:** long-term movement.
- **Seasonality:** a repeating pattern, such as a calendar effect.
- **Remainder:** variation not explained by trend or seasonality.

An additive model is often written as:

$$
 y_t = T_t + S_t + R_t
$$

A multiplicative model is:

$$
 y_t = T_t \times S_t \times R_t
$$

Decomposition can help explain a series, but it does not guarantee that the components will continue in the future. Financial prices are also usually non-stationary, so returns or growth factors may be more appropriate modeling targets than raw prices.

## 11. ARIMA models

ARIMA is a statistical time-series model using three parameters:

- `p`: autoregressive terms, using previous observations.
- `d`: differencing steps, used to make a series more stationary.
- `q`: moving-average terms, using previous errors.

The model uses the time series itself rather than technical and macro features. A typical setup is:

```python
df_arima = df_stock.set_index("Date")
train_validation = df_arima.loc[
    df_arima["split"].isin(["train", "validation"]),
    "Close",
]
test = df_arima.loc[
    df_arima["split"] == "test",
    "Close",
]
```

ARIMA parameters should be selected using training/validation data. The final test period is used only for the final evaluation. An automatic parameter search can be slow and may overfit if it is repeatedly judged on the test set.

## 12. Common modeling mistakes

- Randomly shuffling time-series rows before splitting.
- Using `growth_future_*` or a future-derived indicator as a feature.
- Fitting scalers, encoders, or thresholds on the complete dataset before the split.
- Choosing the best rule after examining test results.
- Reporting accuracy without a baseline or class balance.
- Ignoring the number of trades behind a precision result.
- Treating correlation as proof of a trading opportunity.
- Evaluating predictions without fees, slippage, liquidity, or position limits.
- Comparing models on different date ranges or different missing-value rules.

## 13. What to be able to explain after Module 3

You should be able to explain:

1. The difference between a feature and a target.
2. Why future-growth columns must be excluded from model inputs.
3. Why one-hot encoding is needed for categorical variables.
4. Why temporal train/validation/test splits are required for market data.
5. How a hand rule provides a useful baseline.
6. Why precision depends on the condition under which predictions are selected.
7. The difference between regression and binary classification.
8. What trend, seasonality, remainder, and ARIMA parameters mean.
9. Why good historical performance does not guarantee future profitability.
