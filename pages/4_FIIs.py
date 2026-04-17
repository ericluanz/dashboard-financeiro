import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import numpy as np
from datetime import datetime

from utils.data_fetchers import (
    get_quote, get_history, get_info, get_dividends,
    add_indicators, build_table,
    FIIS, FII_SECTORS, fmt_brl, fmt_pct, fmt_big,
)
from utils.charts import candlestick_chart, macd_chart, gauge_chart, pie_chart, hbar_chart

# ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="FIIs", page_icon="🏢", layout="wide")
st_autorefresh(interval=300_000, key="fii_refresh")

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
st.title("🏢 Fundos de Investimento Imobiliário (FIIs)")
st.caption(f"Dados da B3 via Yahoo Finance · {now} · refresh a cada 5 min")
st.divider()

# ──────────────────────────────────────────────────────────────
#  TABELA GERAL COM INDICADORES FUNDAMENTAIS
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📋 Cotações e Indicadores dos FIIs</p>',
            unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_fii_table() -> pd.DataFrame:
    rows = []
    for ticker, name in FIIS.items():
        q    = get_quote(ticker)
        info = get_info(ticker)
        divs = get_dividends(ticker)

        if q is None:
            continue

        price = q["price"]

        # Dividend Yield 12 meses
        dy_12m = None
        if not divs.empty:
            try:
                one_year_ago = pd.Timestamp.now(tz=divs.index.tz) - pd.DateOffset(years=1)
                last_year_divs = divs[divs.index >= one_year_ago]
                if not last_year_divs.empty and price > 0:
                    dy_12m = (last_year_divs.sum() / price) * 100
            except Exception:
                pass

        # Último dividendo
        last_div = divs.iloc[-1] if not divs.empty else None

        # P/VP do yfinance (pode não estar disponível)
        book_val = info.get("bookValue")
        pvp = (price / book_val) if (book_val and book_val > 0) else None

        rows.append({
            "Ticker":      ticker.replace(".SA", ""),
            "Nome":        name,
            "Setor":       FII_SECTORS.get(ticker, "—"),
            "Preço (R$)":  price,
            "Var. Dia (%)": q["change_pct"],
            "DY 12M (%)":  dy_12m,
            "Último Div.": last_div,
            "P/VP":        pvp,
            "Volume":      q["volume"],
        })

    return pd.DataFrame(rows)

with st.spinner("Carregando FIIs…"):
    df_fiis = load_fii_table()

if not df_fiis.empty:
    def color_var(val):
        try:
            v = float(str(val).replace("%", "").replace("+", ""))
            return f"color: {'#26a69a' if v >= 0 else '#ef5350'}; font-weight:bold"
        except:
            return ""

    df_display = df_fiis.copy()
    df_display["Preço (R$)"]   = df_display["Preço (R$)"].apply(fmt_brl)
    df_display["Var. Dia (%)"] = df_display["Var. Dia (%)"].apply(fmt_pct)
    df_display["DY 12M (%)"]   = df_display["DY 12M (%)"].apply(
        lambda v: f"{v:.2f}%" if (v is not None and not (isinstance(v, float) and np.isnan(v))) else "—"
    )
    df_display["Último Div."]  = df_display["Último Div."].apply(
        lambda v: fmt_brl(v) if v is not None else "—"
    )
    df_display["P/VP"]         = df_display["P/VP"].apply(
        lambda v: f"{v:.2f}x" if (v is not None and not (isinstance(v, float) and np.isnan(v))) else "—"
    )
    df_display["Volume"]       = df_display["Volume"].apply(fmt_big)

    st.dataframe(
        df_display.style.applymap(color_var, subset=["Var. Dia (%)"]),
        use_container_width=True, hide_index=True,
    )

    st.divider()

    # ── Gráficos de ranking ──────────────────────────────────
    col_rank_dy, col_rank_var = st.columns(2)

    with col_rank_dy:
        st.markdown('<p class="section-title">💰 Ranking por Dividend Yield 12M</p>',
                    unsafe_allow_html=True)
        df_dy = df_fiis[df_fiis["DY 12M (%)"].notna()].sort_values("DY 12M (%)", ascending=True)
        if not df_dy.empty:
            st.plotly_chart(
                hbar_chart(
                    list(df_dy["Ticker"]),
                    list(df_dy["DY 12M (%)"]),
                    title="",
                ),
                use_container_width=True,
            )

    with col_rank_var:
        st.markdown('<p class="section-title">📊 Variação % do Dia</p>',
                    unsafe_allow_html=True)
        df_var = df_fiis.sort_values("Var. Dia (%)", ascending=True)
        st.plotly_chart(
            hbar_chart(
                list(df_var["Ticker"]),
                list(df_var["Var. Dia (%)"]),
                title="",
            ),
            use_container_width=True,
        )

    st.divider()

    # ── Distribuição por setor ───────────────────────────────
    st.markdown('<p class="section-title">🏗️ Distribuição por Setor</p>',
                unsafe_allow_html=True)
    sector_vol = df_fiis.groupby("Setor")["Volume"].sum()
    st.plotly_chart(
        pie_chart(
            list(sector_vol.index),
            list(sector_vol.values),
            title="Volume por Setor",
        ),
        use_container_width=True,
    )

