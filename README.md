# 📈 Dashboard Mercado Financeiro

Dashboard interativo para acompanhamento de mercados financeiros em tempo real, construído com Python e Streamlit.

## 🗂️ Módulos

| Página | Conteúdo |
|---|---|
| 🇧🇷 Ações BR | IBOVESPA, PETR4, VALE3, ITUB4 e mais |
| 🌎 Ações Globais | S&P 500, NASDAQ, Apple, NVIDIA e mais |
| ₿ Criptos | Bitcoin, Ethereum, Solana e mais |
| 🏢 FIIs | KNRI11, HGLG11, MXRF11 e mais |

## 📊 Indicadores disponíveis

- Candlestick com médias móveis (EMA 9/20, SMA 50/200)
- RSI (14) e MACD (12/26/9)
- Bollinger Bands
- P/L, Dividend Yield, Market Cap
- Dividend Yield 12M e P/VP (FIIs)
- Fear & Greed Index (Criptos)

## ⚡ Atualização automática

- Ações e FIIs: a cada **5 minutos**
- Criptomoedas: a cada **1 minuto**

## 🛠️ Tecnologias

- [Streamlit](https://streamlit.io/) — interface web
- [yfinance](https://github.com/ranaroussi/yfinance) — dados de mercado
- [Plotly](https://plotly.com/) — gráficos interativos
- [alternative.me](https://alternative.me/crypto/fear-and-greed-index/) — Fear & Greed Index

## 🚀 Como rodar localmente

pip install -r requirements.txt
streamlit run app.py

## 🌐 Deploy

Hospedado gratuitamente no Streamlit Community Cloud.
