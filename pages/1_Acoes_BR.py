import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from datetime import datetime

from utils.data_fetchers import (
    get_quote, get_history, get_info, get_dividends,
    add_indicators, build_table,
    BR_STOCKS, fmt_brl, fmt_pct, fmt_big,
)
from utils.charts import candlestick_chart, macd_chart, gauge_chart, hbar_chart

# ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Ações BR", page_icon="🇧🇷", layout="wide")
st_autorefresh(interval=300_000, key="br_refresh")

st.markdown("""
<style>
[data-testid="metric-container"] {
    background: #161B2E;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 14px 18px;
}
.section-title {
    font-size: 1.05rem; font-weight: 600;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 6px; margin-bottom: 12px; color: #F0B429;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
#  CABEÇALHO
# ──────────────────────────────────────────────────────────────
now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
st.title("🇧🇷 Ações Brasileiras")
st.caption(f"Dados da B3 via Yahoo Finance · {now} · refresh a cada 5 min")
st.divider()

# ──────────────────────────────────────────────────────────────
#  IBOVESPA
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📊 IBOVESPA</p>', unsafe_allow_html=True)

ibov_hist = get_history("^BVSP", period="1y")
ibov_q    = get_quote("^BVSP")

c1, c2, c3, c4 = st.columns(4)
if ibov_q:
    with c1:
        st.metric("Pontos", f"{ibov_q['price']:,.0f}".replace(",", "."),
                  delta=fmt_pct(ibov_q["change_pct"]))
    with c2:
        st.metric("Variação R$", fmt_brl(ibov_q["change"]))
    with c3:
        if ibov_hist is not None:
            week_ago = ibov_hist["Close"].iloc[-6] if len(ibov_hist) >= 6 else ibov_hist["Close"].iloc[0]
            var_sem = (ibov_hist["Close"].iloc[-1] / week_ago - 1) * 100
            st.metric("Variação 5D", fmt_pct(var_sem))
    with c4:
        if ibov_hist is not None:
            var_ano = (ibov_hist["Close"].iloc[-1] / ibov_hist["Close"].iloc[0] - 1) * 100
            st.metric("Variação 1 Ano", fmt_pct(var_ano))

if ibov_hist is not None:
    ibov_ind = add_indicators(ibov_hist)
    st.plotly_chart(
        candlestick_chart(ibov_ind, title="IBOVESPA – Histórico 1 Ano"),
        use_container_width=True,
    )

st.divider()

# ──────────────────────────────────────────────────────────────
#  TABELA GERAL DE AÇÕES
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📋 Cotações em Tempo Real</p>', unsafe_allow_html=True)

with st.spinner("Carregando cotações…"):
    df_table = build_table(BR_STOCKS)

if not df_table.empty:
    # Formatação
    def color_var(val):
        try:
            v = float(str(val).replace("%", "").replace("+", ""))
            return f"color: {'#26a69a' if v >= 0 else '#ef5350'}; font-weight:bold"
        except:
            return ""

    df_display = df_table.copy()
    df_display["Preço"]        = df_display["Preço"].apply(fmt_brl)
    df_display["Var. Dia (%)"] = df_display["Var. Dia (%)"].apply(fmt_pct)
    df_display["Volume"]       = df_display["Volume"].apply(fmt_big)

    styled = df_display.style.map(color_var, subset=["Var. Dia (%)"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Gráfico de variações
    df_sorted = df_table.sort_values("Var. Dia (%)", ascending=False)
    st.plotly_chart(
        hbar_chart(
            list(df_sorted["Ticker"]),
            list(df_sorted["Var. Dia (%)"]),
            "Variação % do Dia – Todas as Ações",
        ),
        use_container_width=True,
    )

st.divider()

# ──────────────────────────────────────────────────────────────
#  ANÁLISE INDIVIDUAL
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">🔍 Análise Técnica Individual</p>', unsafe_allow_html=True)

col_sel, col_per = st.columns([2, 1])
with col_sel:
    ticker_labels = {v: k for k, v in BR_STOCKS.items()}
    nome_sel = st.selectbox("Selecione o ativo", list(BR_STOCKS.values()))
    ticker_sel = ticker_labels[nome_sel]

with col_per:
    period_map = {"1 Mês": "1mo", "3 Meses": "3mo", "6 Meses": "6mo",
                  "1 Ano": "1y",  "2 Anos":  "2y",  "5 Anos":  "5y"}
    period_lbl = st.selectbox("Período", list(period_map.keys()), index=3)
    period_sel = period_map[period_lbl]

col_bb, col_macd = st.columns([1, 1])
with col_bb:
    show_bb   = st.checkbox("Bollinger Bands", value=False)
with col_macd:
    show_macd = st.checkbox("MACD", value=True)

with st.spinner(f"Carregando {nome_sel}…"):
    df_sel  = get_history(ticker_sel, period=period_sel)
    info    = get_info(ticker_sel)
    divs    = get_dividends(ticker_sel)

if df_sel is not None:
    df_ind = add_indicators(df_sel)

    # Métricas do ativo
    q = get_quote(ticker_sel)
    m1, m2, m3, m4, m5, m6 = st.columns(6)

    with m1:
        st.metric("Preço Atual", fmt_brl(q["price"]) if q else "—",
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
        vol52h = info.get("fiftyTwoWeekHigh")
        vol52l = info.get("fiftyTwoWeekLow")
        if vol52h and vol52l:
            st.metric("Máx/Mín 52s", f"{fmt_brl(vol52h)} / {fmt_brl(vol52l)}")

    # Gráfico principal
    st.plotly_chart(
        candlestick_chart(df_ind, title=f"{nome_sel} ({ticker_sel.replace('.SA','')})",
                          show_bb=show_bb),
        use_container_width=True,
    )

    # MACD e Gauge RSI lado a lado
    if show_macd:
        col_macd_chart, col_gauge = st.columns([3, 1])
        with col_macd_chart:
            st.plotly_chart(macd_chart(df_ind), use_container_width=True)
        with col_gauge:
            if rsi_val:
                st.plotly_chart(gauge_chart(rsi_val, title=f"RSI ({nome_sel})"),
                                use_container_width=True)

    # Histórico de dividendos
    if not divs.empty:
        st.markdown('<p class="section-title">💰 Histórico de Dividendos / JCP</p>',
                    unsafe_allow_html=True)
        divs_df = divs.reset_index()
        divs_df.columns = ["Data", "Valor (R$)"]
        divs_df["Valor (R$)"] = divs_df["Valor (R$)"].apply(fmt_brl)
        divs_df["Data"] = pd.to_datetime(divs_df["Data"]).dt.strftime("%d/%m/%Y")
        st.dataframe(divs_df.tail(20).sort_values("Data", ascending=False),
                     use_container_width=True, hide_index=True)
else:
    st.warning(f"Não foi possível carregar dados para {nome_sel}. Tente novamente.")