st.divider()

# ──────────────────────────────────────────────────────────────
#  ANÁLISE INDIVIDUAL
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">🔍 Análise Técnica Individual</p>',
            unsafe_allow_html=True)

col_sel, col_per = st.columns([2, 1])
with col_sel:
    ticker_labels = {v: k for k, v in FIIS.items()}
    nome_sel   = st.selectbox("Selecione o FII", list(FIIS.values()))
    ticker_sel = ticker_labels[nome_sel]

with col_per:
    period_map = {"1 Mês": "1mo", "3 Meses": "3mo", "6 Meses": "6mo",
                  "1 Ano": "1y",  "2 Anos":  "2y",  "5 Anos":  "5y"}
    period_lbl = st.selectbox("Período", list(period_map.keys()), index=3)
    period_sel = period_map[period_lbl]

show_bb   = st.checkbox("Bollinger Bands", value=False, key="bb_fii")
show_macd = st.checkbox("MACD", value=True, key="macd_fii")

with st.spinner(f"Carregando {nome_sel}…"):
    df_sel = get_history(ticker_sel, period=period_sel)
    info   = get_info(ticker_sel)
    divs   = get_dividends(ticker_sel)

if df_sel is not None:
    df_ind = add_indicators(df_sel)
    q = get_quote(ticker_sel)

    # Métricas
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Cota Atual", fmt_brl(q["price"]) if q else "—",
                  delta=fmt_pct(q["change_pct"]) if q else None)
    with m2:
        if not divs.empty and q:
            try:
                one_year_ago = pd.Timestamp.now(tz=divs.index.tz) - pd.DateOffset(years=1)
                dy_12m = (divs[divs.index >= one_year_ago].sum() / q["price"]) * 100
                st.metric("DY 12M", f"{dy_12m:.2f}%")
            except:
                st.metric("DY 12M", "—")
        else:
            st.metric("DY 12M", "—")
    with m3:
        last_div = divs.iloc[-1] if not divs.empty else None
        st.metric("Último Div.", fmt_brl(last_div) if last_div else "—")
    with m4:
        rsi_val = df_ind["RSI"].iloc[-1] if "RSI" in df_ind.columns else None
        st.metric("RSI (14)", f"{rsi_val:.1f}" if rsi_val else "—")
    with m5:
        book = info.get("bookValue")
        pvp  = (q["price"] / book) if (book and book > 0 and q) else None
        st.metric("P/VP", f"{pvp:.2f}x" if pvp else "—")

    st.plotly_chart(
        candlestick_chart(df_ind,
                          title=f"{nome_sel} ({ticker_sel.replace('.SA','')})",
                          show_bb=show_bb),
        use_container_width=True,
    )

    if show_macd:
        col_m, col_g = st.columns([3, 1])
        with col_m:
            st.plotly_chart(macd_chart(df_ind), use_container_width=True)
        with col_g:
            if rsi_val:
                st.plotly_chart(gauge_chart(rsi_val, title="RSI"), use_container_width=True)

    # Dividendos históricos
    if not divs.empty:
        st.divider()
        st.markdown('<p class="section-title">💰 Histórico de Rendimentos (Proventos)</p>',
                    unsafe_allow_html=True)

        divs_df = divs.reset_index()
        divs_df.columns = ["Data", "Valor (R$)"]
        divs_df["Data"] = pd.to_datetime(divs_df["Data"]).dt.strftime("%d/%m/%Y")
        divs_df["Valor (R$)"] = divs_df["Valor (R$)"].apply(fmt_brl)

        col_hist, col_stat = st.columns([2, 1])
        with col_hist:
            st.dataframe(
                divs_df.sort_values("Data", ascending=False).head(24),
                use_container_width=True, hide_index=True,
            )
        with col_stat:
            divs_num = divs.tail(12)
            if not divs_num.empty:
                st.metric("Média mensal (12M)", fmt_brl(divs_num.mean()))
                st.metric("Total 12M / cota",  fmt_brl(divs_num.sum()))
                st.metric("Nº pagamentos 12M",  str(len(divs_num)))
else:
    st.warning(f"Não foi possível carregar dados para {nome_sel}.")
