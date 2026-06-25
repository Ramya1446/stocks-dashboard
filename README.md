# 📈 StockSense — Personal Indian Stock Market Dashboard

A real-time stock dashboard built with Streamlit, powered by Groq AI (LLaMA-3.3-70b).

## Features
- 🏠 **Market Overview** — Live Nifty, Sensex, Bank Nifty + macro indicators
- 👁️ **Watchlist** — Filtered stock list with fundamentals + AI confidence scores
- 🔍 **Stock Deep Dive** — Candlestick chart, factor dashboard, AI analysis
- 📰 **News Feed** — Aggregated from Finnhub + Alpha Vantage + Marketaux with AI summaries
- ❓ **Why Did It Move?** — One-click AI explanation for any stock's daily move

## Setup

### 1. Clone and install
```bash
git clone <your-repo>
cd stock-dashboard
pip install -r requirements.txt
```

### 2. Add your API keys
Edit `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your_key"
FINNHUB_API_KEY = "your_key"
ALPHA_VANTAGE_API_KEY = "your_key"
MARKETAUX_API_KEY = "your_key"
```
**Never commit this file.** It's in `.gitignore`.

### 3. Run locally
```bash
streamlit run app.py
```

### 4. Deploy to Streamlit Cloud
1. Push to GitHub (secrets.toml is gitignored)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo → set `app.py` as main file
4. Under **Settings → Secrets**, paste all 4 API keys
5. Deploy!

## Customizing Your Watchlist
Edit `utils/stock_data.py` → `WATCHLIST` dict:
```python
WATCHLIST = {
    "Tata Power": "TATAPOWER.NS",
    "IRFC": "IRFC.NS",
    # Add any NSE stock: "Display Name": "TICKER.NS"
}
```

## API Keys (all have free tiers)
| Service | Sign up | Used for |
|---|---|---|
| [Groq](https://console.groq.com) | Free | AI summaries & analysis |
| [Finnhub](https://finnhub.io) | Free | Company + market news |
| [Alpha Vantage](https://alphavantage.co) | Free | News + sentiment scores |
| [Marketaux](https://marketaux.com) | Free | Financial news + entity sentiment |

## Tech Stack
- **Streamlit** — UI framework
- **yfinance** — NSE stock data (free, no key needed)
- **Groq (LLaMA-3.3-70b)** — AI analysis
- **Plotly** — Interactive charts
- **Finnhub + Alpha Vantage + Marketaux** — News aggregation
