import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from datetime import datetime

from utils.data_fetchers import (
    get_quote, get_history_crypto, get_info,
    add_indicators, build_table,
    CRYPTOS, get_fear_greed,
    fmt_usd, fmt_pct, fmt_big,
)
from utils.charts import candlestick_chart, macd_chart, gauge_chart, hbar_chart

# ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Criptomoedas", page_icon="₿", layout="wide")
st_autorefresh(interval=60_000, key="crypto_refresh")   # 1 min

st.markdown("""
<style>
[data-testid="metric-container"] {
    background: #161B2E;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px; padding: 14px 18px;
}
.section-title {
    font-size: 1.05rem; font-weight: 600;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 6px; margin-bottom: 12px; color: #F0B429;
}
.fg-box {
    background: #161B2E;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.1);
}
.fg-value { font-size: 3rem; font-weight: 800; margin: 0; }
.fg-label { font-size: 1rem; color: #aaa; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
st.title("₿ Criptomoedas")
st.caption(f"Via Yahoo Finance · {now} · refresh automático a cada 1 min")
st.divider()

# ──────────────────────────────────────────────────────────────
#  CARDS PRINCIPAIS  BTC / ETH / BNB / SOL
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">🏆 Top Criptos – Cotação Atual</p>', unsafe_allow_html=True)

top_4 = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD"]
top_names = {"BTC-USD": "₿ Bitcoin", "ETH-USD": "Ξ Ethereum",
             "BNB-USD": "BNB", "SOL-USD": "◎ Solana"}

cols_top = st.columns(4)
for i, ticker in enumerate(top_4):
    q = get_quote(ticker)
    with cols_top[i]:
        if q:
            color = "normal" if q["change_pct"] >= 0 else "inverse"
            st.metric(
                top_names[ticker],
                fmt_usd(q["price"]),
                delta=fmt_pct(q["change_pct"]),
                delta_color=color,
            )
        else:
            st.metric(top_names[ticker], "—")

st.divider()

# ──────────────────────────────────────────────────────────────
#  FEAR & GREED + DOMINÂNCIA BTC
# ──────────────────────────────────────────────────────────────
col_fg, col_dom = st.columns([1, 2])

with col_fg:
    st.markdown('<p class="section-title">😱 Fear & Greed Index</p>', unsafe_allow_html=True)
    fg = get_fear_greed()
    val = fg["value"]
    label = fg["label"]

    # Cor baseada no valor
    if val <= 25:
        fg_color = "#ef5350"
    elif val <= 45:
        fg_color = "#FFA726"
    elif val <= 55:
        fg_color = "#aaa"
    elif val <= 75:
        fg_color = "#66BB6A"
    else:
        fg_color = "#26a69a"

    st.markdown(f"""
    <div class="fg-box">
      <p class="fg-value" style="color:{fg_color}">{val}</p>
      <p class="fg-label">{label}</p>
      <p style="color:#aaa; font-size:0.75rem; margin-top:8px">
        0–24 Medo Extremo &nbsp;|&nbsp; 25–49 Medo &nbsp;|&nbsp;
        50 Neutro &nbsp;|&nbsp; 51–74 Ganância &nbsp;|&nbsp; 75–100 Ganância Extrema
      </p>
    </div>
    """, unsafe_allow_html=True)

    fg_zones = [
        {"range": [0,   25],  "color": "#ef5350"},
        {"range": [25,  50],  "color": "#FFA726"},
        {"range": [50,  75],  "color": "#66BB6A"},
        {"range": [75,  100], "color": "#26a69a"},
    ]
    st.plotly_chart(
        gauge_chart(val, title="Fear & Greed", zones=fg_zones),
        use_container_width=True,
    )

with col_dom:
    st.markdown('<p class="section-title">📊 Variação 24h – Todas as Criptos</p>',
                unsafe_allow_html=True)
    with st.spinner("Carregando variações…"):
        df_all = build_table(CRYPTOS)

    if not df_all.empty:
        df_sorted = df_all.sort_values("Var. Dia (%)", ascending=False)
        st.plotly_chart(
            hbar_chart(
                list(df_sorted["Ticker"].str.replace("-USD", "")),
                list(df_sorted["Var. Dia (%)"]),
                "Variação % – 24 horas",
            ),
            use_container_width=True,
        )

st.divider()

# ──────────────────────────────────────────────────────────────
#  TABELA COMPLETA
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📋 Tabela de Mercado</p>', unsafe_allow_html=True)

if not df_all.empty:
    def color_var(val):
        try:
            v = float(str(val).replace("%", "").replace("+", ""))
            return f"color: {'#26a69a' if v >= 0 else '#ef5350'}; font-weight:bold"
        except:
            return ""

    df_display = df_all.copy()
    df_display["Ticker"]       = df_display["Ticker"].str.replace("-USD", "")
    df_display["Preço"]        = df_display["Preço"].apply(fmt_usd)
    df_display["Var. Dia (%)"] = df_display["Var. Dia (%)"].apply(fmt_pct)
    df_display["Volume"]       = df_display["Volume"].apply(fmt_big)

    st.dataframe(
        df_display.style.map(color_var, subset=["Var. Dia (%)"]),
        use_container_width=True, hide_index=True,
    )

st.divider()

# ──────────────────────────────────────────────────────────────
#  ANÁLISE TÉCNICA
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">🔍 Análise Técnica Individual</p>', unsafe_allow_html=True)

col_sel, col_per, col_int = st.columns([2, 1, 1])
with col_sel:
    ticker_labels = {v: k for k, v in CRYPTOS.items()}
    nome_sel   = st.selectbox("Selecione a cripto", list(CRYPTOS.values()))
    ticker_sel = ticker_labels[nome_sel]

with col_per:
    period_map = {"7 Dias": "7d", "1 Mês": "1mo", "3 Meses": "3mo",
                  "6 Meses": "6mo", "1 Ano": "1y", "2 Anos": "2y"}
    period_lbl = st.selectbox("Período", list(period_map.keys()), index=4)
    period_sel = period_map[period_lbl]

with col_int:
    int_map = {"Diário": "1d", "Semanal": "1wk", "Horário (max 730d)": "1h"}
    int_lbl = st.selectbox("Intervalo", list(int_map.keys()))
    int_sel = int_map[int_lbl]

show_bb   = st.checkbox("Bollinger Bands", value=False, key="bb_crypto")
show_macd = st.checkbox("MACD", value=True, key="macd_crypto")

with st.spinner(f"Carregando {nome_sel}…"):
    df_sel = get_history_crypto(ticker_sel, period=period_sel, interval=int_sel)
    info   = get_info(ticker_sel)

if df_sel is not None:
    df_ind = add_indicators(df_sel)
    q = get_quote(ticker_sel)

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Preço (USD)", fmt_usd(q["price"]) if q else "—",
                  delta=fmt_pct(q["change_pct"]) if q else None)
    with m2:
        mc = info.get("marketCap")
        st.metric("Market Cap", fmt_big(mc) if mc else "—")
    with m3:
        vol24 = info.get("volume24Hr") or (q["volume"] if q else None)
        st.metric("Vol. 24h", fmt_big(vol24) if vol24 else "—")
    with m4:
        rsi_val = df_ind["RSI"].iloc[-1] if "RSI" in df_ind.columns else None
        st.metric("RSI (14)", f"{rsi_val:.1f}" if rsi_val else "—")
    with m5:
        h52 = info.get("fiftyTwoWeekHigh")
        l52 = info.get("fiftyTwoWeekLow")
        if h52 and l52 and q:
            pct_from_ath = (q["price"] / h52 - 1) * 100
            st.metric("Dist. Máxima 52s", fmt_pct(pct_from_ath))

    st.plotly_chart(
        candlestick_chart(df_ind,
                          title=f"{nome_sel} (USD) – {period_lbl}",
                          show_bb=show_bb),
        use_container_width=True,
    )

    if show_macd:
        col_m, col_g = st.columns([3, 1])
        with col_m:
            st.plotly_chart(macd_chart(df_ind), use_container_width=True)
        with col_g:
            if rsi_val:
                st.plotly_chart(gauge_chart(rsi_val, title=f"RSI – {nome_sel}"),
                                use_container_width=True)
else:
    st.warning(f"Não foi possível carregar dados para {nome_sel}. Tente outro intervalo ou período.")
