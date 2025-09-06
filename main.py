import re
from collections import Counter
import matplotlib.pyplot as plt
from textblob import TextBlob
import praw
import time

# Reddit config
reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET", 
    user_agent="wsb-earnings-sentiment-bot/1.0"
)

# get Weekly Earnings Thread
def fetch_weekly_thread(subreddit="wallstreetbets"):
    try:
        # try to get the latest "Weekly Earnings Thread"
        print(f"Searching for weekly earnings thread in r/{subreddit}...")
        for submission in reddit.subreddit(subreddit).new(limit=50):
            title_lower = submission.title.lower()
            if any(keyword in title_lower for keyword in ["weekly earnings", "earnings thread", "earnings discussion"]):
                print(f"Found thread: {submission.title}")
                return submission, submission.title

        # manual input
        print("No weekly earnings thread found automatically.")
        thread_input = input("Enter the thread URL or ID manually: ").strip()
        if not thread_input:
            raise ValueError("No thread provided")
            
        if "http" in thread_input:
            submission = reddit.submission(url=thread_input)
        else:
            submission = reddit.submission(id=thread_input)
            
        title = input("Enter a title/description for this thread: ").strip()
        if not title:
            title = submission.title
        return submission, title
        
    except Exception as e:
        print(f"Error fetching thread: {e}")
        raise

# Fetch Comments
def fetch_comments(submission, limit=500):
    try:
        print(f"Fetching comments from thread: {submission.title}")
        print("This may take a moment for threads with many comments...")
        
        # replace "MoreComments" objects with actual comments
        submission.comments.replace_more(limit=0)  # 0 = get all
        
        # get all comments
        all_comments = submission.comments.list()
        print(f"Found {len(all_comments)} total comments")
        
        # remove deleted/removed comments and limit
        comments = []
        for comment in all_comments[:limit]:
            if hasattr(comment, 'body') and comment.body not in ['[deleted]', '[removed]']:
                comments.append(comment.body)
        
        print(f"Processing {len(comments)} valid comments")
        if not comments:
            print("Warning: No valid comments found. Check the thread URL/ID.")
        return comments
        
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return []

# ----------------- Analyze Comments -----------------
def analyze_comments(comments):
    # Common words to exclude from ticker detection
    exclude_words = {
        'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BUT', 'HAS', 'HIS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WHO', 'BOY', 'DID', 'GET', 'HIM', 'HIS', 'ITS', 'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE', 'YET', 'YOLO', 'WSB', 'DD', 'TLDR', 'IMO', 'FOMO', 'HODL', 'DIAMOND', 'HANDS', 'TENDIES', 'STONKS', 'GAINS', 'LOSSES', 'MOON', 'ROCKET', 'PUMP', 'DUMP', 'BAG', 'HOLDER', 'APES', 'SQUEEZE', 'GAMMA', 'DELTA', 'THETA', 'VEGA', 'IV', 'OTM', 'ITM', 'ATM', 'SPY', 'QQQ', 'IWM', 'VIX', 'SPX', 'NDX', 'RUT', 'DIA', 'XLF', 'XLK', 'XLE', 'XLI', 'XLY', 'XLP', 'XLU', 'XLV', 'XLB', 'XLRE', 'XLK', 'XLC', 'XLF', 'XLI', 'XLY', 'XLP', 'XLU', 'XLV', 'XLB', 'XLRE'
    }
    
    tickers = []
    bullish, bearish = Counter(), Counter()
    
    print("Analyzing comments for tickers and sentiment...")

    for i, comment in enumerate(comments):
        if i % 100 == 0:
            print(f"Processed {i}/{len(comments)} comments...")
            
        # Find potential tickers (2-5 uppercase letters)
        found = re.findall(r'\b[A-Z]{2,5}\b', comment)
        
        # Filter out common words and get sentiment
        valid_tickers = [t for t in found if t not in exclude_words]
        sentiment = TextBlob(comment).sentiment.polarity
        comment_lower = comment.lower()
        
        # Enhanced bullish/bearish detection
        bullish_keywords = ['call', 'calls', 'bull', 'bullish', 'moon', 'rocket', 'pump', 'buy', 'long', 'yolo', 'diamond hands', 'tendies', 'gains', 'profit', 'green', 'up', 'rise', 'squeeze', 'gamma squeeze']
        bearish_keywords = ['put', 'puts', 'bear', 'bearish', 'dump', 'sell', 'short', 'crash', 'down', 'fall', 'loss', 'red', 'bag', 'bagholder', 'rekt', 'paper hands']
        
        is_bullish = any(keyword in comment_lower for keyword in bullish_keywords) or sentiment > 0.1
        is_bearish = any(keyword in comment_lower for keyword in bearish_keywords) or sentiment < -0.1
        
        for ticker in valid_tickers:
            tickers.append(ticker)
            if is_bullish:
                bullish[ticker] += 1
            if is_bearish:
                bearish[ticker] += 1

    print(f"Analysis complete. Found {len(set(tickers))} unique tickers.")
    return Counter(tickers), bullish, bearish

