import threading

from matplotlib import style
import numpy as np
import streamlit as st
from matplotlib.figure import Figure

from backtest import download_prices, portfolio_weights, simulate

st.set_page_config(page_title="Global Equity and Gold Backtest", layout="centered")

GOLD_BLUE = "#1f77b4"
EQUITY_ORANGE = "#ff7f0e"
TREASURY_GREEN = "#2ca02c"


def allocation_bar(target):
    dollars = 100 * target
    striped_orange = (
        f"repeating-linear-gradient(135deg, {EQUITY_ORANGE} 0 4px, #783b08 4px 6px)"
    )
    holdings = [
        ("URTH", "Developed equities", EQUITY_ORANGE),
        ("IEMG", "Emerging equities", striped_orange),
        ("GLD", "Gold", GOLD_BLUE),
    ]
    segments = []
    labels = []
    for ticker, name, fill in holdings:
        amount = f"{dollars[ticker]:.2f}".rstrip("0").rstrip(".")
        segments.append(f'<span style="width:{dollars[ticker]:.4f}%;background:{fill}"></span>')
        labels.append(
            f'<span><i aria-hidden="true" style="display:inline-block;width:.8em;height:.8em;'
            f'background:{fill};margin-right:.35em"></i>{name} ({ticker}) <b>${amount}</b></span>'
        )

    st.markdown("**Target allocation per $100**")
    st.html(
        '<div aria-hidden="true" style="display:flex;height:22px;border-radius:4px;overflow:hidden">'
        + "".join(segments) + '</div>'
        + '<div style="display:flex;flex-wrap:wrap;gap:.25rem 1.2rem;margin-top:.45rem;font-size:.9rem">'
        + "".join(labels) + '</div>'
    )


@st.cache_data(ttl=86400, show_spinner="Downloading adjusted prices from Yahoo Finance…")
def cached_prices():
    return download_prices()


@st.cache_data(max_entries=32, show_spinner=False)
def scenario(prices, gold_percent, em_percent):
    weights = portfolio_weights(gold_percent, em_percent)
    return weights, *simulate(prices, weights, 2025)


@st.cache_resource
def plot_lock():
    return threading.Lock()


def chart(series, title, ylabel):
    # The Colab notebook uses pandas plotting with the default Matplotlib style.
    with plot_lock(), style.context("default"):
        figure = Figure(figsize=(9, 4), facecolor="white")
        axis = figure.subplots()
        series.plot(ax=axis, title=title, ylabel=ylabel, xlabel="Date",
                    color=[GOLD_BLUE, EQUITY_ORANGE, TREASURY_GREEN])
        st.pyplot(figure, width="stretch")


st.title("Global Equity and Gold Backtest")
st.write("Compare gold with an all-equity portfolio and with the same weight in short-term US Treasuries.")

gold_control, em_control = st.columns(2)
gold = gold_control.slider("Gold share of total portfolio", 0, 100, 10, format="%d%%",
                           help="The Treasury benchmark puts this same percentage in SHY.")
em = em_control.slider("Emerging markets’ share of equities", 0, 100, 10, format="%d%%",
                       help="All three portfolios put this share of their equity allocation in IEMG and the rest in URTH.")

try:
    prices = cached_prices()
except Exception:
    st.error("A complete Yahoo Finance price history is unavailable. Please try the download again.")
    st.button("Retry download")
    st.stop()

weights, wealth, drawdowns, summary, relative = scenario(prices, gold, em)
allocation_bar(weights["Gold"])
st.caption("January 2015 – December 2025 · Quarterly rebalancing · 0.10% per dollar bought or sold")
chart(wealth, "Growth of $1 after trading costs", "Portfolio value (USD)")
chart(100 * drawdowns, "Loss from the previous peak", "Drawdown (%)")

st.subheader("Performance")
st.table(summary.T.style.format(lambda value: f"{value:,.2f}").format(
    "${:,.2f}", subset=(["Ending value of $10,000"], summary.index)))
alpha, beta, information_ratio = relative
ratio_text = f"{information_ratio:.3f}" if np.isfinite(information_ratio) else "undefined (identical returns)"
st.caption(f"Gold relative to Equity · Annualized alpha {alpha:.2%} · Beta {beta:.3f} · Annualized information ratio {ratio_text}")

with st.expander("Target weights and calculation assumptions"):
    st.table(weights.style.format("{:.2%}"))
    st.write("URTH holds developed-market equities and IEMG holds emerging-market equities. "
             "Gold allocates the balance to GLD, and Treasury allocates it to SHY. "
             "Equity invests entirely in the two stock funds.")
    st.write("Each portfolio begins with $1 at the close of 31 December 2014. Holdings drift "
             "until the last trading close of each quarter. Sales cover purchases and fees. "
             "The new holdings earn the next trading day’s return.")
    st.write("The app uses daily USD prices from Yahoo Finance adjusted for splits and distributions. "
             "Drawdowns use daily closes. Annualized statistics use month-end returns, with BIL "
             "as the cash proxy for Sharpe, alpha and beta.")
