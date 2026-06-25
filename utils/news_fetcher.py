"""
news_fetcher.py — Pulls real-time news from Finnhub, Alpha Vantage, and Marketaux
Deduplicates articles and returns a unified list.
"""

import requests
import streamlit as st
from datetime import datetime, timedelta
import time

# ── Finnhub ────────────────────────────────────────────────────────────────────
def fetch_finnhub_news(company_name: str, days_back: int = 3) -> list[dict]:
    """Fetch company news from Finnhub using free-text search."""
    api_key = st.secrets.get("FINNHUB_API_KEY", "")
    if not api_key:
        return []

    # Finnhub uses stock symbols; for Indian stocks we use general news search
    today = datetime.now()
    from_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")

    # Use general news category and filter by keyword
    url = "https://finnhub.io/api/v1/company-news"
    # Try with company name as symbol approximation; fallback to general news
    params = {
        "token": api_key,
        "category": "general",
        "minId": 0,
    }

    # For Indian stocks, use Finnhub general news + filter
    general_url = "https://finnhub.io/api/v1/news"
    try:
        resp = requests.get(general_url, params=params, timeout=8)
        if resp.status_code != 200:
            return []
        articles = resp.json()
        # Filter by company name in headline/summary
        filtered = [
            a for a in articles
            if company_name.lower().split()[0] in (a.get("headline", "") + a.get("summary", "")).lower()
        ]
        return [
            {
                "title": a.get("headline", ""),
                "summary": a.get("summary", ""),
                "url": a.get("url", ""),
                "published_at": datetime.fromtimestamp(a.get("datetime", time.time())).strftime("%Y-%m-%d %H:%M"),
                "source": "Finnhub",
                "sentiment": None,
            }
            for a in filtered[:5]
        ]
    except Exception:
        return []


# ── Alpha Vantage ──────────────────────────────────────────────────────────────
def fetch_alphavantage_news(company_name: str) -> list[dict]:
    """Fetch news + sentiment from Alpha Vantage News Sentiment API."""
    api_key = st.secrets.get("ALPHA_VANTAGE_API_KEY", "")
    if not api_key:
        return []

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "topics": "financial_markets",
        "apikey": api_key,
        "limit": 50,
        "sort": "LATEST",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        articles = data.get("feed", [])

        # Filter by company name keyword
        keyword = company_name.lower().split()[0]
        filtered = [
            a for a in articles
            if keyword in (a.get("title", "") + a.get("summary", "")).lower()
        ]

        results = []
        for a in filtered[:5]:
            # Extract overall sentiment
            sentiment_label = a.get("overall_sentiment_label", "Neutral")
            sentiment_score = a.get("overall_sentiment_score", 0)
            results.append({
                "title": a.get("title", ""),
                "summary": a.get("summary", ""),
                "url": a.get("url", ""),
                "published_at": a.get("time_published", "")[:16].replace("T", " "),
                "source": "Alpha Vantage",
                "sentiment": sentiment_label,
                "sentiment_score": float(sentiment_score),
            })
        return results
    except Exception:
        return []


# ── Marketaux ──────────────────────────────────────────────────────────────────
def fetch_marketaux_news(company_name: str) -> list[dict]:
    """Fetch news from Marketaux with entity-level sentiment."""
    api_key = st.secrets.get("MARKETAUX_API_KEY", "")
    if not api_key:
        return []

    url = "https://api.marketaux.com/v1/news/all"
    params = {
        "api_token": api_key,
        "search": company_name,
        "language": "en",
        "limit": 5,
        "sort": "published_desc",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        articles = data.get("data", [])

        results = []
        for a in articles:
            # Extract entity sentiment for the company
            entities = a.get("entities", [])
            sentiment = None
            for entity in entities:
                if company_name.lower().split()[0] in entity.get("name", "").lower():
                    sentiment = entity.get("sentiment_score", None)
                    break

            results.append({
                "title": a.get("title", ""),
                "summary": a.get("description", ""),
                "url": a.get("url", ""),
                "published_at": a.get("published_at", "")[:16].replace("T", " "),
                "source": "Marketaux",
                "sentiment": "Bullish" if (sentiment and sentiment > 0.1) else
                             "Bearish" if (sentiment and sentiment < -0.1) else "Neutral",
                "sentiment_score": sentiment,
            })
        return results
    except Exception:
        return []


# ── Market-wide news ───────────────────────────────────────────────────────────
def fetch_market_news() -> list[dict]:
    """Fetch broad Indian market news from Marketaux."""
    api_key = st.secrets.get("MARKETAUX_API_KEY", "")
    if not api_key:
        return []

    url = "https://api.marketaux.com/v1/news/all"
    params = {
        "api_token": api_key,
        "search": "Nifty OR Sensex OR RBI OR India stock market",
        "language": "en",
        "limit": 10,
        "sort": "published_desc",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return []
        articles = resp.json().get("data", [])
        return [
            {
                "title": a.get("title", ""),
                "summary": a.get("description", ""),
                "url": a.get("url", ""),
                "published_at": a.get("published_at", "")[:16].replace("T", " "),
                "source": "Marketaux",
                "sentiment": None,
            }
            for a in articles
        ]
    except Exception:
        return []


# ── Combined fetcher ───────────────────────────────────────────────────────────
def fetch_all_news(company_name: str) -> list[dict]:
    """Aggregate news from all 3 sources, deduplicate by title."""
    all_articles = []
    all_articles += fetch_marketaux_news(company_name)
    all_articles += fetch_alphavantage_news(company_name)
    all_articles += fetch_finnhub_news(company_name)

    # Deduplicate by title similarity (first 40 chars)
    seen = set()
    unique = []
    for a in all_articles:
        key = a.get("title", "")[:40].lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(a)

    return unique[:10]  # Max 10 articles per company
