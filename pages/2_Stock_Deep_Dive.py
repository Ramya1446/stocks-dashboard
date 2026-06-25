"""
pages/2_Stock_Deep_Dive.py — Deep analysis for a single stock
Price chart + fundamentals + news + AI factor dashboard
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.stock_data import get_all_stocks, get_price_history, WATCHLIST
from utils.news_fetcher import fetch_all_news
from utils.ai_analyzer import get_company_ai_score, summarize_article

st.set_page_config(page_title="Stock Deep Dive — StockSense", page_icon="🔍", layout="wide")

COMMON_STYLE = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .main { background: #0d1117; }
  div[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #21262d; }

  .page-title { font-size: 28px; font-weight: 800; color: #f0f6fc; }
  .page-sub { font-size: 14px; color: #8b949e; margin-top: -6px; margin-bottom: 20px; }
  .section-header { font-size: 16px; font-weight: 700; color: #f0f6fc; margin: 28px 0 14px; padding-bottom: 8px; border-bottom: 1px solid #21262d; display: flex; align-items: center; gap: 8px; }

  .stat-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 14px;
    padding: 18px 20px;
    transition: border-color 0.2s;
  }
  .stat-card:hover { border-color: #58a6ff; }
  .stat-label { font-size: 10px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
  .stat-value { font-size: 20px; font-weight: 800; color: #f0f6fc; margin: 6px 0 2px; }
  .stat-sub { font-size: 12px; color: #8b949e; }

  .price-hero { background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%); border: 1px solid #30363d; border-radius: 16px; padding: 28px 32px; margin-bottom: 24px; }
  .hero-name { font-size: 13px; color: #8b949e; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600; }
  .hero-price { font-size: 48px; font-weight: 900; color: #f0f6fc; line-height: 1.1; }
  .hero-change-pos { font-size: 18px; font-weight: 700; color: #3fb950; }
  .hero-change-neg { font-size: 18px; font-weight: 700; color: #f85149; }

  .factor-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #21262d;
  }
  .factor-name { font-size: 14px; color: #c9d1d9; font-weight: 500; }
  .pill-pos { background: rgba(63,185,80,0.15); color: #3fb950; border: 1px solid rgba(63,185,80,0.3); border-radius: 20px; padding: 4px 14px; font-size: 12px; font-weight: 700; }
  .pill-neg { background: rgba(248,81,73,0.15); color: #f85149; border: 1px solid rgba(248,81,73,0.3); border-radius: 20px; padding: 4px 14px; font-size: 12px; font-weight: 700; }
  .pill-neu { background: rgba(210,153,34,0.15); color: #d29922; border: 1px solid rgba(210,153,34,0.3); border-radius: 20px; padding: 4px 14px; font-size: 12px; font-weight: 700; }

  .news-card { background: #161b22; border: 1px solid #21262d; border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; transition: border-color 0.2s; }
  .news-card:hover { border-color: #58a6ff; }
  .news-title { font-size: 14px; font-weight: 600; color: #f0f6fc; line-height: 1.5; }
  .news-meta { font-size: 11px; color: #8b949e; margin-top: 6px; }
  .news-body { font-size: 13px; color: #8b949e; margin-top: 8px; line-height: 1.6; }

  .ai-insight { background: linear-gradient(135deg, #1c2233 0%, #161b22 100%); border: 1px solid #30363d; border-left: 3px solid #58a6ff; border-radius: 10px; padding: 14px 18px; margin: 10px 0; }
  .ai-tag { font-size: 10px; color: #58a6ff; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
  .ai-body { font-size: 13px; color: #c9d1d9; margin-top: 8px; line-height: 1.6; }

  .score-ring { text-align: center; padding: 20px; }
  .score-num { font-size: 60px; font-weight: 900; line-height: 1; }
  .score-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }

  .verdict-tag { display: inline-block; border-radius: 20px; padding: 5px 18px; font-size: 13px; font-weight: 700; margin-top: 10px; }
  .vt-bull { background: rgba(63,185,80,0.15); color: #3fb950; border: 1px solid rgba(63,185,80,0.35); }
  .vt-bear { background: rgba(248,81,73,0.15); color: #f85149; border: 1px solid rgba(248,81,73,0.35); }
  .vt-neu { background: rgba(210,153,34,0.15); color: #d29922; border: 1px solid rgba(210,153,34,0.35); }

  .stButton>button { background: #21262d; color: #f0f6fc; border: 1px solid #30363d; border-radius: 8px; font-weight: 500; }
  .stButton>button:hover { background: #30363d; border-color: #58a6ff; }
  .stSelectbox label { color: #8b949e !important; }
</style>
"""
st.markdown(COMMON_STYLE, unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 StockSense")
    st.divider()
    st.page_link("app.py", label="🏠 Market Overview")
    st.page_link("pages/1_Watchlist.py", label="👁️ Watchlist")
    st.page_link("pages/2_Stock_Deep_Dive.py", label="🔍 Stock Deep Dive")
    st.page_link("pages/3_News_Feed.py", label="📰 News Feed")
    st.page_link("pages/4_Why_Did_It_Move.py", label="❓ Why Did It Move?")

# ── Stock Selector ─────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">🔍 Stock Deep Dive</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Full analysis — price chart, fundamentals, news, and AI factor dashboard.</div>', unsafe_allow_html=True)

selected = st.selectbox("Choose a stock", list(WATCHLIST.keys()), index=0)
period = st.select_slider("Chart Period", options=["5d", "1mo", "3mo", "6mo", "1y"], value="1mo")

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()

ticker = WATCHLIST[selected]

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_stock_data():
    return get_all_stocks()

@st.cache_data(ttl=300)
def load_history(sym, p):
    return get_price_history(sym, p)

@st.cache_data(ttl=600)
def load_news(name):
    return fetch_all_news(name)

with st.spinner(f"Loading {selected} data..."):
    all_stocks = load_stock_data()
    hist = load_history(ticker, period)
    news = load_news(selected)

data = all_stocks.get(selected, {})

if data.get("error"):
    st.error(f"Error fetching data: {data['error']}")
    st.stop()

price = data.get("price", 0)
chg = data.get("change_pct", 0)
change = data.get("change", 0)
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
eps = data.get("eps")
sector = data.get("sector", "N/A")

chg_class = "hero-change-pos" if chg >= 0 else "hero-change-neg"
arrow = "▲" if chg >= 0 else "▼"

# ── Price Hero ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="price-hero">
  <div class="hero-name">{ticker.replace('.NS','')} · NSE · {sector}</div>
  <div class="hero-price">₹{price:,.2f}</div>
  <div class="{chg_class}">{arrow} ₹{abs(change):.2f} &nbsp;({chg:+.2f}%) today</div>
</div>
""", unsafe_allow_html=True)

# ── Key Stats Grid ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Key Fundamentals</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
stats = [
    ("Market Cap", f"₹{round(mcap/1e9, 1)}B" if mcap else "N/A", "Total company value"),
    ("P/E Ratio", f"{round(pe,1)}" if pe else "N/A", "Price-to-earnings"),
    ("EPS", f"₹{round(eps,2)}" if eps else "N/A", "Earnings per share"),
    ("Beta", f"{round(beta,2)}" if beta else "N/A", "Market sensitivity"),
    ("52W High", f"₹{w52h:.2f}" if w52h else "N/A", "1-year peak"),
    ("52W Low", f"₹{w52l:.2f}" if w52l else "N/A", "1-year bottom"),
    ("Promoter %", f"{round(promoter*100,1)}%" if promoter else "N/A", "Founder stake"),
    ("FII/Inst %", f"{round(institutional*100,1)}%" if institutional else "N/A", "Institutional stake"),
]
cols = [c1, c2, c3, c4]
for i, (label, val, sub) in enumerate(stats):
    with cols[i % 4]:
        st.markdown(f"""
        <div class="stat-card" style="margin-bottom:12px;">
          <div class="stat-label">{label}</div>
          <div class="stat-value">{val}</div>
          <div class="stat-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

# Volume bar
if volume and avg_vol:
    vol_ratio = volume / avg_vol
    vol_color = "#3fb950" if vol_ratio > 1.3 else "#f85149" if vol_ratio < 0.7 else "#d29922"
    vol_label = "High activity 🔥" if vol_ratio > 1.3 else "Low activity" if vol_ratio < 0.7 else "Normal"
    st.markdown(f"""
    <div class="stat-card" style="margin-bottom:20px;">
      <div class="stat-label">Volume vs Average</div>
      <div style="display:flex;align-items:center;gap:14px;margin-top:8px;">
        <div style="flex:1;background:#21262d;border-radius:6px;height:8px;overflow:hidden;">
          <div style="width:{min(vol_ratio*50, 100)}%;background:{vol_color};height:8px;border-radius:6px;"></div>
        </div>
        <div style="font-size:14px;font-weight:700;color:{vol_color};">{vol_ratio:.1f}x · {vol_label}</div>
      </div>
      <div class="stat-sub" style="margin-top:6px;">Today: {volume:,} · Avg: {avg_vol:,}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Price Chart ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📈 Price Chart</div>', unsafe_allow_html=True)

if not hist.empty:
    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist["Open"], high=hist["High"],
        low=hist["Low"], close=hist["Close"],
        increasing_line_color="#3fb950", decreasing_line_color="#f85149",
        increasing_fillcolor="rgba(63,185,80,0.3)", decreasing_fillcolor="rgba(248,81,73,0.3)",
        name="Price",
    ))

    # Volume bars at bottom
    vol_colors = ["rgba(63,185,80,0.5)" if c >= o else "rgba(248,81,73,0.5)"
                  for c, o in zip(hist["Close"], hist["Open"])]
    fig.add_trace(go.Bar(
        x=hist.index, y=hist["Volume"],
        marker_color=vol_colors,
        name="Volume",
        yaxis="y2",
        showlegend=False,
    ))

    fig.update_layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(family="Inter", color="#8b949e"),
        xaxis=dict(gridcolor="#21262d", showgrid=True, rangeslider_visible=False, color="#8b949e"),
        yaxis=dict(gridcolor="#21262d", showgrid=True, color="#8b949e", side="right", title="Price (₹)"),
        yaxis2=dict(overlaying="y", side="left", showgrid=False, color="#8b949e", title="Volume", showticklabels=False),
        height=420,
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#21262d"),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Chart data not available for this period.")

# ── AI Factor Dashboard ────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🤖 AI Factor Dashboard</div>', unsafe_allow_html=True)

if st.button("✨ Run AI Analysis", key="run_ai"):
    with st.spinner("Groq is analyzing news + fundamentals..."):
        ai = get_company_ai_score(selected, data, news)

    st.session_state[f"ai_{selected}"] = ai

if f"ai_{selected}" in st.session_state:
    ai = st.session_state[f"ai_{selected}"]
    score = ai.get("confidence_score", 50)
    verdict = ai.get("verdict", "Neutral")
    one_liner = ai.get("one_liner", "")
    reasoning = ai.get("reasoning", "")
    factors = ai.get("factors", {})

    score_color = "#3fb950" if score >= 65 else "#f85149" if score <= 40 else "#d29922"
    vt_class = "vt-bull" if verdict == "Bullish" else "vt-bear" if verdict == "Bearish" else "vt-neu"

    left, right = st.columns([1, 2])
    with left:
        st.markdown(f"""
        <div class="score-ring">
          <div class="score-num" style="color:{score_color}">{score}</div>
          <div class="score-label">AI Confidence Score</div>
          <div><span class="verdict-tag {vt_class}">{verdict}</span></div>
        </div>
        """, unsafe_allow_html=True)

        # Gauge chart
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            gauge=dict(
                axis=dict(range=[0, 100], tickcolor="#8b949e", tickfont=dict(color="#8b949e")),
                bar=dict(color=score_color, thickness=0.25),
                bgcolor="#161b22",
                borderwidth=0,
                steps=[
                    dict(range=[0, 40], color="rgba(248,81,73,0.15)"),
                    dict(range=[40, 65], color="rgba(210,153,34,0.15)"),
                    dict(range=[65, 100], color="rgba(63,185,80,0.15)"),
                ],
            ),
            number=dict(font=dict(color=score_color, size=36), suffix="/100"),
        ))
        fig_gauge.update_layout(
            paper_bgcolor="#161b22", font_color="#8b949e",
            height=200, margin=dict(l=20, r=20, t=20, b=10),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with right:
        st.markdown(f"""
        <div class="ai-insight">
          <div class="ai-tag">🤖 AI Verdict · {selected}</div>
          <div class="ai-body"><strong>{one_liner}</strong></div>
          <div class="ai-body" style="margin-top:8px;color:#8b949e;font-size:12px;">{reasoning}</div>
        </div>
        """, unsafe_allow_html=True)

        if factors:
            st.markdown("**Factor Breakdown:**")
            for factor, status in factors.items():
                pill = "pill-pos" if status == "Positive" else "pill-neg" if status == "Negative" else "pill-neu"
                icon = "🟢" if status == "Positive" else "🔴" if status == "Negative" else "🟡"
                st.markdown(f"""
                <div class="factor-row">
                  <div class="factor-name">{icon} &nbsp;{factor}</div>
                  <span class="{pill}">{status}</span>
                </div>
                """, unsafe_allow_html=True)

# ── News with AI Summaries ─────────────────────────────────────────────────────
st.markdown(f'<div class="section-header">📰 Latest News for {selected}</div>', unsafe_allow_html=True)

if not news:
    st.info("No news found. This could be due to API limits or no recent coverage.")
else:
    for i, article in enumerate(news[:6]):
        title = article.get("title", "No title")
        body = article.get("summary", "")
        source = article.get("source", "Unknown")
        published = article.get("published_at", "")
        url = article.get("url", "#")
        raw_sentiment = article.get("sentiment")

        # Sentiment badge
        if raw_sentiment in ["Bullish", "Positive", "positive", "bullish"]:
            sent_html = '<span class="pill-pos">🟢 Bullish</span>'
        elif raw_sentiment in ["Bearish", "Negative", "negative", "bearish"]:
            sent_html = '<span class="pill-neg">🔴 Bearish</span>'
        elif raw_sentiment:
            sent_html = '<span class="pill-neu">🟡 Neutral</span>'
        else:
            sent_html = ""

        st.markdown(f"""
        <div class="news-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:6px;">
            <div class="news-title"><a href="{url}" target="_blank" style="color:#f0f6fc;text-decoration:none;">{title}</a></div>
            {sent_html}
          </div>
          <div class="news-meta">📌 {source} · {published}</div>
          {f'<div class="news-body">{body[:220]}...</div>' if body else ''}
        </div>
        """, unsafe_allow_html=True)

        # AI Summarize button
        if st.button(f"🤖 AI Explain This Article", key=f"news_ai_{i}_{selected}"):
            with st.spinner("Groq is reading the article..."):
                ai_sum = summarize_article(selected, title, body)

            verdict = ai_sum.get("verdict", "Neutral")
            impact = ai_sum.get("impact", "Neutral")
            one_liner = ai_sum.get("one_liner", "")
            why = ai_sum.get("why_investors_care", "")
            outlook = ai_sum.get("short_term_outlook", "")

            impact_color = "#3fb950" if impact == "Positive" else "#f85149" if impact == "Negative" else "#d29922"
            verdict_class = "pill-pos" if verdict == "Bullish" else "pill-neg" if verdict == "Bearish" else "pill-neu"

            st.markdown(f"""
            <div class="ai-insight">
              <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px;">
                <div class="ai-tag">🤖 Groq AI · Article Analysis</div>
                <span class="{verdict_class}">{verdict}</span>
                <span style="font-size:12px;color:{impact_color};font-weight:700;">Impact: {impact}</span>
              </div>
              <div class="ai-body"><strong>📌 {one_liner}</strong></div>
              <div class="ai-body" style="margin-top:8px;">💼 <em>Why investors care:</em> {why}</div>
              <div class="ai-body" style="margin-top:6px;">📈 <em>Short-term outlook:</em> {outlook}</div>
            </div>
            """, unsafe_allow_html=True)
