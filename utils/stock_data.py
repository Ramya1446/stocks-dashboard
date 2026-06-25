"""
stock_data.py — Fetches real-time price, fundamentals, and historical data
for Indian stocks via yfinance (.NS suffix for NSE)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

IST = pytz.timezone("Asia/Kolkata")

# Map of display name → NSE ticker
WATCHLIST = {
    "Tata Power": "TATAPOWER.NS",
    "IRFC": "IRFC.NS",
    "NHPC": "NHPC.NS",
    "Suzlon Energy": "SUZLON.NS",
    "RVNL": "RVNL.NS",
    "IREDA": "IREDA.NS",
    "YES Bank": "YESBANK.NS",
    "Trident": "TRIDENT.NS",
    "Zomato": "ZOMATO.NS",
    "Paytm": "PAYTM.NS",
}


def get_stock_info(ticker_symbol: str) -> dict:
    """Fetch real-time stock info for one ticker."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        prev_close = info.get("previousClose") or price
        change = round(price - prev_close, 2) if price and prev_close else 0
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0

        return {
            "price": price,
            "prev_close": prev_close,
            "change": change,
            "change_pct": change_pct,
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "avg_volume": info.get("averageVolume"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "eps": info.get("trailingEps"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "promoter_holding": info.get("heldPercentInsiders"),
            "institutional_holding": info.get("heldPercentInstitutions"),
            "beta": info.get("beta"),
            "dividend_yield": info.get("dividendYield"),
            "name": info.get("longName", ticker_symbol),
            "error": None,
        }
    except Exception as e:
        return {"error": str(e), "price": None}


def get_all_stocks() -> dict:
    """Fetch data for all watchlist stocks. Returns dict keyed by display name."""
    results = {}
    for display_name, ticker in WATCHLIST.items():
        results[display_name] = {
            "ticker": ticker,
            **get_stock_info(ticker),
        }
    return results


def get_price_history(ticker_symbol: str, period: str = "1mo") -> pd.DataFrame:
    """Returns OHLCV history for charting."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        hist.index = hist.index.tz_convert(IST)
        return hist
    except Exception:
        return pd.DataFrame()


def get_market_indices() -> dict:
    """Fetch Nifty 50 and Sensex live."""
    indices = {
        "Nifty 50": "^NSEI",
        "Sensex": "^BSESN",
        "Bank Nifty": "^NSEBANK",
    }
    results = {}
    for name, sym in indices.items():
        try:
            t = yf.Ticker(sym)
            info = t.info
            price = info.get("regularMarketPrice") or info.get("previousClose")
            prev = info.get("previousClose") or price
            chg = round(price - prev, 2) if price and prev else 0
            chg_pct = round((chg / prev) * 100, 2) if prev else 0
            results[name] = {"price": price, "change": chg, "change_pct": chg_pct}
        except Exception:
            results[name] = {"price": None, "change": 0, "change_pct": 0}
    return results


def get_macro_data() -> dict:
    """Fetch Gold, Crude Oil, USD/INR."""
    macro_tickers = {
        "Gold (₹/10g)": "GC=F",
        "Crude Oil (USD)": "CL=F",
        "USD/INR": "INR=X",
    }
    results = {}
    for name, sym in macro_tickers.items():
        try:
            t = yf.Ticker(sym)
            info = t.info
            price = info.get("regularMarketPrice") or info.get("previousClose")
            prev = info.get("previousClose") or price
            chg_pct = round(((price - prev) / prev) * 100, 2) if prev and price else 0
            results[name] = {"price": price, "change_pct": chg_pct}
        except Exception:
            results[name] = {"price": None, "change_pct": 0}
    return results
