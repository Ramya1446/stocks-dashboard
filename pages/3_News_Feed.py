"""
pages/3_News_Feed.py — Aggregated news feed for all watchlist companies
with per-article AI summaries from Groq
"""

import streamlit as st
from utils.stock_data import WATCHLIST
from utils.news_fetcher import fetch_all_news, fetch_market_news
from utils.ai_analyzer import summarize_article

st.set_page_config(page_title="News Feed — StockSense", page_icon="📰", layout="wide")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .main { background: #0d1117; }
  div[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #21262d; }

  .page-title { font-size: 28px; font-weight: 800; color: #f0f6fc; }
  .page-sub { font-size: 14px; color: #8b949e; margin-top: -6px; margin-bottom: 20px; }
  .section-header { font-size: 16px; font-weight: 700; color: #f0f6fc; margin: 28px 0 14px; padding-bottom: 8px; border-bottom: 1px solid #21262d; }

  .news-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 14px;
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
  }
  .news-card:hover { border-color: #58a6ff; transform: translateY(-1px); }
  .news-card::before { content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: #58a6ff; }

  .news-bull::before { background: #3fb950; }
  .news-bear::before { background: #f85149; }
  .news-neu::before { background: #d29922; }

  .news-company { font-size: 11px; color: #58a6ff; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
  .news-title { font-size: 15px; font-weight: 600; color: #f0f6fc; line-height: 1.5; }
  .news-meta { font-size: 11px; color: #8b949e; margin-top: 6px; display: flex; gap: 12px; align-items: center; }
  .news-body { font-size: 13px; color: #8b949e; margin-top: 10px; line-height: 1.6; }

  .pill { display: inline-block; border-radius: 20px; padding: 3px 12px; font-size: 11px; font-weight: 700; }
  .pill-pos { background: rgba(63,185,80,0.15); color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }
  .pill-neg { background: rgba(248,81,73,0.15); color: #f85149; border: 1px solid rgba(248,81,73,0.3); }
  .pill-neu { background: rgba(210,153,34,0.15); color: #d29922; border: 1px solid rgba(210,153,34,0.3); }
  .pill-src { background: rgba(88,166,255,0.1); color: #58a6ff; border: 1px solid rgba(88,166,255,0.2); }

  .ai-result { background: linear-gradient(135deg, #1c2233 0%, #161b22 100%); border: 1px solid #30363d; border-left: 3px solid #58a6ff; border-radius: 10px; padding: 14px 18px; margin: 12px 0; }
  .ai-tag { font-size: 10px; color: #58a6ff; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
  .ai-body { font-size: 13px; color: #c9d1d9; margin-top: 8px; line-height: 1.6; }

  .filter-bar { background: #161b22; border: 1px solid #21262d; border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; }

  .empty-state { text-align: center; padding: 60px 20px; color: #8b949e; }
  .empty-icon { font-size: 48px; margin-bottom: 12px; }

  .stButton>button { background: #21262d; color: #f0f6fc; border: 1px solid #30363d; border-radius: 8px; font-weight: 500; }
  .stButton>button:hover { background: #30363d; border-color: #58a6ff; }
  .stMultiSelect label, .stSelectbox label { color: #8b949e !important; }
  .stTabs [data-baseweb="tab"] { color: #8b949e; }
  .stTabs [aria-selected="true"] { color: #58a6ff !important; border-bottom-color: #58a6ff !important; }
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

from datetime import datetime, timedelta, timezone as _tz

st.markdown('<div class="page-title">📰 News Feed</div>', unsafe_allow_html=True)
_week_ago_label = (datetime.now(_tz.utc) - timedelta(days=7)).strftime("%d %b")
_today_label = datetime.now(_tz.utc).strftime("%d %b %Y")
st.markdown(f'<div class="page-sub">📅 This week only · {_week_ago_label} → {_today_label} · Finnhub + Marketaux · Groq AI summaries on demand.</div>', unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📌 Company News", "🌐 Market News"])

# ── Company News Tab ───────────────────────────────────────────────────────────
with tab1:
    # Filters
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected_companies = st.multiselect(
            "Filter by company",
            list(WATCHLIST.keys()),
            default=list(WATCHLIST.keys())[:4],
            placeholder="Select companies..."
        )
    with col2:
        sentiment_filter = st.selectbox("Sentiment", ["All", "Bullish", "Bearish", "Neutral"])
    with col3:
        source_filter = st.selectbox("Source", ["All", "Marketaux", "Alpha Vantage", "Finnhub"])
    st.markdown('</div>', unsafe_allow_html=True)

    if not selected_companies:
        st.markdown("""
        <div class="empty-state">
          <div class="empty-icon">📭</div>
          <div>Select at least one company to see news.</div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    fetch_btn = st.button("🔄 Fetch Latest News", key="fetch_company")

    if fetch_btn or "company_news_cache" not in st.session_state:
        all_articles = []
        progress = st.progress(0, text="Fetching news...")
        for i, company in enumerate(selected_companies):
            progress.progress((i + 1) / len(selected_companies), text=f"Fetching news for {company}...")
            articles = fetch_all_news(company)
            for a in articles:
                a["company"] = company
            all_articles.extend(articles)
        progress.empty()
        st.session_state["company_news_cache"] = all_articles

    all_articles = st.session_state.get("company_news_cache", [])

    # Apply filters
    filtered = all_articles
    if sentiment_filter != "All":
        filtered = [a for a in filtered if a.get("sentiment", "") == sentiment_filter]
    if source_filter != "All":
        filtered = [a for a in filtered if a.get("source", "") == source_filter]

    # Sort newest first
    filtered.sort(key=lambda x: x.get("published_at", ""), reverse=True)

    st.markdown(f'<div class="section-header">📋 {len(filtered)} articles found</div>', unsafe_allow_html=True)

    if not filtered:
        st.markdown("""
        <div class="empty-state">
          <div class="empty-icon">🔍</div>
          <div>No articles match your filters. Try broadening your search.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for i, article in enumerate(filtered[:20]):
            company = article.get("company", "")
            title = article.get("title", "No title")
            body = article.get("summary", "")
            source = article.get("source", "Unknown")
            published = article.get("display_date") or article.get("published_at", "")[:16]
            url = article.get("url", "#")
            sentiment = article.get("sentiment", "")

            # Card accent color by sentiment
            card_class = "news-bull" if sentiment in ["Bullish", "Positive", "positive", "bullish"] else \
                         "news-bear" if sentiment in ["Bearish", "Negative", "negative", "bearish"] else \
                         "news-neu"

            sent_pill = ""
            if sentiment in ["Bullish", "Positive", "positive", "bullish"]:
                sent_pill = '<span class="pill pill-pos">🟢 Bullish</span>'
            elif sentiment in ["Bearish", "Negative", "negative", "bearish"]:
                sent_pill = '<span class="pill pill-neg">🔴 Bearish</span>'
            elif sentiment:
                sent_pill = '<span class="pill pill-neu">🟡 Neutral</span>'

            st.markdown(f"""
            <div class="news-card {card_class}">
              <div class="news-company">{company}</div>
              <div class="news-title">
                <a href="{url}" target="_blank" style="color:#f0f6fc;text-decoration:none;">{title}</a>
              </div>
              <div class="news-meta">
                <span class="pill pill-src">{source}</span>
                {sent_pill}
                <span>🕐 {published}</span>
              </div>
              {f'<div class="news-body">{body[:260]}...</div>' if body else ''}
            </div>
            """, unsafe_allow_html=True)

            # AI summary button
            cache_key = f"ai_news_{i}_{company}"
            if st.button(f"🤖 Explain to me (AI)", key=f"btn_news_{i}_{company}"):
                with st.spinner("Groq is analyzing..."):
                    result = summarize_article(company, title, body)
                st.session_state[cache_key] = result

            if cache_key in st.session_state:
                r = st.session_state[cache_key]
                verdict = r.get("verdict", "Neutral")
                impact = r.get("impact", "Neutral")
                one_liner = r.get("one_liner", "")
                why = r.get("why_investors_care", "")
                outlook = r.get("short_term_outlook", "")

                impact_color = "#3fb950" if impact == "Positive" else "#f85149" if impact == "Negative" else "#d29922"
                v_pill = "pill-pos" if verdict == "Bullish" else "pill-neg" if verdict == "Bearish" else "pill-neu"

                st.markdown(f"""
                <div class="ai-result">
                  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
                    <span class="ai-tag">🤖 Groq AI</span>
                    <span class="pill {v_pill}">{verdict}</span>
                    <span style="font-size:12px;color:{impact_color};font-weight:700;">Impact: {impact}</span>
                  </div>
                  <div class="ai-body"><strong>{one_liner}</strong></div>
                  <div class="ai-body" style="margin-top:8px;">💼 <em>Why investors care:</em> {why}</div>
                  <div class="ai-body" style="margin-top:6px;">📈 <em>Short-term:</em> {outlook}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<hr style='border:none;border-top:1px solid #21262d;margin:4px 0 4px;'>", unsafe_allow_html=True)


# ── Market News Tab ────────────────────────────────────────────────────────────
with tab2:
    if st.button("🔄 Fetch Market News", key="fetch_market"):
        if "market_news_cache" in st.session_state:
            del st.session_state["market_news_cache"]

    if "market_news_cache" not in st.session_state:
        with st.spinner("Fetching this week's market news..."):
            deduped = fetch_market_news()
        st.session_state["market_news_cache"] = deduped

    market_news = st.session_state.get("market_news_cache", [])

    st.markdown(f'<div class="section-header">🌐 {len(market_news)} Market Headlines This Week</div>', unsafe_allow_html=True)

    if not market_news:
        st.info("No market news fetched. Check your Marketaux API key.")
    else:
        for i, article in enumerate(market_news):
            title = article.get("title", "No title")
            body = article.get("summary", "")
            source = article.get("source", "Unknown")
            published = article.get("display_date") or article.get("published_at", "")[:16]
            url = article.get("url", "#")

            st.markdown(f"""
            <div class="news-card news-neu">
              <div class="news-company">🌐 MARKET WIDE</div>
              <div class="news-title">
                <a href="{url}" target="_blank" style="color:#f0f6fc;text-decoration:none;">{title}</a>
              </div>
              <div class="news-meta">
                <span class="pill pill-src">{source}</span>
                <span>🕐 {published}</span>
              </div>
              {f'<div class="news-body">{body[:260]}...</div>' if body else ''}
            </div>
            """, unsafe_allow_html=True)

            cache_key = f"market_ai_{i}"
            if st.button("🤖 Explain this", key=f"mkt_btn_{i}"):
                with st.spinner("Groq is summarizing..."):
                    result = summarize_article("Indian Market", title, body)
                st.session_state[cache_key] = result

            if cache_key in st.session_state:
                r = st.session_state[cache_key]
                verdict = r.get("verdict", "Neutral")
                one_liner = r.get("one_liner", "")
                why = r.get("why_investors_care", "")
                v_pill = "pill-pos" if verdict == "Bullish" else "pill-neg" if verdict == "Bearish" else "pill-neu"

                st.markdown(f"""
                <div class="ai-result">
                  <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px;">
                    <span class="ai-tag">🤖 Groq AI</span>
                    <span class="pill {v_pill}">{verdict}</span>
                  </div>
                  <div class="ai-body"><strong>{one_liner}</strong></div>
                  <div class="ai-body" style="margin-top:8px;">💼 {why}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<hr style='border:none;border-top:1px solid #21262d;margin:4px 0 4px;'>", unsafe_allow_html=True)
