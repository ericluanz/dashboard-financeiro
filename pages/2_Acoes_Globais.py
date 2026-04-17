import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from datetime import datetime

from utils.data_fetchers import (
    get_quote, get_history, get_info, get_dividends,
    add_indicators, build_table,
    GLOBAL_INDICES, GLOBAL_STOCKS, fmt_usd, fmt_pct, fmt_big,
)
from utils.charts import candlestick_chart, macd_chart, gauge_chart, hbar_chart, line_chart

# ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Ações Globais", page_icon="🌎", layout="wide")
st_autorefresh(interval=300_000, key="global_refresh")

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
</style>
""", unsafe_allow_html=True)

now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
st.title("🌎 Ações Globais")
st.caption(f"NYSE · NASDAQ · LSE · Frankfurt · Tóquio · {now} · refresh a cada 5 min")
st.divider()

# ──────────────────────────────────────────────────────────────
#  ÍNDICES
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📊 Principais Índices Mundiais</p>', unsafe_allow_html=True)

index_rows = []
for ticker, name in GLOBAL_INDICES.items():
    q = get_quote(ticker)
    if q:
        index_rows.append({
            "Índice":     name,
            "Cotação":    f"{q['price']:,.2f}",
            "Variação":   fmt_pct(q["change_pct"]),
            "Volume":     fmt_big(q["volume"]),
            "_var_raw":   q["change_pct"],
        })

if index_rows:
    cols = st.columns(min(len(index_rows), 4))
    for i, row in enumerate(index_rows[:4]):
        with cols[i]:
            color = "normal" if row["_var_raw"] >= 0 else "inverse"
            st.metric(row["Índice"], row["Cotação"],
                      delta=row["Variação"], delta_color=color)

    # Tabela completa
    df_idx = pd.DataFrame(index_rows)[["Índice", "Cotação", "Variação", "Volume"]]

    def color_var(val):
        try:
            v = float(str(val).replace("%", "").replace("+", ""))
            return f"color: {'#26a69a' if v >= 0 else '#ef5350'}; font-weight:bold"
        except:
            return ""

    st.dataframe(
        df_idx.style.map(color_var, subset=["Variação"]),
        use_container_width=True, hide_index=True,
    )

st.divider()

# ──────────────────────────────────────────────────────────────
#  CÂMBIO USD/BRL
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">💵 USD / BRL</p>', unsafe_allow_html=True)
fx_hist = get_history("BRL=X", period="1y")
if fx_hist is not None:
    st.plotly_chart(line_chart(fx_hist, col="Close", title="USD/BRL – 1 Ano"),
                    use_container_width=True)

st.divider()

# ──────────────────────────────────────────────────────────────
#  COTAÇÕES EM TEMPO REAL
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📋 Cotações em Tempo Real – Top Stocks</p>',
            unsafe_allow_html=True)

with st.spinner("Carregando cotações…"):
    df_table = build_table(GLOBAL_STOCKS)

if not df_table.empty:
    def color_var(val):
        try:
            v = float(str(val).replace("%", "").replace("+", ""))
            return f"color: {'#26a69a' if v >= 0 else '#ef5350'}; font-weight:bold"
        except:
            return ""

    df_display = df_table.copy()
    df_display["Preço"]        = df_display["Preço"].apply(fmt_usd)
    df_display["Var. Dia (%)"] = df_display["Var. Dia (%)"].apply(fmt_pct)
    df_display["Volume"]       = df_display["Volume"].apply(fmt_big)

    st.dataframe(
        df_display.style.map(color_var, subset=["Var. Dia (%)"]),
        use_container_width=True, hide_index=True,
    )

    df_sorted = df_table.sort_values("Var. Dia (%)", ascending=False)
    st.plotly_chart(
        hbar_chart(list(df_sorted["Ticker"]),
                   list(df_sorted["Var. Dia (%)"]),
                   "Variação % do Dia"),
        use_container_width=True,
    )

st.divider()

# ──────────────────────────────────────────────────────────────
#  ANÁLISE INDIVIDUAL
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">🔍 Análise Técnica Individual</p>', unsafe_allow_html=True)

col_sel, col_per = st.columns([2, 1])
with col_sel:
    ticker_labels = {v: k for k, v in GLOBAL_STOCKS.items()}
    nome_sel  = st.selectbox("Selecione o ativo", list(GLOBAL_STOCKS.values()))
    ticker_sel = ticker_labels[nome_sel]

with col_per:
    period_map = {"1 Mês": "1mo", "3 Meses": "3mo", "6 Meses": "6mo",
                  "1 Ano": "1y",  "2 Anos":  "2y",  "5 Anos":  "5y"}
    period_lbl = st.selectbox("Período", list(period_map.keys()), index=3)
    period_sel = period_map[period_lbl]

show_bb   = st.checkbox("Bollinger Bands", value=False)
show_macd = st.checkbox("MACD", value=True)

with st.spinner(f"Carregando {nome_sel}…"):
    df_sel = get_history(ticker_sel, period=period_sel)
    info   = get_info(ticker_sel)

if df_sel is not None:
    df_ind = add_indicators(df_sel)
    q = get_quote(ticker_sel)

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        st.metric("Preço", fmt_usd(q["price"]) if q else "—",
                  delta=fmt_pct(q["change_pct"]) if q else None)
    with m2:
        pe = info.get("trailingPE")
        st.metric("P/L", f"{pe:.1f}x" if pe else "—")
    with m3:
        dy = info.get("dividendYield")
        st.metric("Div. Yield", f"{dy*100:.2f}%" if dy else "—")
    with m4:
        mc = info.get("marketCap")
        st.metric("Market Cap", fmt_big(mc) if mc else "—")
    with m5:
        rsi_val = df_ind["RSI"].iloc[-1] if "RSI" in df_ind.columns else None
        st.metric("RSI (14)", f"{rsi_val:.1f}" if rsi_val else "—")
    with m6:
        beta = info.get("beta")
        st.metric("Beta", f"{beta:.2f}" if beta else "—")

    st.plotly_chart(
        candlestick_chart(df_ind,
                          title=f"{nome_sel} ({ticker_sel})",
                          show_bb=show_bb),
        use_container_width=True,
    )

    if show_macd:
        col_m, col_g = st.columns([3, 1])
        with col_m:
            st.plotly_chart(macd_chart(df_ind), use_container_width=True)
        with col_g:
            if rsi_val:
                st.plotly_chart(gauge_chart(rsi_val, title=f"RSI ({ticker_sel})"),
                                use_container_width=True)
else:
    st.warning(f"Não foi possível carregar dados para {nome_sel}.")
