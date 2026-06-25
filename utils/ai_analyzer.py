"""
ai_analyzer.py — All Groq API calls for summarization, scoring, and analysis.
Uses llama-3.3-70b-versatile (fast + capable on Groq's free tier).
"""

import streamlit as st
from groq import Groq
import json

def get_groq_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])


def summarize_article(company_name: str, article_title: str, article_body: str) -> dict:
    """
    Returns structured AI analysis of a single news article.
    Output: one-liner, verdict, impact, why_investors_care
    """
    client = get_groq_client()

    prompt = f"""You are a financial analyst explaining news to a beginner Indian investor.

Company: {company_name}
Article Title: {article_title}
Article Content: {article_body[:1500]}

Respond ONLY with a valid JSON object (no markdown, no extra text):
{{
  "one_liner": "One sentence summary a beginner can understand",
  "verdict": "Bullish" or "Bearish" or "Neutral",
  "impact": "Positive" or "Negative" or "Neutral",
  "why_investors_care": "One sentence on why this matters for investors",
  "short_term_outlook": "One sentence on expected short-term stock impact"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        return {
            "one_liner": "Could not analyze this article.",
            "verdict": "Neutral",
            "impact": "Neutral",
            "why_investors_care": "N/A",
            "short_term_outlook": "N/A",
        }


def get_company_ai_score(company_name: str, stock_data: dict, news_list: list) -> dict:
    """
    Returns a 0–100 AI Confidence Score + factor table for a company.
    """
    client = get_groq_client()

    # Build news headlines string
    headlines = "\n".join([f"- {n.get('title', '')}" for n in news_list[:5]]) or "No recent news found."

    price = stock_data.get("price", "N/A")
    change_pct = stock_data.get("change_pct", 0)
    pe = stock_data.get("pe_ratio", "N/A")
    promoter = round((stock_data.get("promoter_holding") or 0) * 100, 1)
    institutional = round((stock_data.get("institutional_holding") or 0) * 100, 1)
    beta = stock_data.get("beta", "N/A")
    week52_high = stock_data.get("52w_high", "N/A")
    week52_low = stock_data.get("52w_low", "N/A")

    prompt = f"""You are a stock analyst evaluating {company_name} for a beginner Indian investor.

Stock Data:
- Current Price: ₹{price}
- Today's Change: {change_pct}%
- P/E Ratio: {pe}
- Promoter Holding: {promoter}%
- Institutional Holding: {institutional}%
- Beta: {beta}
- 52W High: ₹{week52_high} | 52W Low: ₹{week52_low}

Recent News Headlines:
{headlines}

Respond ONLY with a valid JSON object (no markdown, no extra text):
{{
  "confidence_score": <integer 0-100>,
  "factors": {{
    "Latest News": "Positive" or "Negative" or "Neutral",
    "Promoter Holding": "Positive" or "Negative" or "Neutral",
    "Institutional Activity": "Positive" or "Negative" or "Neutral",
    "Valuation (PE)": "Positive" or "Negative" or "Neutral",
    "Price Momentum": "Positive" or "Negative" or "Neutral",
    "Volatility (Beta)": "Positive" or "Negative" or "Neutral"
  }},
  "one_liner": "One-sentence overall take on this stock for a beginner",
  "verdict": "Bullish" or "Bearish" or "Neutral",
  "reasoning": "Two sentences explaining the confidence score"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception:
        return {
            "confidence_score": 50,
            "factors": {},
            "one_liner": "Analysis unavailable.",
            "verdict": "Neutral",
            "reasoning": "Could not generate analysis.",
        }


def explain_stock_move(company_name: str, change_pct: float, news_list: list, stock_data: dict) -> dict:
    """
    'Why did this stock move today?' feature.
    """
    client = get_groq_client()
    headlines = "\n".join([f"- {n.get('title', '')}" for n in news_list[:5]]) or "No specific news found."
    volume = stock_data.get("volume", "N/A")
    avg_vol = stock_data.get("avg_volume", "N/A")

    prompt = f"""Explain to a beginner investor why {company_name} moved {change_pct:+.2f}% today.

Volume today: {volume} | Average volume: {avg_vol}
Recent News:
{headlines}

Respond ONLY with valid JSON (no markdown):
{{
  "reasons": ["reason 1", "reason 2", "reason 3"],
  "ai_verdict": "One sentence short-term verdict",
  "momentum": "Bullish" or "Bearish" or "Neutral",
  "volume_signal": "High buying" or "High selling" or "Normal" or "Unknown"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception:
        return {
            "reasons": ["Data not available for analysis."],
            "ai_verdict": "Could not generate verdict.",
            "momentum": "Neutral",
            "volume_signal": "Unknown",
        }


def summarize_market_overview(market_news: list, indices: dict, macro: dict) -> str:
    """
    Generates a plain-English market overview paragraph.
    """
    client = get_groq_client()

    headlines = "\n".join([f"- {n.get('title', '')}" for n in market_news[:8]])
    nifty = indices.get("Nifty 50", {})
    sensex = indices.get("Sensex", {})
    crude = macro.get("Crude Oil (USD)", {})
    usdinr = macro.get("USD/INR", {})

    prompt = f"""You are a market analyst. Summarize today's Indian stock market in 3–4 plain English sentences for a beginner investor. Be specific about what moved and why.

Market Data:
- Nifty 50: {nifty.get('price', 'N/A')} ({nifty.get('change_pct', 0):+.2f}%)
- Sensex: {sensex.get('price', 'N/A')} ({sensex.get('change_pct', 0):+.2f}%)
- Crude Oil: ${crude.get('price', 'N/A')} ({crude.get('change_pct', 0):+.2f}%)
- USD/INR: {usdinr.get('price', 'N/A')}

Today's Market News Headlines:
{headlines}

Write a direct, beginner-friendly summary. No bullet points. Plain paragraph only."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Could not generate market summary. Please check your Groq API key."
