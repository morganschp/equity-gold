"""Global Equity and Gold Backtest, adapted from the Group DE Colab notebook."""

import exchange_calendars as calendars
import numpy as np
import pandas as pd
import yfinance as yf

SYMBOLS = ["URTH", "IEMG", "GLD", "SHY", "BIL"]
START = "2014-12-31"
END = "2025-12-31"


def validate_prices(closes):
    prices = closes.loc[START:END, SYMBOLS].copy()
    sessions = calendars.get_calendar("XNYS", start=START, end=END).sessions
    if not prices.index.equals(sessions):
        raise ValueError("Dates must match every NYSE trading close in the backtest.")
    if not np.isfinite(prices).all().all() or (prices <= 0).any().any():
        raise ValueError("Each ETF must have a positive adjusted close on every trading day.")
    return prices


def download_prices():
    data = yf.download(SYMBOLS, start="2014-12-01", end="2026-01-01", interval="1d",
                       auto_adjust=True, progress=False, threads=False, timeout=20)
    closes = data["Close"].reindex(columns=SYMBOLS).sort_index()
    return validate_prices(closes)


def portfolio_weights(gold_percent, em_percent):
    defensive = gold_percent / 100
    em_share = em_percent / 100
    equity = 1 - defensive
    return pd.DataFrame({
        "Gold": [equity * (1 - em_share), equity * em_share, defensive, 0],
        "Equity": [1 - em_share, em_share, 0, 0],
        "Treasury": [equity * (1 - em_share), equity * em_share, 0, defensive],
    }, index=pd.Index(SYMBOLS[:4], name="Holding"))


def trade_to_target(before, target, fee_rate):
    gross_value = before.sum()
    net_value = gross_value
    for attempt in range(20):
        trades = target * net_value - before
        next_value = gross_value - fee_rate * trades.abs().sum()
        if abs(next_value - net_value) < 1e-12:
            break
        net_value = next_value

    after = target * next_value
    trades = after - before
    fees = fee_rate * trades.abs()
    assert abs(trades.sum() + fees.sum()) < 1e-11
    assert np.allclose(after / after.sum(), target)
    return after, trades, fees


def backtest(prices, quarter_ends, target, fee_rate):
    holdings = target.copy()                  # $1 invested, no opening fee
    start = prices.index[0]
    wealth = pd.Series(index=prices.index, dtype=float)
    wealth.loc[start] = holdings.sum()
    ledger = {}
    for end in quarter_ends:
        quarter_prices = prices.loc[start:end, target.index]
        marked = quarter_prices.div(quarter_prices.iloc[0]).mul(holdings)
        wealth.loc[marked.index[1:]] = marked.sum(axis=1).iloc[1:]
        before = marked.iloc[-1]
        holdings, trades, fees = trade_to_target(before, target, fee_rate)
        wealth.loc[end] = holdings.sum()
        ledger[end] = pd.DataFrame({"Before": before, "Trade": trades,
                                    "Fee": fees, "After": holdings})
        start = end
    assert wealth.notna().all() and (wealth > 0).all()
    return wealth, ledger


def simulate(prices, weights, end_year):
    prices = prices.loc[:f"{end_year}-12-31"]
    dates = prices.index.to_series()
    quarter_ends = dates.groupby(prices.index.to_period("Q")).last().iloc[1:]
    wealth = pd.DataFrame(index=prices.index)
    for name in weights:
        wealth[name], _ = backtest(prices, quarter_ends, weights[name], 10 / 10_000)

    drawdowns = wealth / wealth.cummax() - 1
    month_ends = dates.groupby(prices.index.to_period("M")).last()
    monthly = wealth.loc[month_ends].pct_change().iloc[1:]
    cash = prices.loc[month_ends, "BIL"].pct_change().iloc[1:]
    excess = monthly.sub(cash, axis=0)
    summary = pd.DataFrame({
        "Ending value of $10,000": 10_000 * wealth.iloc[-1],
        "Average return (%/yr)": 100 * 12 * monthly.mean(),
        "CAGR (%/yr)": 100 * (wealth.iloc[-1] ** (12 / len(monthly)) - 1),
        "Volatility (%/yr)": 100 * np.sqrt(12) * monthly.std(),
        "Sharpe ratio": np.sqrt(12) * excess.mean() / excess.std(),
        "Max drawdown (%)": 100 * drawdowns.min(),
    })
    beta = excess["Gold"].cov(excess["Equity"]) / excess["Equity"].var()
    alpha = 12 * (excess["Gold"].mean() - beta * excess["Equity"].mean())
    active = monthly["Gold"] - monthly["Equity"]
    tracking_error = active.std()
    information_ratio = np.sqrt(12) * active.mean() / tracking_error if tracking_error > 0 else np.nan
    return wealth, drawdowns, summary, (alpha, beta, information_ratio)