# Plot Results
def plot_results(title, tickers, bullish, bearish):
    try:
        if not tickers:
            print("No tickers found to plot.")
            return
            
        print("\nTop Tickers:", tickers.most_common(10))

        # Bar chart of overall mentions
        top_tickers = tickers.most_common(10)
        if top_tickers:
            labels, counts = zip(*top_tickers)
            plt.figure(figsize=(12, 6))
            plt.bar(labels, counts, color="orange", alpha=0.7)
            plt.title(f"Top Mentioned Tickers - {title[:50]}...")
            plt.xlabel("Ticker")
            plt.ylabel("Total Mentions")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()

        # Bullish vs Bearish
        all_tickers = list(set(bullish.keys()) | set(bearish.keys()))
        if all_tickers:
            # Only show tickers with at least 2 mentions total
            filtered_tickers = [t for t in all_tickers if (bullish[t] + bearish[t]) >= 2]
            if filtered_tickers:
                bull_counts = [bullish[t] for t in filtered_tickers]
                bear_counts = [bearish[t] for t in filtered_tickers]

                plt.figure(figsize=(14, 6))
                x_pos = range(len(filtered_tickers))
                
                plt.bar(x_pos, bull_counts, label="Bullish/Calls", color="green", alpha=0.7)
                plt.bar(x_pos, bear_counts, bottom=bull_counts, label="Bearish/Puts", color="red", alpha=0.7)
                
                plt.title("Bullish vs Bearish Sentiment by Ticker")
                plt.xlabel("Ticker")
                plt.ylabel("Mentions")
                plt.xticks(x_pos, filtered_tickers, rotation=45)
                plt.legend()
                plt.tight_layout()
                plt.show()
                
                # Print summary
                print(f"\nSentiment Summary:")
                for ticker in filtered_tickers[:10]:  # top 10
                    bull_count = bullish[ticker]
                    bear_count = bearish[ticker]
                    total = bull_count + bear_count
                    sentiment = "Bullish" if bull_count > bear_count else "Bearish" if bear_count > bull_count else "Neutral"
                    print(f"{ticker}: {sentiment} ({bull_count}B/{bear_count}R, Total: {total})")
            else:
                print("No tickers with sufficient sentiment data to plot.")
        else:
            print("No sentiment data found.")
            
    except Exception as e:
        print(f"Error creating plots: {e}")
        print("Data summary:")
        print(f"Total tickers found: {len(tickers)}")
        print(f"Bullish mentions: {sum(bullish.values())}")
        print(f"Bearish mentions: {sum(bearish.values())}")

# Main
if __name__ == "__main__":
    try:
        print("=== WSB Earnings Sentiment Bot ===")
        print("Fetching Weekly Earnings Thread...")
        submission, thread_title = fetch_weekly_thread()
        print(f"Found thread: {thread_title}")

        print("\nFetching comments...")
        comments = fetch_comments(submission, limit=500)
        print(f"Fetched {len(comments)} comments")

        if not comments:
            print("No comments to analyze. Exiting.")
            exit(1)

        print("\nAnalyzing sentiment...")
        tickers, bullish, bearish = analyze_comments(comments)

        print("\nGenerating visualizations...")
        plot_results(thread_title, tickers, bullish, bearish)
        
        print("\n=== Analysis Complete ===")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure you have:")
        print("1. Valid Reddit API credentials in the script")
        print("2. All required packages installed (praw, textblob, matplotlib)")
        print("3. A valid internet connection")
