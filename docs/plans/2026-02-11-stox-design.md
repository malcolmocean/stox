# Stox — Stock Analysis Dashboard

## Overview

A single-page Flask web app that shows a stock's trade setup (initial buy, stop loss, take profit) alongside an interactive candlestick chart with technical analysis markings. User enters a ticker symbol, gets a split-screen view: numbers on the left, chart on the right.

## Architecture

**Backend** (`app.py`): Flask server that takes a ticker symbol, fetches 6 months of daily data via `yfinance`, runs technical analysis (MA crossovers + candlestick pattern detection), and computes stop loss / take profit levels.

**Frontend** (`index.html` + `style.css`): Single HTML page with a split layout. Left panel (~30% width) shows key numbers in a card layout. Right panel (~70% width) shows an interactive Plotly candlestick chart with buy/sell markers overlaid.

### Data Flow

1. User types ticker in search bar, hits enter
2. Flask fetches 6 months of daily OHLCV data from Yahoo Finance
3. Backend computes: 50/200-day MAs, candlestick patterns (hammer, engulfing, doji, morning star), most recent buy signal price, stop loss, and take profit
4. Returns everything to the frontend — numbers populate the left panel, Plotly chart renders on the right

### Stop Loss & Take Profit Logic

- **Initial buy**: Most recent buy signal price (from MA crossover or bullish candle pattern)
- **Stop loss**: Most recent swing low (local minimum) below the buy price, or a default 5% below buy
- **Take profit**: 2:1 reward-to-risk ratio based on the stop loss distance

## Left Panel — Key Numbers

Card-style layout, color coded (green for buy/take profit, red for stop loss).

**Stock Info:**
- Ticker symbol & company name
- Current price & daily change (% and $)

**Trade Setup:**
- Initial Buy price
- Stop Loss price
- Take Profit price
- Risk/Reward Ratio (e.g. "1:2")

**Signal Info:**
- Signal type that triggered the buy (e.g. "Golden Cross" or "Bullish Engulfing")
- Date of the signal

If no buy signal exists in the 6-month window, display "No active buy signal."

## Right Panel — Candlestick Chart

Interactive Plotly candlestick chart showing 6 months of daily data.

**Chart elements:**
- Standard OHLC candlesticks (green = up, red = down)
- 50-day MA line (blue)
- 200-day MA line (orange)
- Volume bars along the bottom (subtle, semi-transparent)

**Markers & annotations:**
- Buy signals: Green upward triangle markers at the triggering candle
- Sell signals: Red downward triangle markers for bearish signals
- Horizontal dashed lines for: Initial Buy (green), Stop Loss (red), Take Profit (blue)

**Interactivity (built into Plotly):**
- Hover to see OHLC values for any candle
- Zoom and pan with mouse
- Double-click to reset view

## Candlestick Pattern Detection

Using `pandas-ta` for pattern detection.

**Bullish (buy signals):**
- Hammer — Small body, long lower wick at bottom of downtrend
- Bullish Engulfing — Green candle fully engulfs previous red candle
- Morning Star — Three-candle reversal pattern at a low
- Doji — Indecision candle at support

**Bearish (sell signals):**
- Shooting Star — Small body, long upper wick at top of uptrend
- Bearish Engulfing — Red candle fully engulfs previous green candle
- Evening Star — Three-candle reversal at a high

**Moving average crossovers:**
- Golden Cross (50 MA crosses above 200 MA) = strong buy
- Death Cross (50 MA crosses below 200 MA) = strong sell

## Tech Stack

- Python 3 + Flask
- yfinance (data)
- pandas-ta (candlestick patterns)
- Plotly (charting)
- Pandas (data manipulation)

## File Structure

```
stox/
├── app.py              # Flask server, routes, data fetching
├── analysis.py         # Technical analysis logic (MAs, patterns, stop/take)
├── templates/
│   └── index.html      # Single page with search bar + split layout
├── static/
│   └── style.css       # Styling for the layout
└── requirements.txt    # flask, yfinance, plotly, pandas-ta
```
