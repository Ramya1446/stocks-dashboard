"""
pages/4_Why_Did_It_Move.py — "Why did this stock move today?"
Fetches price change + news + volume, sends to Groq for explanation.
"""

import streamlit as st
import plotly.graph_objects as go
from utils.stock_data import get_all_stocks, get_price_history, WATCHLIST
from utils.news_fetcher import fetch_all_news
from utils.ai_analyzer import explain_stock_move

st.set_page_config(page_title="Why Did It Move — StockSense", page_icon="❓", layout="wide")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .main { background: #0d1117; }
  div[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #21262d; }

  .page-title { font-size: 28px; font-weight: 800; color: #f0f6fc; }
  .page-sub { font-size: 14px; color: #8b949e; margin-top: -6px; margin-bottom: 20px; }
  .section-header { font-size: 16px; font-weight: 700; color: #f0f6fc; margin: 28px 0 14px; padding-bottom: 8px; border-bottom: 1px solid #21262d; }

  .move-hero {
    background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
    border: 1px solid #30363d;
    border-radius: 18px;
    padding: 32px 36px;
    margin-bottom: 28px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .move-hero::after {
    content: '';
    position: absolute;
    top: -40%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(88,166,255,0.06) 0%, transparent 70%);
    pointer-events: none;
  }

  .move-company { font-size: 13px; color: #8b949e; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; }
  .move-price { font-size: 52px; font-weight: 900; color: #f0f6fc; line-height: 1.1; margin: 8px 0; }
  .move-change-pos { font-size: 28px; font-weight: 800; color: #3fb950; }
  .move-change-neg { font-size: 28px; font-weight: 800; color: #f85149; }
  .move-change-flat { font-size: 28px; font-weight: 800; color: #d29922; }

  .reason-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 14px;
    display: flex;
    align-items: flex-start;
    gap: 16px;
  }
  .reason-num { font-size: 20px; font-weight: 800; color: #58a6ff; min-width: 30px; margin-top: 2px; }
  .reason-text { font-size: 15px; color: #c9d1d9; font-weight: 500; line-height: 1.5; }

  .verdict-box {
    border-radius: 16px;
    padding: 24px 28px;
    text-align: center;
    margin: 20px 0;
  }
  .verdict-bull { background: linear-gradient(135deg, rgba(63,185,80,0.12) 0%, rgba(63,185,80,0.05) 100%); border: 1px solid rgba(63,185,80,0.3); }
  .verdict-bear { background: linear-gradient(135deg, rgba(248,81,73,0.12) 0%, rgba(248,81,73,0.05) 100%); border: 1px solid rgba(248,81,73,0.3); }
  .verdict-neu { background: linear-gradient(135deg, rgba(210,153,34,0.12) 0%, rgba(210,153,34,0.05) 100%); border: 1px solid rgba(210,153,34,0.3); }
  .verdict-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
  .verdict-text-bull { font-size: 18px; font-weight: 700; color: #3fb950; margin-top: 8px; line-height: 1.5; }
  .verdict-text-bear { font-size: 18px; font-weight: 700; color: #f85149; margin-top: 8px; line-height: 1.5; }
  .verdict-text-neu { font-size: 18px; font-weight: 700; color: #d29922; margin-top: 8px; line-height: 1.5; }

  .volume-pill {
    display: inline-block;
    border-radius: 20px;
    padding: 6px 20px;
    font-size: 13px;
    font-weight: 700;
    margin-top: 12px;
  }
  .vol-high { background: rgba(63,185,80,0.15); color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }
  .vol-sell { background: rgba(248,81,73,0.15); color: #f85149; border: 1px solid rgba(248,81,73,0.3); }
  .vol-normal { background: rgba(210,153,34,0.15); color: #d29922; border: 1px solid rgba(210,153,34,0.3); }

  .news-snippet { background: #161b22; border: 1px solid #21262d; border-left: 3px solid #58a6ff; border-radius: 10px; padding: 12px 16px; margin-bottom: 10px; }
  .news-snip-title { font-size: 13px; font-weight: 600; color: #f0f6fc; line-height: 1.4; }
  .news-snip-meta { font-size: 11px; color: #8b949e; margin-top: 4px; }

  .stButton>button { background: linear-gradient(135deg, #1f6feb 0%, #58a6ff 100%); color: #fff; border: none; border-radius: 10px; font-weight: 600; font-size: 15px; padding: 10px 24px; }
  .stButton>button:hover { opacity: 0.9; }
  .stSelectbox label { color: #8b949e !important; }

  .movers-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px; }
  .mover-chip {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 14px 16px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .mover-chip:hover { border-color: #58a6ff; background: #1c2233; }
  .mover-chip-name { font-size: 13px; font-weight: 600; color: #f0f6fc; }
  .mover-chip-chg-pos { font-size: 14px; font-weight: 800; color: #3fb950; }
  .mover-chip-chg-neg { font-size: 14px; font-weight: 800; color: #f85149; }
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

st.markdown('<div class="page-title">❓ Why Did It Move Today?</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Pick any stock. Groq explains the move using live news, volume, and price data.</div>', unsafe_allow_html=True)

# ── Load stocks ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_stocks():
    return get_all_stocks()

with st.spinner("Loading live prices..."):
    all_stocks = load_stocks()

# ── Top Movers Quick Select ───────────────────────────────────────────────────
st.markdown('<div class="section-header">🏃 Today\'s Movers — Click to analyze</div>', unsafe_allow_html=True)

sorted_stocks = sorted(
    [(n, d) for n, d in all_stocks.items() if d.get("price") and d.get("error") is None],
    key=lambda x: abs(x[1].get("change_pct", 0)),
    reverse=True
)

# Show top 8 movers as quick-select chips using columns
mover_cols = st.columns(4)
for idx, (name, data) in enumerate(sorted_stocks[:8]):
    chg = data.get("change_pct", 0)
    price = data.get("price", 0)
    chg_str = f"▲ {chg:+.2f}%" if chg >= 0 else f"▼ {chg:.2f}%"
    col = mover_cols[idx % 4]
    with col:
        if st.button(f"{name}\n{chg_str}", key=f"mover_{name}", use_container_width=True):
            st.session_state["selected_company"] = name

st.divider()

# ── Stock Selector ─────────────────────────────────────────────────────────────
default_idx = list(WATCHLIST.keys()).index(st.session_state.get("selected_company", list(WATCHLIST.keys())[0]))
selected = st.selectbox("Or choose manually:", list(WATCHLIST.keys()), index=default_idx)

analyze_btn = st.button(f"🔍 Explain why {selected} moved today", use_container_width=True)

# ── Load + Display ─────────────────────────────────────────────────────────────
if analyze_btn:
    ticker = WATCHLIST[selected]
    data = all_stocks.get(selected, {})
    price = data.get("price", 0)
    chg = data.get("change_pct", 0)
    change = data.get("change", 0)
    volume = data.get("volume")
    avg_vol = data.get("avg_volume")

    # Hero section
    chg_class = "move-change-pos" if chg > 0 else "move-change-neg" if chg < 0 else "move-change-flat"
    arrow = "▲" if chg > 0 else "▼" if chg < 0 else "→"
    move_label = "GAINED" if chg > 0 else "LOST" if chg < 0 else "UNCHANGED"

    st.markdown(f"""
    <div class="move-hero">
      <div class="move-company">{selected} · {ticker.replace('.NS','')} · NSE</div>
      <div class="move-price">₹{price:,.2f}</div>
      <div class="{chg_class}">{arrow} ₹{abs(change):.2f} &nbsp;({chg:+.2f}%) &nbsp;·&nbsp; {move_label} today</div>
    </div>
    """, unsafe_allow_html=True)

    col_chart, col_stats = st.columns([2, 1])

    with col_chart:
        with st.spinner("Loading intraday chart..."):
            hist = get_price_history(ticker, "5d")

        if not hist.empty:
            fig = go.Figure()
            colors = ["rgba(63,185,80,0.8)" if c >= o else "rgba(248,81,73,0.8)"
                      for c, o in zip(hist["Close"], hist["Open"])]
            fig.add_trace(go.Candlestick(
                x=hist.index, open=hist["Open"], high=hist["High"],
                low=hist["Low"], close=hist["Close"],
                increasing_line_color="#3fb950", decreasing_line_color="#f85149",
                increasing_fillcolor="rgba(63,185,80,0.3)", decreasing_fillcolor="rgba(248,81,73,0.3)",
                name="Price",
            ))
            fig.update_layout(
                paper_bgcolor="#161b22", plot_bgcolor="#161b22",
                font=dict(family="Inter", color="#8b949e"),
                xaxis=dict(gridcolor="#21262d", rangeslider_visible=False, color="#8b949e"),
                yaxis=dict(gridcolor="#21262d", color="#8b949e", side="right"),
                height=260, margin=dict(l=10, r=10, t=10, b=10),
                xaxis_rangebreaks=[dict(bounds=["sat", "mon"])],
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_stats:
        vol_ratio = (volume / avg_vol) if volume and avg_vol else 1
        vol_signal = "High buying 🔥" if vol_ratio > 1.3 else "High selling 📉" if vol_ratio < 0.7 else "Normal activity"
        vol_class = "vol-high" if vol_ratio > 1.3 else "vol-sell" if vol_ratio < 0.7 else "vol-normal"

        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #21262d;border-radius:14px;padding:20px;margin-bottom:12px;">
          <div style="font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:1px;">Volume Signal</div>
          <div style="font-size:28px;font-weight:900;color:#f0f6fc;margin:8px 0 4px;">{vol_ratio:.1f}x</div>
          <span class="volume-pill {vol_class}">{vol_signal}</span>
          <div style="font-size:11px;color:#8b949e;margin-top:10px;">Today: {volume:,}<br>Avg: {avg_vol:,}</div>
        </div>
        """, unsafe_allow_html=True)

        w52h = data.get("52w_high", 0)
        w52l = data.get("52w_low", 0)
        if w52h and w52l and w52h > w52l:
            pos_in_range = ((price - w52l) / (w52h - w52l)) * 100
            st.markdown(f"""
            <div style="background:#161b22;border:1px solid #21262d;border-radius:14px;padding:20px;">
              <div style="font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">52-Week Position</div>
              <div style="background:#21262d;border-radius:6px;height:8px;overflow:hidden;">
                <div style="width:{pos_in_range:.0f}%;background:linear-gradient(90deg,#f85149,#d29922,#3fb950);height:8px;border-radius:6px;"></div>
              </div>
              <div style="display:flex;justify-content:space-between;margin-top:6px;font-size:11px;color:#8b949e;">
                <span>₹{w52l:.0f}</span>
                <span style="color:#58a6ff;font-weight:700;">{pos_in_range:.0f}%</span>
                <span>₹{w52h:.0f}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # Fetch news
    st.markdown('<div class="section-header">📰 News Used for Analysis</div>', unsafe_allow_html=True)
    with st.spinner("Fetching latest news..."):
        news = fetch_all_news(selected)

    if news:
        for article in news[:4]:
            title = article.get("title", "")
            source = article.get("source", "")
            published = article.get("published_at", "")
            url = article.get("url", "#")
            st.markdown(f"""
            <div class="news-snippet">
              <div class="news-snip-title"><a href="{url}" target="_blank" style="color:#f0f6fc;text-decoration:none;">{title}</a></div>
              <div class="news-snip-meta">📌 {source} · {published}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No specific news found for this company. AI will analyze based on price + volume signals.")

    # AI Explanation
    st.markdown('<div class="section-header">🤖 AI Explanation</div>', unsafe_allow_html=True)
    with st.spinner(f"Groq is explaining why {selected} moved {chg:+.2f}%..."):
        ai = explain_stock_move(selected, chg, news, data)

    reasons = ai.get("reasons", [])
    ai_verdict = ai.get("ai_verdict", "")
    momentum = ai.get("momentum", "Neutral")
    vol_ai_signal = ai.get("volume_signal", "Normal")

    # Reasons
    for i, reason in enumerate(reasons, 1):
        st.markdown(f"""
        <div class="reason-card">
          <div class="reason-num">#{i}</div>
          <div class="reason-text">{reason}</div>
        </div>
        """, unsafe_allow_html=True)

    # AI Verdict box
    verdict_box_class = "verdict-bull" if momentum == "Bullish" else "verdict-bear" if momentum == "Bearish" else "verdict-neu"
    verdict_text_class = "verdict-text-bull" if momentum == "Bullish" else "verdict-text-bear" if momentum == "Bearish" else "verdict-text-neu"
    momentum_emoji = "🟢" if momentum == "Bullish" else "🔴" if momentum == "Bearish" else "🟡"

    st.markdown(f"""
    <div class="verdict-box {verdict_box_class}">
      <div class="verdict-label">🤖 AI Verdict · Short-term Momentum</div>
      <div class="{verdict_text_class}">{momentum_emoji} {ai_verdict}</div>
      <div style="margin-top:12px;">
        <span class="volume-pill {'vol-high' if 'buying' in vol_ai_signal.lower() else 'vol-sell' if 'selling' in vol_ai_signal.lower() else 'vol-normal'}">
          📊 Volume: {vol_ai_signal}
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # Landing state
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;background:#161b22;border:1px solid #21262d;border-radius:18px;margin-top:20px;">
      <div style="font-size:56px;margin-bottom:16px;">🤔</div>
      <div style="font-size:20px;font-weight:700;color:#f0f6fc;margin-bottom:8px;">Pick a stock above</div>
      <div style="font-size:14px;color:#8b949e;max-width:400px;margin:0 auto;line-height:1.6;">
        Click any of the top movers or choose from the dropdown.<br>
        Groq will explain the move using real-time news, volume data, and price action.
      </div>
    </div>
    """, unsafe_allow_html=True)
