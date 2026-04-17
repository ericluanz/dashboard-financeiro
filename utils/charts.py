import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

DARK_BG   = "rgba(0,0,0,0)"
GRID_CLR  = "rgba(255,255,255,0.06)"
GREEN     = "#26a69a"
RED       = "#ef5350"
YELLOW    = "#F0B429"
BLUE      = "#42A5F5"
PURPLE    = "#CE93D8"
ORANGE    = "#FFA726"


# ──────────────────────────────────────────────────────────────
#  CANDLE + INDICADORES
# ──────────────────────────────────────────────────────────────

def candlestick_chart(df: pd.DataFrame, title: str = "", show_bb: bool = False) -> go.Figure:
    """
    Gráfico completo: candlestick + EMAs/BB  |  RSI  |  Volume
    """
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.60, 0.20, 0.20],
        subplot_titles=[title, "RSI (14)", "Volume"],
    )

    # ── Candlestick ──────────────────────────────────────────
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"], high=df["High"],
            low=df["Low"],   close=df["Close"],
            name="Preço",
            increasing_line_color=GREEN,
            decreasing_line_color=RED,
        ),
        row=1, col=1,
    )

    # ── Médias móveis ────────────────────────────────────────
    for col, color, dash, wid in [
        ("EMA9",   YELLOW, "solid", 1),
        ("EMA20",  BLUE,   "solid", 1),
        ("SMA50",  PURPLE, "dash",  1),
        ("SMA200", RED,    "dash",  1.5),
    ]:
        if col in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df[col], name=col,
                           line=dict(color=color, dash=dash, width=wid)),
                row=1, col=1,
            )

    # ── Bollinger Bands ──────────────────────────────────────
    if show_bb and "BB_Up" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["BB_Up"], name="BB +2σ",
                       line=dict(color="rgba(173,216,230,0.5)", dash="dot", width=1)),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df["BB_Lo"], name="BB −2σ",
                       line=dict(color="rgba(173,216,230,0.5)", dash="dot", width=1),
                       fill="tonexty", fillcolor="rgba(173,216,230,0.07)"),
            row=1, col=1,
        )

    # ── RSI ──────────────────────────────────────────────────
    if "RSI" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                       line=dict(color=PURPLE, width=1.5)),
            row=2, col=1,
        )
        fig.add_hline(y=70, line_dash="dot", line_color=RED,   opacity=0.5, row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color=GREEN, opacity=0.5, row=2, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor=RED,   opacity=0.04, row=2, col=1)
        fig.add_hrect(y0=0,  y1=30,  fillcolor=GREEN, opacity=0.04, row=2, col=1)

    # ── Volume ───────────────────────────────────────────────
    bar_colors = [GREEN if c >= o else RED
                  for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(
        go.Bar(x=df.index, y=df["Volume"], name="Volume",
               marker_color=bar_colors, opacity=0.6),
        row=3, col=1,
    )

    # ── Layout ───────────────────────────────────────────────
    fig.update_layout(
        height=680,
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, font=dict(size=11)),
        xaxis_rangeslider_visible=False,
        margin=dict(t=50, b=30, l=50, r=20),
    )
    fig.update_yaxes(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR)
    fig.update_xaxes(gridcolor=GRID_CLR)
    return fig


# ──────────────────────────────────────────────────────────────
#  MACD
# ──────────────────────────────────────────────────────────────

def macd_chart(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(rows=1, cols=1)

    if "MACD" not in df.columns:
        return fig

    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"],
                             name="MACD", line=dict(color=BLUE, width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"],
                             name="Signal", line=dict(color=ORANGE, width=1.5)))

    colors = [GREEN if v >= 0 else RED for v in df["MACD_Hist"]]
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], name="Histograma",
                         marker_color=colors, opacity=0.7))

    fig.update_layout(
        title="MACD (12 / 26 / 9)",
        height=240,
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        legend=dict(orientation="h"),
        margin=dict(t=40, b=20),
    )
    fig.update_yaxes(gridcolor=GRID_CLR)
    fig.update_xaxes(gridcolor=GRID_CLR)
    return fig


# ──────────────────────────────────────────────────────────────
#  GAUGE  (RSI / Fear & Greed)
# ──────────────────────────────────────────────────────────────

def gauge_chart(value: float, title: str = "RSI",
                min_v: float = 0, max_v: float = 100,
                zones: list | None = None) -> go.Figure:
    if zones is None:
        zones = [
            {"range": [0,   30],  "color": GREEN},
            {"range": [30,  70],  "color": ORANGE},
            {"range": [70,  100], "color": RED},
        ]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 14}},
        gauge={
            "axis": {"range": [min_v, max_v], "tickwidth": 1},
            "bar":  {"color": "white", "thickness": 0.18},
            "steps": zones,
            "threshold": {"line": {"color": "white", "width": 3},
                          "thickness": 0.8, "value": value},
        },
    ))
    fig.update_layout(
        height=200,
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        margin=dict(t=30, b=10, l=20, r=20),
    )
    return fig


# ──────────────────────────────────────────────────────────────
#  GRÁFICO DE PIZZA
# ──────────────────────────────────────────────────────────────

def pie_chart(labels: list, values: list, title: str = "") -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.42,
        textinfo="label+percent",
        textposition="outside",
        marker=dict(line=dict(color="#0E1117", width=2)),
    ))
    fig.update_layout(
        title=title,
        height=380,
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        margin=dict(t=50, b=20),
    )
    return fig


# ──────────────────────────────────────────────────────────────
#  BARRAS HORIZONTAIS (movers)
# ──────────────────────────────────────────────────────────────

def hbar_chart(labels: list, values: list, title: str = "") -> go.Figure:
    colors = [GREEN if v >= 0 else RED for v in values]
    fig = go.Figure(go.Bar(
        x=values, y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.2f}%" for v in values],
        textposition="outside",
    ))
    fig.update_layout(
        title=title,
        height=max(250, len(labels) * 32 + 80),
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        margin=dict(t=50, b=20, l=10, r=60),
        xaxis=dict(gridcolor=GRID_CLR, zeroline=True,
                   zerolinecolor="white", zerolinewidth=0.5),
        yaxis=dict(gridcolor=GRID_CLR),
    )
    return fig


# ──────────────────────────────────────────────────────────────
#  LINHA SIMPLES
# ──────────────────────────────────────────────────────────────

def line_chart(df: pd.DataFrame, col: str = "Close",
               title: str = "", color: str = YELLOW) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=df.index, y=df[col], name=col,
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=f"rgba({','.join(str(int(c*255)) for c in [0.94, 0.70, 0.16])},0.08)",
    ))
    fig.update_layout(
        title=title,
        height=300,
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        margin=dict(t=40, b=20),
    )
    fig.update_yaxes(gridcolor=GRID_CLR)
    fig.update_xaxes(gridcolor=GRID_CLR)
    return fig
