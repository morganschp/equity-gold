# Global Equity and Gold Backtest

Explore how the gold weight and the emerging-markets share of equities affect a global portfolio over January 2015 to December 2025. The allocation bar shows the target holdings per $100. The charts show the growth of $1 after trading costs and daily losses from previous peaks.

| Default allocation | Developed equities (URTH) | Emerging equities (IEMG) | Gold (GLD) | Treasuries (SHY) |
| --- | ---: | ---: | ---: | ---: |
| Gold | 81% | 9% | 10% | 0% |
| Equity | 90% | 10% | 0% | 0% |
| Treasury | 81% | 9% | 0% | 10% |

Both sliders start at 10%. All three portfolios use the selected developed/emerging split within equities. Treasury invests the same percentage in SHY that Gold invests in GLD.

## Run locally

Use Python 3.12. From the repository root, run:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Streamlit Community Cloud

Select repository `morganschp/equity-gold`, branch `main`, and entry point `app.py`. Choose Python 3.12 in Advanced settings. Dependencies and the theme are included. The first run needs internet access to Yahoo Finance.

## Prices and calculations

The app downloads daily USD closing prices adjusted for splits and distributions with yfinance. It verifies that all five funds have positive, finite prices for each of the 2,767 NYSE closes from 31 December 2014 through 31 December 2025. Streamlit caches the validated prices for 24 hours across sessions. Changing a weight reuses that download. If Yahoo supplies an incomplete history, the app offers a retry.

The portfolios start with $1 and rebalance at the last close of each quarter. The model charges 0.10% per dollar bought or sold, and calculates target holdings after deducting fees. The new positions earn the following trading day’s return. The performance measures use month-end returns, including BIL as the cash proxy, while drawdowns use daily closes.

## Colab reference results

At the default weights, the saved notebook reports:

| 2015–2025 | Ending value of $10,000 | Avg. return/yr | CAGR | Volatility/yr | Sharpe | Max drawdown |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Gold | $31,307.05 | 11.29% | 10.93% | 13.23% | 0.72 | −30.63% |
| Equity | $30,398.93 | 11.19% | 10.64% | 14.47% | 0.65 | −33.86% |
| Treasury | $28,028.27 | 10.25% | 9.82% | 13.03% | 0.65 | −30.34% |

Gold’s annualized alpha versus Equity was 0.96%, beta was 0.908, and the annualized information ratio was 0.049. Yahoo may revise historical adjusted prices between downloads, which can change the last cents of ending wealth.
