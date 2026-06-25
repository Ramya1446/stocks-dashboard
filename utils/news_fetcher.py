"""
news_fetcher.py — Pulls THIS WEEK's news only from Finnhub, Alpha Vantage, and Marketaux.
All fetchers enforce a hard date cutoff — articles older than 7 days are dropped
both at the API query level (via date params) AND after fetching (post-filter).
"""

import requests
import streamlit as st
from datetime import datetime, timedelta, timezone
import time

# ── Date helpers ───────────────────────────────────────────────────────────────
def _week_ago() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=7)

def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def _week_ago_str() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

def _parse_date(date_str: str) -> datetime | None:
    """Try multiple date formats and return UTC-aware datetime."""
    if not date_str:
        return None
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y%m%dT%H%M%S",  # Alpha Vantage format
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str[:19], fmt[:len(date_str[:19])])
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None

def _is_this_week(date_str: str) -> bool:
    """Return True only if article is within the last 7 days."""
    dt = _parse_date(date_str)
    if dt is None:
        return False
    return dt >= _week_ago()

def _format_display_date(date_str: str) -> str:
    """Format for display. Shows 'X hours ago' or 'Mon, 23 Jun' style."""
    dt = _parse_date(date_str)
    if dt is None:
        return date_str[:16] if date_str else "Unknown date"
    now = datetime.now(timezone.utc)
    diff = now - dt
    if diff.total_seconds() < 3600:
        mins = int(diff.total_seconds() / 60)
        return f"{mins}m ago"
    elif diff.total_seconds() < 86400:
        hrs = int(diff.total_seconds() / 3600)
        return f"{hrs}h ago"
    elif diff.days <= 7:
        return dt.strftime("%a, %d %b · %H:%M")
    else:
        return dt.strftime("%d %b %Y")


# ── Finnhub ────────────────────────────────────────────────────────────────────
def fetch_finnhub_news(company_name: str) -> list[dict]:
    """Fetch this week's general market news from Finnhub, filtered by company keyword."""
    api_key = st.secrets.get("FINNHUB_API_KEY", "")
    if not api_key:
        return []

    # Finnhub /news returns general news with a datetime unix timestamp
    # We filter by keyword + enforce date cutoff after fetching
    url = "https://finnhub.io/api/v1/news"
    params = {
        "token": api_key,
        "category": "general",
    }

    try:
        resp = requests.get(url, params=params, timeout=8)
        if resp.status_code != 200:
            return []

        articles = resp.json()
        if not isinstance(articles, list):
            return []

        keyword = company_name.lower().split()[0]
        cutoff_ts = _week_ago().timestamp()

        results = []
        for a in articles:
            ts = a.get("datetime", 0)
            # Hard timestamp cutoff — drop anything older than 7 days
            if ts < cutoff_ts:
                continue
            headline = a.get("headline", "")
            summary = a.get("summary", "")
            if keyword not in (headline + summary).lower():
                continue

            pub_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            results.append({
                "title": headline,
                "summary": summary,
                "url": a.get("url", ""),
                "published_at": pub_str,
                "display_date": _format_display_date(pub_str),
                "source": "Finnhub",
                "sentiment": None,
            })

        # Sort newest first
        results.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        return results[:5]

    except Exception:
        return []


# ── Alpha Vantage ──────────────────────────────────────────────────────────────
def fetch_alphavantage_news(company_name: str) -> list[dict]:
    """
    Fetch this week's news from Alpha Vantage.
    Uses time_from param to limit results to last 7 days.
    Only called when AV API quota available (25/day).
    """
    api_key = st.secrets.get("ALPHA_VANTAGE_API_KEY", "")
    if not api_key:
        return []

    # AV time_from format: YYYYMMDDTHHMM
    time_from = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y%m%dT%H%M")

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "topics": "financial_markets",
        "apikey": api_key,
        "limit": 50,
        "sort": "LATEST",
        "time_from": time_from,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()

        # AV returns rate limit info in a "Note" or "Information" key — skip if so
        if "Note" in data or "Information" in data:
            return []

        articles = data.get("feed", [])
        keyword = company_name.lower().split()[0]

        results = []
        for a in articles:
            title = a.get("title", "")
            summary = a.get("summary", "")
            if keyword not in (title + summary).lower():
                continue

            pub_raw = a.get("time_published", "")  # Format: 20250101T120000
            # Post-filter: enforce 7-day cutoff
            if not _is_this_week(pub_raw):
                continue

            sentiment_label = a.get("overall_sentiment_label", "Neutral")
            results.append({
                "title": title,
                "summary": summary,
                "url": a.get("url", ""),
                "published_at": pub_raw,
                "display_date": _format_display_date(pub_raw),
                "source": "Alpha Vantage",
                "sentiment": sentiment_label,
                "sentiment_score": float(a.get("overall_sentiment_score", 0)),
            })

        results.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        return results[:5]

    except Exception:
        return []


