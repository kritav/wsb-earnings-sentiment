# WSB Earnings Sentiment Bot

A simple bot that analyzes sentiment from Wall Street Bets earnings threads to generate bullish vs bearish graphs.

## Features

- Automatically finds the latest Weekly Earnings Thread on r/wallstreetbets
- Extracts stock tickers from comments
- Analyzes sentiment using keyword detection and TextBlob
- Generates visualizations showing:
  - Top mentioned tickers
  - Bullish vs Bearish sentiment by ticker

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Reddit API credentials:**
   - Go to https://www.reddit.com/prefs/apps
   - Click "Create App" or "Create Another App"
   - Choose "script" as the app type
   - Note down your `client_id` and `client_secret`

3. **Configure the bot:**
   - Open `main.py`
   - Replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with your actual credentials

4. **Run the bot:**
   ```bash
   python main.py
   ```

## How it works

1. Searches for the latest "Weekly Earnings Thread" in r/wallstreetbets
2. If not found automatically, prompts for manual thread URL/ID
3. Fetches and analyzes comments for:
   - Stock tickers (2-5 uppercase letters, filtered for common words)
   - Bullish sentiment (calls, moon, rocket, etc.)
   - Bearish sentiment (puts, dump, crash, etc.)
4. Generates two charts:
   - Bar chart of most mentioned tickers
   - Stacked bar chart showing bullish vs bearish sentiment

## Requirements

- Python 3.7+
- Reddit API credentials (free)
- Internet connection
