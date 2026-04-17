import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pandas as pd

from utils.data_fetchers import (
    get_quote, get_history,
    BR_STOCKS, GLOBAL_INDICES, CRYPTOS, FIIS,
    fmt_pct,
)
from utils.charts import hbar_chart

# ──────────────────────────────────────────────────────────────
#  CONFIGURAÇÃO DA PÁGINA
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mercado Financeiro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Auto-refresh a cada 5 minutos
st_autorefresh(interval=300_000, key="home_refresh")

# ──────────────────────────────────────────────────────────────
#  CSS CUSTOMIZADO
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Cards de métrica */
[data-testid="metric-container"] {
    background: #161B2E;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 16px 20px;
}
[data-testid="metric-container"] > div {
    gap: 4px;
}
/* Cabeçalho */
.header-box {
    background: linear-gradient(135deg, #161B2E 0%, #1E2540 100%);
    border-left: 4px solid #F0B429;
    padding: 18px 24px;
    border-radius: 8px;
    margin-bottom: 24px;
}
.header-box h1 { margin: 0; font-size: 1.8rem; }
.header-box p  { margin: 4px 0 0; color: #aaa; font-size: 0.9rem; }
/* Seção */
.section-title {
    font-size: 1.1rem;
    font-weight: 600;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 6px;
    margin-bottom: 12px;
    color: #F0B429;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
#  CABEÇALHO
# ──────────────────────────────────────────────────────────────
now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
st.markdown(f"""
<div class="header-box">
  <h1>📈 Mercado Financeiro</h1>
  <p>Visão geral dos mercados · Atualizado em: {now} · Refresh automático a cada 5 min</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
#  RESUMO DE MERCADOS (4 cards principais)
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">🌐 Resumo dos Mercados</p>', unsafe_allow_html=True)

with st.spinner("Carregando cotações…"):
    ibov  = get_quote("^BVSP")
    sp500 = get_quote("^GSPC")
    btc   = get_quote("BTC-USD")
    dolar = get_quote("BRL=X")

col1, col2, col3, col4 = st.columns(4)

def show_metric(col, label, q, is_brl=False, is_usd=False):
    with col:
        if q:
            price = q["price"]
            if is_brl:
                price_str = f"R$ {price:,.0f}".replace(",", ".")
            elif is_usd:
                price_str = f"$ {price:,.2f}"
            else:
                price_str = f"{price:,.2f}"
            delta_str = fmt_pct(q["change_pct"])
            color = "normal" if q["change_pct"] >= 0 else "inverse"
            st.metric(label=label, value=price_str, delta=delta_str, delta_color=color)
        else:
            st.metric(label=label, value="—", delta="sem dados")

show_metric(col1, "🇧🇷 IBOVESPA",  ibov,  is_brl=True)
show_metric(col2, "🇺🇸 S&P 500",   sp500, is_usd=True)
show_metric(col3, "₿  Bitcoin",    btc,   is_usd=True)
show_metric(col4, "💵 USD/BRL",    dolar)

st.divider()

# ──────────────────────────────────────────────────────────────
#  MAIORES ALTAS E BAIXAS
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📊 Maiores Variações do Dia</p>', unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_movers():
    all_tickers = list(BR_STOCKS.keys()) + list(CRYPTOS.keys())[:6]
    movers = {}
    for t in all_tickers:
        q = get_quote(t)
        if q:
            label = t.replace(".SA", "").replace("-USD", "")
            movers[label] = q["change_pct"]
    return movers

with st.spinner("Calculando variações…"):
    movers = load_movers()

if movers:
    sorted_m = sorted(movers.items(), key=lambda x: x[1], reverse=True)
    top5  = sorted_m[:5]
    bot5  = sorted_m[-5:]

    col_a, col_b = st.columns(2)
    with col_a:
        labels = [x[0] for x in top5]
        values = [x[1] for x in top5]
        st.plotly_chart(
            hbar_chart(labels, values, "🚀 Maiores Altas"),
            use_container_width=True,
        )
    with col_b:
        labels = [x[0] for x in bot5]
        values = [x[1] for x in bot5]
        st.plotly_chart(
            hbar_chart(labels, values, "📉 Maiores Quedas"),
            use_container_width=True,
        )

st.divider()

# ──────────────────────────────────────────────────────────────
#  ÍNDICES GLOBAIS
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">🌎 Índices Globais</p>', unsafe_allow_html=True)

indices_data = []
for ticker, name in GLOBAL_INDICES.items():
    q = get_quote(ticker)
    if q:
        indices_data.append({
            "Índice":     name,
            "Cotação":    f"{q['price']:,.2f}",
            "Var. Dia":   fmt_pct(q["change_pct"]),
            "Variação %": q["change_pct"],
        })

if indices_data:
    df_idx = pd.DataFrame(indices_data)

    def color_var(val):
        try:
            v = float(val.replace("%", "").replace("+", ""))
            color = "#26a69a" if v >= 0 else "#ef5350"
            return f"color: {color}; font-weight: bold"
        except Exception:
            return ""

    styled = (
        df_idx[["Índice", "Cotação", "Var. Dia"]]
        .style
        .applymap(color_var, subset=["Var. Dia"])
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()

# ──────────────────────────────────────────────────────────────
#  NAVEGAÇÃO RÁPIDA
# ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">🗂️ Acesse os Dashboards</p>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.info("🇧🇷 **Ações BR**\nIBOVESPA, PETR4, VALE3, ITUB4 e mais")
with c2:
    st.info("🌎 **Ações Globais**\nS&P 500, NASDAQ, Apple, NVIDIA e mais")
with c3:
    st.info("₿ **Criptos**\nBitcoin, Ethereum, Solana e mais")
with c4:
    st.info("🏢 **FIIs**\nKNRI11, HGLG11, MXRF11 e mais")

st.caption("Use o menu lateral para navegar entre os dashboards.")