# ── Marketaux ──────────────────────────────────────────────────────────────────
def fetch_marketaux_news(company_name: str) -> list[dict]:
    """
    Fetch this week's news from Marketaux.
    Uses published_after param — this is the critical fix for old articles.
    """
    api_key = st.secrets.get("MARKETAUX_API_KEY", "")
    if not api_key:
        return []

    # Marketaux accepts published_after in YYYY-MM-DD format
    week_ago = _week_ago_str()

    url = "https://api.marketaux.com/v1/news/all"
    params = {
        "api_token": api_key,
        "search": company_name,
        "language": "en",
        "limit": 10,
        "sort": "published_desc",
        "published_after": week_ago,  # ← THIS was missing before
        "filter_entities": "true",    # Only return articles where entity is mentioned
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        articles = data.get("data", [])

        results = []
        for a in articles:
            pub_raw = a.get("published_at", "")

            # Double-check with post-fetch filter (belt + suspenders)
            if not _is_this_week(pub_raw):
                continue

            entities = a.get("entities", [])
            sentiment = None
            for entity in entities:
                name = entity.get("name", "").lower()
                sym = entity.get("symbol", "").lower()
                kw = company_name.lower().split()[0]
                if kw in name or kw in sym:
                    sentiment = entity.get("sentiment_score", None)
                    break

            # If no entity match, use first entity sentiment as fallback
            if sentiment is None and entities:
                sentiment = entities[0].get("sentiment_score", None)

            sent_label = (
                "Bullish" if (sentiment and sentiment > 0.1) else
                "Bearish" if (sentiment and sentiment < -0.1) else
                "Neutral"
            )

            results.append({
                "title": a.get("title", ""),
                "summary": a.get("description", "") or a.get("snippet", ""),
                "url": a.get("url", ""),
                "published_at": pub_raw,
                "display_date": _format_display_date(pub_raw),
                "source": "Marketaux",
                "sentiment": sent_label,
                "sentiment_score": sentiment,
            })

        return results[:5]

    except Exception:
        return []


# ── Market-wide news ───────────────────────────────────────────────────────────
def fetch_market_news() -> list[dict]:
    """Fetch this week's broad Indian market news from Marketaux + Finnhub, merged."""
    results = []

    # — Marketaux —
    api_key = st.secrets.get("MARKETAUX_API_KEY", "")
    if api_key:
        week_ago = _week_ago_str()
        url = "https://api.marketaux.com/v1/news/all"
        params = {
            "api_token": api_key,
            "search": "Nifty OR Sensex OR RBI OR BSE OR Indian stock market",
            "language": "en",
            "limit": 15,
            "sort": "published_desc",
            "published_after": week_ago,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                for a in resp.json().get("data", []):
                    pub_raw = a.get("published_at", "")
                    if not _is_this_week(pub_raw):
                        continue
                    results.append({
                        "title": a.get("title", ""),
                        "summary": a.get("description", "") or a.get("snippet", ""),
                        "url": a.get("url", ""),
                        "published_at": pub_raw,
                        "display_date": _format_display_date(pub_raw),
                        "source": "Marketaux",
                        "sentiment": None,
                    })
        except Exception:
            pass

    # — Finnhub —
    fh_key = st.secrets.get("FINNHUB_API_KEY", "")
    if fh_key:
        cutoff_ts = _week_ago().timestamp()
        try:
            resp = requests.get(
                "https://finnhub.io/api/v1/news",
                params={"token": fh_key, "category": "general"},
                timeout=8,
            )
            if resp.status_code == 200 and isinstance(resp.json(), list):
                for a in resp.json():
                    ts = a.get("datetime", 0)
                    if ts < cutoff_ts:
                        continue
                    pub_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    results.append({
                        "title": a.get("headline", ""),
                        "summary": a.get("summary", ""),
                        "url": a.get("url", ""),
                        "published_at": pub_str,
                        "display_date": _format_display_date(pub_str),
                        "source": "Finnhub",
                        "sentiment": None,
                    })
        except Exception:
            pass

    # Deduplicate + sort newest first
    seen = set()
    unique = []
    for a in results:
        key = a.get("title", "")[:50].lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(a)
    unique.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    return unique


# ── Combined fetcher ───────────────────────────────────────────────────────────
def fetch_all_news(company_name: str) -> list[dict]:
    """
    Aggregate THIS WEEK'S news from Marketaux + Finnhub.
    Alpha Vantage disabled by default to preserve its 25/day quota.
    All articles guaranteed to be ≤7 days old.
    """
    all_articles = []
    all_articles += fetch_marketaux_news(company_name)
    all_articles += fetch_finnhub_news(company_name)
    # Alpha Vantage skipped — uncomment below if you need it and have quota
    # all_articles += fetch_alphavantage_news(company_name)

    # Deduplicate by title (first 50 chars)
    seen = set()
    unique = []
    for a in all_articles:
        key = a.get("title", "")[:50].lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(a)

    # Final sort: newest first
    unique.sort(key=lambda x: x.get("published_at", ""), reverse=True)

    # Final hard cutoff — nothing older than 7 days passes
    unique = [a for a in unique if _is_this_week(a.get("published_at", ""))]

    return unique[:10]
