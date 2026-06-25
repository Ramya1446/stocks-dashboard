"""
pages/1_Watchlist.py — Full watchlist with price filters, live data, AI one-liners
"""

import streamlit as st
import pandas as pd
from utils.stock_data import get_all_stocks, WATCHLIST
from utils.news_fetcher import fetch_all_news
from utils.ai_analyzer import get_company_ai_score

st.set_page_config(page_title="Watchlist — StockSense", page_icon="👁️", layout="wide")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .metric-card { background:#161b22; border:1px solid #21262d; border-radius:12px; padding:16px 20px; margin-bottom:12px; }
  .metric-label { font-size:11px; color:#8b949e; font-weight:500; text-transform:uppercase; letter-spacing:0.8px; }
  .metric-value { font-size:20px; font-weight:700; color:#f0f6fc; margin:4px 0 2px; }
  .metric-change-pos { font-size:13px; color:#3fb950; font-weight:500; }
  .metric-change-neg { font-size:13px; color:#f85149; font-weight:500; }
  .stock-card { background:#161b22; border:1px solid #21262d; border-radius:12px; padding:18px 22px; margin-bottom:14px; }
  .stock-name { font-size:17px; font-weight:700; color:#f0f6fc; }
  .stock-ticker { font-size:11px; color:#8b949e; margin-top:2px; }
  .section-header { font-size:18px; font-weight:700; color:#f0f6fc; margin:24px 0 12px; padding-bottom:8px; border-bottom:1px solid #21262d; }
  .ai-box { background:linear-gradient(135deg,#1a1f2e 0%,#161b22 100%); border:1px solid #30363d; border-left:3px solid #58a6ff; border-radius:10px; padding:12px 16px; margin:10px 0; }
  .ai-label { font-size:10px; color:#58a6ff; font-weight:600; text-transform:uppercase; letter-spacing:1px; }
  .ai-text { font-size:13px; color:#c9d1d9; margin-top:6px; line-height:1.5; }
  .badge { display:inline-block; border-radius:20px; padding:3px 12px; font-size:12px; font-weight:600; }
  .badge-bull { background:rgba(63,185,80,0.12); color:#3fb950; border:1px solid rgba(63,185,80,0.3); }
  .badge-bear { background:rgba(248,81,73,0.12); color:#f85149; border:1px solid rgba(248,81,73,0.3); }
  .badge-neu { background:rgba(139,148,158,0.15); color:#8b949e; border:1px solid rgba(139,148,158,0.3); }
  .score-circle { font-size:32px; font-weight:800; }
  .data-row { display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid #21262d; font-size:13px; color:#c9d1d9; }
  .data-label { color:#8b949e; }
  div[data-testid="stSidebar"] { background:#0d1117; border-right:1px solid #21262d; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 📈 StockSense")
    st.divider()
    st.page_link("app.py", label="🏠 Market Overview")
    st.page_link("pages/1_Watchlist.py", label="👁️ Watchlist")
    st.page_link("pages/2_Stock_Deep_Dive.py", label="🔍 Stock Deep Dive")
    st.page_link("pages/3_News_Feed.py", label="📰 News Feed")
    st.page_link("pages/4_Why_Did_It_Move.py", label="❓ Why Did It Move?")

st.markdown("## 👁️ Watchlist")
st.markdown("<p style='color:#8b949e;margin-top:-8px'>Live prices, fundamentals, and AI verdicts for your tracked stocks.</p>", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🔽 Filters</div>', unsafe_allow_html=True)
fcol1, fcol2, fcol3 = st.columns(3)
with fcol1:
    max_price = st.number_input("Max Share Price (₹)", min_value=1, max_value=10000, value=1000, step=50)
with fcol2:
    min_mcap_cr = st.number_input("Min Market Cap (₹ Cr)", min_value=0, max_value=100000, value=0, step=500)
with fcol3:
    show_only_positive = st.checkbox("Show only gainers today", value=False)

refresh = st.button("🔄 Refresh Watchlist")
if refresh:
    st.cache_data.clear()

st.divider()

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_stocks():
    return get_all_stocks()

with st.spinner("Fetching live prices from NSE..."):
    all_stocks = load_stocks()

# ── Filter & render ───────────────────────────────────────────────────────────
filtered = {
    name: data for name, data in all_stocks.items()
    if (
        data.get("price") is not None
        and data.get("price", 9999) <= max_price
        and (data.get("market_cap") or 0) / 1e7 >= min_mcap_cr  # Convert to Cr
        and (not show_only_positive or data.get("change_pct", 0) > 0)
        and data.get("error") is None
    )
}

st.markdown(f'<div class="section-header">📋 {len(filtered)} stocks match your filters</div>', unsafe_allow_html=True)

if not filtered:
    st.warning("No stocks match your current filters. Try relaxing the constraints.")
    st.stop()

for name, data in filtered.items():
    price = data.get("price", 0)
    chg = data.get("change_pct", 0)
    change = data.get("change", 0)
    ticker = data.get("ticker", "").replace(".NS", "")
    mcap = data.get("market_cap")
    pe = data.get("pe_ratio")
    volume = data.get("volume")
    avg_vol = data.get("avg_volume")
    promoter = data.get("promoter_holding")
    institutional = data.get("institutional_holding")
    w52h = data.get("52w_high")
    w52l = data.get("52w_low")
    beta = data.get("beta")
    div_yield = data.get("dividend_yield")

    chg_class = "metric-change-pos" if chg >= 0 else "metric-change-neg"
    arrow = "▲" if chg >= 0 else "▼"
    badge_class = "badge-bull" if chg >= 0 else "badge-bear"

    with st.container():
        st.markdown(f"""
        <div class="stock-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;">
            <div>
              <div class="stock-name">{name}</div>
              <div class="stock-ticker">{ticker} · NSE</div>
            </div>
            <div style="text-align:right">
              <div style="font-size:24px;font-weight:800;color:#f0f6fc;">₹{price:.2f}</div>
              <div class="{chg_class}">{arrow} ₹{abs(change):.2f} ({chg:+.2f}%)</div>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:16px;">
            <div>
              <div class="data-label" style="font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:0.7px;">Market Cap</div>
              <div style="font-size:14px;font-weight:600;color:#f0f6fc;margin-top:3px;">
                {'₹' + str(round(mcap/1e9, 1)) + ' B' if mcap else 'N/A'}
              </div>
            </div>
            <div>
              <div class="data-label" style="font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:0.7px;">P/E Ratio</div>
              <div style="font-size:14px;font-weight:600;color:#f0f6fc;margin-top:3px;">{round(pe, 1) if pe else 'N/A'}</div>
            </div>
            <div>
              <div class="data-label" style="font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:0.7px;">Promoter %</div>
              <div style="font-size:14px;font-weight:600;color:#f0f6fc;margin-top:3px;">{round(promoter*100, 1) if promoter else 'N/A'}%</div>
            </div>
            <div>
              <div class="data-label" style="font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:0.7px;">FII/Inst %</div>
              <div style="font-size:14px;font-weight:600;color:#f0f6fc;margin-top:3px;">{round(institutional*100, 1) if institutional else 'N/A'}%</div>
            </div>
            <div>
              <div class="data-label" style="font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:0.7px;">52W High</div>
              <div style="font-size:14px;font-weight:600;color:#f0f6fc;margin-top:3px;">₹{w52h:.2f if w52h else 'N/A'}</div>
            </div>
            <div>
              <div class="data-label" style="font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:0.7px;">52W Low</div>
              <div style="font-size:14px;font-weight:600;color:#f0f6fc;margin-top:3px;">₹{w52l:.2f if w52l else 'N/A'}</div>
            </div>
            <div>
              <div class="data-label" style="font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:0.7px;">Beta</div>
              <div style="font-size:14px;font-weight:600;color:#f0f6fc;margin-top:3px;">{round(beta, 2) if beta else 'N/A'}</div>
            </div>
            <div>
              <div class="data-label" style="font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:0.7px;">Div Yield</div>
              <div style="font-size:14px;font-weight:600;color:#f0f6fc;margin-top:3px;">{round(div_yield*100, 2) if div_yield else 'N/A'}%</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # AI Score button per stock
        with st.expander(f"🤖 AI Analysis for {name}"):
            if st.button(f"Generate AI Score for {name}", key=f"ai_{name}"):
                with st.spinner("Fetching news + running Groq analysis..."):
                    news = fetch_all_news(name)
                    ai = get_company_ai_score(name, data, news)

                score = ai.get("confidence_score", 50)
                verdict = ai.get("verdict", "Neutral")
                one_liner = ai.get("one_liner", "")
                reasoning = ai.get("reasoning", "")
                factors = ai.get("factors", {})

                score_color = "#3fb950" if score >= 65 else "#f85149" if score <= 40 else "#d29922"
                verdict_class = "badge-bull" if verdict == "Bullish" else "badge-bear" if verdict == "Bearish" else "badge-neu"

                col_score, col_detail = st.columns([1, 3])
                with col_score:
                    st.markdown(f"""
                    <div style="text-align:center;padding:20px;">
                      <div style="font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:1px;">AI Confidence</div>
                      <div style="font-size:52px;font-weight:900;color:{score_color};line-height:1;">{score}</div>
                      <div style="font-size:12px;color:#8b949e;">/100</div>
                      <div style="margin-top:10px;"><span class="badge {verdict_class}">{verdict}</span></div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_detail:
                    st.markdown(f"""
                    <div class="ai-box">
                      <div class="ai-label">🤖 AI Verdict</div>
                      <div class="ai-text"><strong>{one_liner}</strong></div>
                      <div class="ai-text" style="margin-top:8px;font-size:12px;color:#8b949e;">{reasoning}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if factors:
                        st.markdown("**Factor Analysis:**")
                        for factor, status in factors.items():
                            icon = "🟢" if status == "Positive" else "🔴" if status == "Negative" else "🟡"
                            st.markdown(f"{icon} **{factor}:** {status}")
