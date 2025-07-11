# Crypto 3-Bucket Dashboard

A smart Streamlit dashboard that provides crypto allocation signals for **BTC • ALTS • STABLES** with automated Telegram alerts and trade journaling.

## 🎯 Overview

This dashboard analyzes key crypto market signals and recommends optimal portfolio allocation across three buckets:
- **BTC** (Bitcoin allocation percentage)
- **ALTS** (Altcoin allocation percentage) 
- **STABLES** (Stablecoin allocation percentage)

**Key Features:**
- Real-time market data from free APIs
- Smart trigger system with 12-hour cooldowns
- Visual allocation gauge with color-coded recommendations
- Automated Telegram alerts for significant market shifts
- CSV trading journal with automatic logging
- Auto-refresh every 12 hours

## 🏗️ Architecture

```
crypto-dashboard/
├── dashboard.py        # Main Streamlit UI
├── metrics.py         # Data fetching from multiple sources
├── triggers.py        # Rule engine + alert system
├── journal.py         # CSV trading journal
├── telegram_utils.py  # Telegram messaging
├── requirements.txt   # Dependencies
└── .env.template      # API configuration template
```

## 📊 Data Sources

All data sources are **free** with generous rate limits:

| **Metric** | **Source** | **Auth Required** | **Rate Limit** |
|------------|------------|-------------------|----------------|
| BTC Dominance & Market Cap | CoinGecko `/global` | None | 30 req/min |
| Alt Season Index | BlockchainCenter CSV | None | Daily updates |
| Stablecoin Supply | DeFiLlama API | None | Unlimited |
| BTC Funding & OI | Binance Futures API | None | 500 req/5min |
| Alt Funding (HYPE) | Hyperliquid API | None | Unlimited |
| Macro Events | TradingEconomics/Finnhub | Free Key | 100-500 req/day |

## 🚨 Trigger Rules

The system monitors these conditions and sends alerts:

| **Condition** | **Action** | **Telegram Alert** |
|---------------|------------|-------------------|
| BTC Dom < 60% & Alt Index > 50 | Start BTC→ALT rotation | "BTC.D < 60% & alt momentum ↑" |
| Alt Index ≥ 75 | Increase ALT allocation to 50% | "Full alt-season (≥ 75)" |
| Alt Index ≤ 25 | Reduce ALT allocation to 15% | "Back to BTC dominance" |
| Funding Rate ≥ 0.10%/8h | Trim leveraged positions | "Crowded leverage: {symbol}" |
| Stablecoin Δ ≥ $1B/7d | Deploy stablecoin reserves | "New stablecoin issuance" |
| Major macro event ± 12h | Pause new risk taking | "Macro in play: {event}" |

## 📈 Allocation Logic

```python
if btc_dominance >= 61 and alt_index < 50:
    allocation = (70%, 25%, 5%)    # BTC dominant phase
elif btc_dominance < 60 and alt_index >= 50:
    allocation = (45%, 50%, 5%)    # Alt season phase
else:
    allocation = (60%, 35%, 5%)    # Neutral phase
```

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Optional: Configure API keys** (works with mock data if skipped)
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

3. **Run the dashboard:**
   ```bash
   streamlit run dashboard.py
   ```

4. **Access at:** `http://localhost:8501`

## 🔧 Configuration

### API Keys (Optional)
```bash
# Macro events (free signup required)
TRADINGECON_KEY=your_key_here
FINNHUB_KEY=your_key_here

# Telegram alerts (optional)
TG_TOKEN=your_bot_token
TG_CHAT=your_chat_id
```

### Telegram Bot Setup
1. Message `@BotFather` on Telegram
2. Create new bot with `/newbot`
3. Copy the bot token to `.env`
4. Get your chat ID by messaging the bot and visiting: `https://api.telegram.org/bot{TOKEN}/getUpdates`

## 📝 Trading Journal

The system automatically logs all allocation changes to `trading_journal.csv`:

```csv
date,asset,change_pct,reason,emotion
2025-07-11,BTC,-10,"BTC.D <60, rotate","😐"
2025-07-11,ALTS,+15,"Full alt-season","🚀"
```

## 🔄 Deployment Options

### Local Development
```bash
streamlit run dashboard.py
```

### Streamlit Cloud
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Deploy from `dashboard.py`

### Docker
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 📱 Features

- **Real-time Metrics**: Live BTC dominance, alt season index, funding rates
- **Visual Gauge**: Color-coded allocation recommendations
- **Smart Alerts**: 12-hour cooldowns prevent spam
- **Trade Journal**: Automatic logging of all decisions
- **Fallback Data**: Works offline with mock data
- **Mobile Friendly**: Responsive Streamlit interface

## 🛠️ Customization

- **Add new triggers**: Edit `triggers.py`
- **Change allocation logic**: Modify `calculate_allocation()` in `triggers.py`
- **Add data sources**: Extend `metrics.py`
- **Custom UI**: Update `dashboard.py`

## 📊 Dashboard Sections

1. **Key Metrics Cards**: BTC dominance, alt index, funding rates, stablecoin flows
2. **Allocation Gauge**: Visual recommendation with current percentages
3. **Active Triggers**: Real-time alert status
4. **Trading Journal**: Recent entries and statistics
5. **Macro Events**: Upcoming high-impact events
6. **Detailed Metrics**: Expandable technical data

Built for traders who want to spend **< 20 minutes twice a week** yet still outperform the market with systematic, data-driven decisions.