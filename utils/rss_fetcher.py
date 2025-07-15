import feedparser

def fetch_rss_entries(url, source_name):
    """Fetch entries from RSS feed URL"""
    feed = feedparser.parse(url)
    entries = []

    for entry in feed.entries:
        entries.append({
            "title": entry.get("title", ""),
            "description": entry.get("summary", ""),
            "link": entry.get("link", ""),
            "published_date": entry.get("published", ""),
            "source": source_name,
            "selected": False,
            "analyzed": False
        })

    return entries
