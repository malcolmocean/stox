# Stox — Stock Analysis Dashboard

A web app that shows a stock's trade setup (buy, stop loss, take profit) alongside an interactive candlestick chart with technical analysis.

Enter a ticker symbol and get a split-screen view: key numbers on the left, chart on the right.

## Quick Start

Requires Python 3.11+.

```
./run.sh
```

That's it. On first run it sets up a virtual environment and installs dependencies. Then it starts the app at **http://localhost:5000**.

## What It Shows

**Left panel:**
- Current price and daily change
- Trade setup: buy price, stop loss, take profit, risk/reward ratio
- Signal that triggered the buy (e.g. "Golden Cross", "Bullish Engulfing")

**Right panel — interactive chart:**
- 6 months of daily candlesticks
- 50-day and 200-day moving average lines
- Volume bars
- Buy/sell signal markers
- Horizontal lines for trade levels

## How It Works

- Fetches daily OHLCV data from Yahoo Finance via `yfinance`
- Detects candlestick patterns (hammer, engulfing, doji, morning/evening star, shooting star)
- Detects moving average crossovers (golden cross / death cross)
- Computes stop loss from the most recent swing low (or 5% default)
- Take profit at a 2:1 reward-to-risk ratio
- Chart rendered with Plotly
