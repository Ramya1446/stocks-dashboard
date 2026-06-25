"""
app.py — Main entry point: Market Overview Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import pytz

from utils.stock_data import get_all_stocks, get_market_indices, get_macro_data, WATCHLIST
from utils.news_fetcher import fetch_market_news
from utils.ai_analyzer import summarize_market_overview

st.set_page_config(
    page_title="StockSense — Your Personal Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .main { background: #0d1117; }

  .metric-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
  }
  .metric-label { font-size: 11px; color: #8b949e; font-weight: 500; text-transform: uppercase; letter-spacing: 0.8px; }
  .metric-value { font-size: 22px; font-weight: 700; color: #f0f6fc; margin: 4px 0 2px; }
  .metric-change-pos { font-size: 13px; color: #3fb950; font-weight: 500; }
  .metric-change-neg { font-size: 13px; color: #f85149; font-weight: 500; }
  .metric-change-neu { font-size: 13px; color: #8b949e; font-weight: 500; }

  .stock-row {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .stock-name { font-size: 15px; font-weight: 600; color: #f0f6fc; }
  .stock-ticker { font-size: 11px; color: #8b949e; }

  .verdict-bullish {
    background: rgba(63, 185, 80, 0.12);
    color: #3fb950;
    border: 1px solid rgba(63, 185, 80, 0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
  }
  .verdict-bearish {
    background: rgba(248, 81, 73, 0.12);
    color: #f85149;
    border: 1px solid rgba(248, 81, 73, 0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
  }
  .verdict-neutral {
    background: rgba(139, 148, 158, 0.15);
    color: #8b949e;
    border: 1px solid rgba(139, 148, 158, 0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
  }

  .news-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
  }
  .news-title { font-size: 14px; font-weight: 600; color: #f0f6fc; line-height: 1.4; }
  .news-meta { font-size: 11px; color: #8b949e; margin-top: 6px; }
  .news-summary { font-size: 13px; color: #c9d1d9; margin-top: 8px; line-height: 1.5; }

  .ai-box {
    background: linear-gradient(135deg, #1a1f2e 0%, #161b22 100%);
    border: 1px solid #30363d;
    border-left: 3px solid #58a6ff;
    border-radius: 10px;
    padding: 18px 20px;
    margin: 12px 0;
  }
  .ai-label { font-size: 10px; color: #58a6ff; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
  .ai-text { font-size: 14px; color: #c9d1d9; margin-top: 8px; line-height: 1.6; }

  .section-header {
    font-size: 18px;
    font-weight: 700;
    color: #f0f6fc;
    margin: 24px 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #21262d;
  }

  .factor-pos { color: #3fb950; font-weight: 600; }
  .factor-neg { color: #f85149; font-weight: 600; }
  .factor-neu { color: #8b949e; font-weight: 600; }

  .score-ring {
    font-size: 40px;
    font-weight: 800;
    text-align: center;
  }

  div[data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 1px solid #21262d;
  }

  .stButton>button {
    background: #21262d;
    color: #f0f6fc;
    border: 1px solid #30363d;
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s;
  }
  .stButton>button:hover {
    background: #30363d;
    border-color: #58a6ff;
  }

  .tag-bullish { background: rgba(63,185,80,0.15); color: #3fb950; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .tag-bearish { background: rgba(248,81,73,0.15); color: #f85149; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .tag-neutral { background: rgba(139,148,158,0.15); color: #8b949e; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 StockSense")
    st.markdown("<p style='color:#8b949e;font-size:12px;margin-top:-8px'>Your personal market dashboard</p>", unsafe_allow_html=True)
    st.divider()

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    st.markdown(f"<p style='color:#8b949e;font-size:12px'>🕐 {now.strftime('%d %b %Y, %I:%M %p IST')}</p>", unsafe_allow_html=True)

    st.markdown("### Navigation")
    st.page_link("app.py", label="🏠 Market Overview", icon=None)
    st.page_link("pages/1_Watchlist.py", label="👁️ Watchlist", icon=None)
    st.page_link("pages/2_Stock_Deep_Dive.py", label="🔍 Stock Deep Dive", icon=None)
    st.page_link("pages/3_News_Feed.py", label="📰 News Feed", icon=None)
    st.page_link("pages/4_Why_Did_It_Move.py", label="❓ Why Did It Move?", icon=None)

    st.divider()
    st.markdown("<p style='color:#8b949e;font-size:11px'>Data: NSE via yfinance · News: Finnhub, Alpha Vantage, Marketaux · AI: Groq LLaMA-3.3</p>", unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("## 🏠 Market Overview")
st.markdown("<p style='color:#8b949e;margin-top:-8px'>Live Indian market pulse — refreshed on demand</p>", unsafe_allow_html=True)

refresh = st.button("🔄 Refresh All Data")
st.divider()


# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)  # Cache 5 mins
def load_indices():
    return get_market_indices()

@st.cache_data(ttl=300)
def load_macro():
    return get_macro_data()

@st.cache_data(ttl=600)
def load_market_news():
    return fetch_market_news()

@st.cache_data(ttl=600)
def load_all_stocks():
    return get_all_stocks()

if refresh:
    st.cache_data.clear()

indices = load_indices()
macro = load_macro()
market_news = load_market_news()
all_stocks = load_all_stocks()


# ── Market Indices ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Market Indices</div>', unsafe_allow_html=True)

cols = st.columns(3)
index_list = list(indices.items())
for i, (name, data) in enumerate(index_list):
    price = data.get("price")
    chg = data.get("change_pct", 0)
    color_class = "metric-change-pos" if chg >= 0 else "metric-change-neg"
    arrow = "▲" if chg >= 0 else "▼"
    price_str = f"{price:,.2f}" if price else "N/A"
    with cols[i]:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">{name}</div>
          <div class="metric-value">{price_str}</div>
          <div class="{color_class}">{arrow} {chg:+.2f}% today</div>
        </div>
        """, unsafe_allow_html=True)


