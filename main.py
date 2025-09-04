import requests
import re
from collections import Counter
import matplotlib.pyplot as plt
from textblob import TextBlob


# get weekly earnings thread
def fetch_weekly_thread(subreddit="wallstreetbets"):
    url = "https://api.pushshift.io/reddit/submission/search/"
    params = {
        "subreddit": subreddit,
        "q": "Weekly Earnings Thread",
        "size": 1,
        "sort": "desc",
        "sort_type": "created_utc"
    }
    res = requests.get(url, params=params)
    data = res.json().get("data", [])
    if not data:
        raise ValueError("No weekly earnings thread found!")
    return data[0]["id"], data[0]["title"]


# get comments
def fetch_comments(thread_id, subreddit="wallstreetbets", limit=500):
    url = "https://api.pushshift.io/reddit/comment/search/"
    params = {
        "link_id": thread_id,
        "subreddit": subreddit,
        "size": limit
    }
    res = requests.get(url, params=params)
    data = res.json().get("data", [])
    return [c.get("body", "") for c in data]


# 3. find tickers and direction
def analyze_comments(comments):
    tickers = []
    bullish, bearish = Counter(), Counter()

    for c in comments:
        found = re.findall(r'\b[A-Z]{2,5}\b', c)
        sentiment = TextBlob(c).sentiment.polarity

        for t in found:
            tickers.append(t)
            cl = c.lower()
            if "call" in cl or sentiment > 0.2:
                bullish[t] += 1
            if "put" in cl or sentiment < -0.2:
                bearish[t] += 1

    return Counter(tickers), bullish, bearish


# visualize
def plot_results(title, tickers, bullish, bearish):
    print("\nTop Tickers:", tickers.most_common(10))

    # Bar chart of overall mentions
    labels, counts = zip(*tickers.most_common(10))
    plt.figure(figsize=(10, 4))
    plt.bar(labels, counts, color="orange")
    plt.title(f"Top Mentioned Tickers ({title})")
    plt.xlabel("Ticker")
    plt.ylabel("Mentions")
    plt.show()

    # Bullish vs Bearish
    all_tickers = list(set(bullish.keys()) | set(bearish.keys()))
    bull_counts = [bullish[t] for t in all_tickers]
    bear_counts = [bearish[t] for t in all_tickers]

    plt.figure(figsize=(12, 5))
    plt.bar(all_tickers, bull_counts, label="Calls/Bullish", color="green")
    plt.bar(all_tickers, bear_counts, bottom=bull_counts, label="Puts/Bearish", color="red")
    plt.title("Bullish vs Bearish Mentions")
    plt.xlabel("Ticker")
    plt.ylabel("Mentions")
    plt.legend()
    plt.show()


# main
if __name__ == "__main__":
    print("Fetching Weekly Earnings Thread...")
    thread_id, thread_title = fetch_weekly_thread()
    print("Found thread:", thread_title)

    print("Fetching comments...")
    comments = fetch_comments(thread_id, limit=500)
    print(f"Fetched {len(comments)} comments")

    print("Analyzing...")
    tickers, bullish, bearish = analyze_comments(comments)

    plot_results(thread_title, tickers, bullish, bearish)
