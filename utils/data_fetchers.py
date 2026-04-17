import yfinance as yf
import pandas as pd
import numpy as np
import requests
import streamlit as st
from datetime import datetime

# ============================================================
#  ATIVOS MONITORADOS
# ============================================================

BR_STOCKS = {
    "PETR4.SA": "Petrobras PN",
    "VALE3.SA": "Vale ON",
    "ITUB4.SA": "Itaú Unibanco PN",
    "BBDC4.SA": "Bradesco PN",
    "ABEV3.SA": "Ambev ON",
    "WEGE3.SA": "WEG ON",
    "B3SA3.SA": "B3 ON",
    "BBAS3.SA": "Banco do Brasil ON",
    "RENT3.SA": "Localiza ON",
    "SUZB3.SA": "Suzano ON",
    "RDOR3.SA": "Rede D'Or ON",
    "LREN3.SA": "Lojas Renner ON",
}

GLOBAL_INDICES = {
    "^GSPC": "S&P 500",
    "^IXIC": "NASDAQ",
    "^DJI": "Dow Jones",
    "^FTSE": "FTSE 100",
    "^GDAXI": "DAX",
    "^N225": "Nikkei 225",
    "BRL=X": "USD/BRL",
}

GLOBAL_STOCKS = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "META": "Meta",
    "BRK-B": "Berkshire Hathaway",
    "JPM": "JPMorgan Chase",
    "V": "Visa",
}

CRYPTOS = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "BNB-USD": "BNB",
    "XRP-USD": "XRP",
    "SOL-USD": "Solana",
    "ADA-USD": "Cardano",
    "DOGE-USD": "Dogecoin",
    "AVAX-USD": "Avalanche",
}

FIIS = {
    "KNRI11.SA": "Kinea Renda Imob.",
    "HGLG11.SA": "CSHG Logística",
    "XPLG11.SA": "XP Log",
    "BTLG11.SA": "BTG Logística",
    "VISC11.SA": "Vinci Shopping Centers",
    "HGRE11.SA": "CSHG Real Estate",
    "MXRF11.SA": "Maxi Renda",
    "BCFF11.SA": "BTG Fundo de Fundos",
    "XPML11.SA": "XP Malls",
    "IRDM11.SA": "Iridium Recebíveis",
}

FII_SECTORS = {
    "KNRI11.SA": "Híbrido",
    "HGLG11.SA": "Logística",
    "XPLG11.SA": "Logística",
    "BTLG11.SA": "Logística",
    "VISC11.SA": "Shopping",
    "HGRE11.SA": "Escritórios",
    "MXRF11.SA": "Papel / CRI",
    "BCFF11.SA": "Fundo de Fundos",
    "XPML11.SA": "Shopping",
    "IRDM11.SA": "Papel / CRI",
}


# ============================================================
#  BUSCA DE DADOS
# ============================================================

@st.cache_data(ttl=300)
def get_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame | None:
    """Retorna histórico de preços OHLCV."""
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)
        return df if not df.empty else None
    except Exception:
        return None


@st.cache_data(ttl=60)
def get_history_crypto(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame | None:
    """Histórico para criptos com cache de 1 minuto."""
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)
        return df if not df.empty else None
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_quote(ticker: str) -> dict | None:
    """Cotação atual: preço, variação, volume."""
    try:
        hist = yf.Ticker(ticker).history(period="5d")
        if hist.empty or len(hist) < 2:
            return None
        price = hist["Close"].iloc[-1]
        prev  = hist["Close"].iloc[-2]
        chg   = price - prev
        chg_p = (chg / prev) * 100
        vol   = hist["Volume"].iloc[-1]
        return {
            "price":      price,
            "change":     chg,
            "change_pct": chg_p,
            "volume":     vol,
            "prev_close": prev,
        }
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_info(ticker: str) -> dict:
    """Informações fundamentalistas do yfinance."""
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


@st.cache_data(ttl=300)
def get_dividends(ticker: str) -> pd.Series:
    """Histórico de dividendos."""
    try:
        return yf.Ticker(ticker).dividends
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=60)
def get_fear_greed() -> dict:
    """Índice Fear & Greed do Bitcoin (alternative.me)."""
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
        d = r.json()["data"][0]
        return {"value": int(d["value"]), "label": d["value_classification"]}
    except Exception:
        return {"value": 50, "label": "Neutral"}


@st.cache_data(ttl=300)
def build_table(tickers: dict) -> pd.DataFrame:
    """
    Monta DataFrame com cotações de múltiplos tickers.
    Colunas: Ticker, Nome, Preço, Variação (%), Volume
    """
    rows = []
    for ticker, name in tickers.items():
        q = get_quote(ticker)
        if q:
            rows.append({
                "Ticker":       ticker.replace(".SA", ""),
                "Nome":         name,
                "Preço":        q["price"],
                "Var. Dia (%)": q["change_pct"],
                "Volume":       q["volume"],
            })
    return pd.DataFrame(rows)


# ============================================================
#  INDICADORES TÉCNICOS
# ============================================================

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona EMA, SMA, RSI, MACD e Bollinger ao DataFrame."""
    if df is None or df.empty:
        return df

    df = df.copy()

    # Médias móveis
    df["EMA9"]   = df["Close"].ewm(span=9,   adjust=False).mean()
    df["EMA20"]  = df["Close"].ewm(span=20,  adjust=False).mean()
    df["SMA50"]  = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()

    # RSI (14)
    delta = df["Close"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD (12, 26, 9)
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]        = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"]   = df["MACD"] - df["MACD_Signal"]

    # Bollinger Bands (20, 2σ)
    sma20        = df["Close"].rolling(20).mean()
    std20        = df["Close"].rolling(20).std()
    df["BB_Mid"] = sma20
    df["BB_Up"]  = sma20 + 2 * std20
    df["BB_Lo"]  = sma20 - 2 * std20

    return df


# ============================================================
#  FORMATAÇÃO
# ============================================================

def fmt_brl(v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_usd(v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"$ {v:,.2f}"


def fmt_big(v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    if v >= 1e12: return f"{v/1e12:.2f}T"
    if v >= 1e9:  return f"{v/1e9:.2f}B"
    if v >= 1e6:  return f"{v/1e6:.2f}M"
    return f"{v:,.0f}"


def fmt_pct(v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v:+.2f}%"
