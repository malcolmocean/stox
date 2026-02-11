import json

import plotly
import plotly.graph_objects as go
import yfinance as yf
from flask import Flask, render_template, request, jsonify

from analysis import analyze

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_ticker():
    ticker = request.json.get("ticker", "").strip().upper()
    if not ticker:
        return jsonify({"error": "No ticker provided"}), 400

    # Fetch 6 months of daily data (need extra history for 200-day MA)
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty:
            return jsonify({"error": f"No data found for {ticker}"}), 404
        info = stock.info
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Run analysis
    result = analyze(df)
    analysis_df = result["df"]
    signals = result["signals"]
    trade_setup = result["trade_setup"]

    # Trim to ~6 months for display
    display_df = analysis_df.tail(126)

    # Build Plotly chart
    chart = build_chart(display_df, signals, trade_setup)

    # Stock info
    current_price = float(df["Close"].iloc[-1])
    prev_close = float(df["Close"].iloc[-2]) if len(df) > 1 else current_price
    change_dollar = round(current_price - prev_close, 2)
    change_pct = round((change_dollar / prev_close) * 100, 2)

    return jsonify(
        {
            "ticker": ticker,
            "company_name": info.get("shortName", ticker),
            "current_price": round(current_price, 2),
            "change_dollar": change_dollar,
            "change_pct": change_pct,
            "trade_setup": trade_setup,
            "chart": json.loads(plotly.io.to_json(chart)),
        }
    )


def build_chart(df, signals, trade_setup):
    fig = go.Figure()

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        )
    )

    # 50-day MA
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["ma_50"],
            mode="lines",
            name="50 MA",
            line=dict(color="#2196F3", width=1.5),
        )
    )

    # 200-day MA
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["ma_200"],
            mode="lines",
            name="200 MA",
            line=dict(color="#FF9800", width=1.5),
        )
    )

    # Volume
    colors = [
        "rgba(38,166,154,0.3)" if c >= o else "rgba(239,83,80,0.3)"
        for c, o in zip(df["Close"], df["Open"])
    ]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker_color=colors,
            yaxis="y2",
        )
    )

    # Buy/Sell signal markers
    display_start = df.index[0]
    for sig in signals:
        if sig["date"] < display_start:
            continue
        if sig["type"] == "buy":
            fig.add_trace(
                go.Scatter(
                    x=[sig["date"]],
                    y=[sig["price"]],
                    mode="markers",
                    marker=dict(symbol="triangle-up", size=12, color="#4CAF50"),
                    name=sig["pattern"],
                    showlegend=False,
                    hovertext=sig["pattern"],
                )
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=[sig["date"]],
                    y=[sig["price"]],
                    mode="markers",
                    marker=dict(symbol="triangle-down", size=12, color="#F44336"),
                    name=sig["pattern"],
                    showlegend=False,
                    hovertext=sig["pattern"],
                )
            )

    # Trade level lines
    if trade_setup:
        for level, color, label in [
            ("buy_price", "#4CAF50", "Buy"),
            ("stop_loss", "#F44336", "Stop Loss"),
            ("take_profit", "#2196F3", "Take Profit"),
        ]:
            fig.add_hline(
                y=trade_setup[level],
                line_dash="dash",
                line_color=color,
                annotation_text=f"{label}: ${trade_setup[level]}",
                annotation_position="top left",
            )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#16213e",
        xaxis_rangeslider_visible=False,
        height=600,
        margin=dict(l=50, r=20, t=30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="Price", side="right"),
        yaxis2=dict(
            title="Volume",
            overlaying="y",
            side="left",
            showgrid=False,
            range=[0, df["Volume"].max() * 4],
        ),
        xaxis=dict(
            type="date",
            rangebreaks=[dict(bounds=["sat", "mon"])],
        ),
    )

    return fig


if __name__ == "__main__":
    app.run(debug=True, port=5000)
