import pandas as pd
import numpy as np


def compute_moving_averages(df):
    df["ma_50"] = df["Close"].rolling(window=50).mean()
    df["ma_200"] = df["Close"].rolling(window=200).mean()
    return df


def detect_ma_crossovers(df):
    signals = []
    ma50 = df["ma_50"]
    ma200 = df["ma_200"]

    for i in range(1, len(df)):
        if pd.isna(ma50.iloc[i]) or pd.isna(ma200.iloc[i]):
            continue
        if pd.isna(ma50.iloc[i - 1]) or pd.isna(ma200.iloc[i - 1]):
            continue

        if ma50.iloc[i] > ma200.iloc[i] and ma50.iloc[i - 1] <= ma200.iloc[i - 1]:
            signals.append(
                {
                    "date": df.index[i],
                    "price": df["Close"].iloc[i],
                    "type": "buy",
                    "pattern": "Golden Cross",
                }
            )
        elif ma50.iloc[i] < ma200.iloc[i] and ma50.iloc[i - 1] >= ma200.iloc[i - 1]:
            signals.append(
                {
                    "date": df.index[i],
                    "price": df["Close"].iloc[i],
                    "type": "sell",
                    "pattern": "Death Cross",
                }
            )

    return signals


def _body(o, c):
    return abs(c - o)


def _upper_wick(o, h, c):
    return h - max(o, c)


def _lower_wick(o, l, c):
    return min(o, c) - l


def _candle_range(h, l):
    return h - l


def detect_candlestick_patterns(df):
    signals = []
    o = df["Open"].values
    h = df["High"].values
    l = df["Low"].values
    c = df["Close"].values

    for i in range(2, len(df)):
        rng = _candle_range(h[i], l[i])
        if rng == 0:
            continue
        body = _body(o[i], c[i])
        upper = _upper_wick(o[i], h[i], c[i])
        lower = _lower_wick(o[i], l[i], c[i])

        prev_rng = _candle_range(h[i - 1], l[i - 1])
        prev_body = _body(o[i - 1], c[i - 1])

        # Hammer: small body at top, long lower wick (>= 2x body), small upper wick
        if body > 0 and lower >= 2 * body and upper <= body * 0.5:
            signals.append(
                {"date": df.index[i], "price": c[i], "type": "buy", "pattern": "Hammer"}
            )

        # Shooting Star: small body at bottom, long upper wick (>= 2x body), small lower wick
        if body > 0 and upper >= 2 * body and lower <= body * 0.5:
            signals.append(
                {"date": df.index[i], "price": c[i], "type": "sell", "pattern": "Shooting Star"}
            )

        # Doji: very small body relative to range
        if body <= rng * 0.1:
            signals.append(
                {"date": df.index[i], "price": c[i], "type": "buy", "pattern": "Doji"}
            )

        # Bullish Engulfing: prev red, current green, current body engulfs prev body
        if (
            c[i - 1] < o[i - 1]
            and c[i] > o[i]
            and o[i] <= c[i - 1]
            and c[i] >= o[i - 1]
            and prev_body > 0
        ):
            signals.append(
                {"date": df.index[i], "price": c[i], "type": "buy", "pattern": "Bullish Engulfing"}
            )

        # Bearish Engulfing: prev green, current red, current body engulfs prev body
        if (
            c[i - 1] > o[i - 1]
            and c[i] < o[i]
            and o[i] >= c[i - 1]
            and c[i] <= o[i - 1]
            and prev_body > 0
        ):
            signals.append(
                {"date": df.index[i], "price": c[i], "type": "sell", "pattern": "Bearish Engulfing"}
            )

        # Morning Star (3-candle): [i-2] red, [i-1] small body, [i] green closing above midpoint of [i-2]
        if i >= 2:
            body_2 = _body(o[i - 2], c[i - 2])
            rng_2 = _candle_range(h[i - 2], l[i - 2])
            if (
                rng_2 > 0
                and c[i - 2] < o[i - 2]
                and (prev_body <= prev_rng * 0.3 if prev_rng > 0 else False)
                and c[i] > o[i]
                and c[i] > (o[i - 2] + c[i - 2]) / 2
            ):
                signals.append(
                    {"date": df.index[i], "price": c[i], "type": "buy", "pattern": "Morning Star"}
                )

            # Evening Star: [i-2] green, [i-1] small body, [i] red closing below midpoint of [i-2]
            if (
                rng_2 > 0
                and c[i - 2] > o[i - 2]
                and (prev_body <= prev_rng * 0.3 if prev_rng > 0 else False)
                and c[i] < o[i]
                and c[i] < (o[i - 2] + c[i - 2]) / 2
            ):
                signals.append(
                    {"date": df.index[i], "price": c[i], "type": "sell", "pattern": "Evening Star"}
                )

    return signals


def find_swing_low(df, buy_price, buy_date):
    buy_idx = df.index.get_loc(buy_date)
    lookback = max(0, buy_idx - 20)
    window = df.iloc[lookback:buy_idx]

    lows_below = window[window["Low"] < buy_price]["Low"]
    if not lows_below.empty:
        return float(lows_below.min())
    return None


def compute_trade_setup(df, signals):
    buy_signals = [s for s in signals if s["type"] == "buy"]

    if not buy_signals:
        return None

    latest_buy = buy_signals[-1]
    buy_price = float(latest_buy["price"])
    buy_date = latest_buy["date"]

    swing_low = find_swing_low(df, buy_price, buy_date)
    if swing_low is not None:
        stop_loss = swing_low
    else:
        stop_loss = buy_price * 0.95

    risk = buy_price - stop_loss
    take_profit = buy_price + (risk * 2)

    return {
        "buy_price": round(buy_price, 2),
        "stop_loss": round(stop_loss, 2),
        "take_profit": round(take_profit, 2),
        "risk_reward": "1:2",
        "signal_type": latest_buy["pattern"],
        "signal_date": latest_buy["date"].strftime("%Y-%m-%d"),
    }


def analyze(df):
    df = compute_moving_averages(df)
    ma_signals = detect_ma_crossovers(df)
    candle_signals = detect_candlestick_patterns(df)
    all_signals = sorted(ma_signals + candle_signals, key=lambda s: s["date"])
    trade_setup = compute_trade_setup(df, all_signals)

    return {
        "df": df,
        "signals": all_signals,
        "trade_setup": trade_setup,
    }
