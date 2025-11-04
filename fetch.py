import time, feedparser, requests, urllib.parse, datetime as dt
from typing import List, Dict, Any, Tuple

def google_news_rss(query: str, lang="en", region="US") -> str:
    q = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl={lang}&gl={region}&ceid={region}:{lang}"

def fetch_feed(url: str, timeout: int = 15) -> List[Dict[str, Any]]:
    d = feedparser.parse(url)
    items = []
    for e in d.entries[:20]:  
        items.append({
            "title": getattr(e, "title", ""),
            "link": getattr(e, "link", ""),
            "summary": getattr(e, "summary", ""),
            "published": getattr(e, "published", ""),
            "source": getattr(d.feed, "title", url),
            "feed_url": url,
        })
    return items

def recent_articles_for_market(market: str,
                               queries: List[str],
                               direct_rss: List[str],
                               lang_region: Tuple[str,str]=("en","US")) -> List[Dict[str, Any]]:
    lang, region = lang_region
    articles = []
    # google news 
    for q in queries:
        url = google_news_rss(q + f" {market}", lang=lang, region=region)
        articles += fetch_feed(url)
        time.sleep(0.2)
    # regulator feeds
    for url in direct_rss:
        articles += fetch_feed(url)
        time.sleep(0.2)
    seen = set()
    deduped = []
    for a in articles:
        link = a.get("link","")
        if link and link not in seen:
            seen.add(link)
            deduped.append(a)
    return deduped