# ── Macro Indicators ──────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🌍 Macro Indicators</div>', unsafe_allow_html=True)

mcols = st.columns(3)
macro_list = list(macro.items())
for i, (name, data) in enumerate(macro_list):
    price = data.get("price")
    chg = data.get("change_pct", 0)
    color_class = "metric-change-pos" if chg >= 0 else "metric-change-neg"
    arrow = "▲" if chg >= 0 else "▼"
    price_str = f"{price:,.2f}" if price else "N/A"
    with mcols[i]:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">{name}</div>
          <div class="metric-value">{price_str}</div>
          <div class="{color_class}">{arrow} {chg:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)


# ── AI Market Summary ─────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🤖 AI Market Summary</div>', unsafe_allow_html=True)

if st.button("✨ Generate Today's Market Summary", key="gen_summary"):
    with st.spinner("Groq is reading the market..."):
        summary = summarize_market_overview(market_news, indices, macro)
    st.markdown(f"""
    <div class="ai-box">
      <div class="ai-label">🤖 Groq AI · Market Overview</div>
      <div class="ai-text">{summary}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Watchlist Snapshot ────────────────────────────────────────────────────────
st.markdown('<div class="section-header">👁️ Watchlist Snapshot</div>', unsafe_allow_html=True)
st.markdown("<p style='color:#8b949e;font-size:13px;margin-top:-8px'>Go to the Watchlist page for full details and filters.</p>", unsafe_allow_html=True)

# Show top movers in a grid
gainers = []
losers = []
for name, data in all_stocks.items():
    if data.get("price") and data.get("error") is None:
        chg = data.get("change_pct", 0)
        if chg > 0:
            gainers.append((name, data))
        else:
            losers.append((name, data))

gainers.sort(key=lambda x: x[1].get("change_pct", 0), reverse=True)
losers.sort(key=lambda x: x[1].get("change_pct", 0))

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### 🟢 Top Gainers")
    for name, data in gainers[:3]:
        price = data.get("price", 0)
        chg = data.get("change_pct", 0)
        ticker = data.get("ticker", "").replace(".NS", "")
        st.markdown(f"""
        <div class="stock-row">
          <div>
            <div class="stock-name">{name}</div>
            <div class="stock-ticker">{ticker}</div>
          </div>
          <div style="text-align:right">
            <div style="color:#f0f6fc;font-weight:700;font-size:16px">₹{price:.2f}</div>
            <div class="metric-change-pos">▲ {chg:+.2f}%</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("#### 🔴 Top Losers")
    for name, data in losers[:3]:
        price = data.get("price", 0)
        chg = data.get("change_pct", 0)
        ticker = data.get("ticker", "").replace(".NS", "")
        st.markdown(f"""
        <div class="stock-row">
          <div>
            <div class="stock-name">{name}</div>
            <div class="stock-ticker">{ticker}</div>
          </div>
          <div style="text-align:right">
            <div style="color:#f0f6fc;font-weight:700;font-size:16px">₹{price:.2f}</div>
            <div class="metric-change-neg">▼ {chg:.2f}%</div>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ── Live Market News ──────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📰 Live Market News</div>', unsafe_allow_html=True)

if market_news:
    for article in market_news[:6]:
        title = article.get("title", "")
        summary = article.get("summary", "")
        source = article.get("source", "")
        published = article.get("published_at", "")
        url = article.get("url", "#")
        st.markdown(f"""
        <div class="news-card">
          <div class="news-title"><a href="{url}" target="_blank" style="color:#f0f6fc;text-decoration:none;">{title}</a></div>
          <div class="news-meta">📌 {source} · {published}</div>
          {f'<div class="news-summary">{summary[:200]}...</div>' if summary else ''}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No market news fetched. Check your API keys in secrets.")
