import os, json
from typing import Dict, Any
from utils import _key, cache_get, cache_set, clean_text

CLASSIFIER_VERSION = "2025-11-04-reg-v2"

SYSTEM = """You are a classifier and extractor for regulatory or policy-related financial news.
Return ONLY a compact JSON object with fields:
- is_regulatory: boolean
- jurisdiction: short string (e.g., "US", "UK", "EU", "NO", "JP")
- authority: string (e.g., "SEC", "FCA", "ESMA", "Finanstilsynet", "JFSA", etc.)
- topic: short string (e.g., "market conduct", "prudential", "crypto/MiCA", etc.)
- summary: 2–3 sentence summary, plain English
- implications: brief list-style string of potential impacts for a large global investor
- risk_tags: list of up to 4 tags (e.g., ["policy shift", "enforcement", "rulemaking"])

Classify an article as regulatory **if it discusses, explains, or analyses any policy, rule, regulatory agenda, or supervisory action**, even if written by law firms or consultancies.
"""

USER_TMPL = """Article:
Title: {title}
Source: {source}
Published: {published}
URL: {url}
Text: {text}

Market context: {market}
Return JSON only.
"""

def _openai_client():
    from openai import OpenAI
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def analyse_article(article: Dict[str, Any], market: str, model: str = "gpt-4.1-mini") -> Dict[str, Any]:
    title = clean_text(article.get("title", ""))
    text = clean_text(article.get("summary", ""))
    payload = USER_TMPL.format(
        title=title,
        source=article.get("source", ""),
        published=article.get("published", ""),
        url=article.get("link", ""),
        text=text,
        market=market,
    )
    force_refresh = os.environ.get("LLM_FORCE_REFRESH") == "1"
    ckey = _key("|".join([CLASSIFIER_VERSION, model, SYSTEM, payload]))
    cached = cache_get(ckey)
    if cached and not force_refresh:
        return cached

    client = _openai_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": payload},
        ],
        temperature=0.2,
        max_tokens=350,
    )
    content = resp.choices[0].message.content.strip()

    try:
        if content.startswith("```"):
            content = content.strip("` \n")
            if content.lower().startswith("json"):
                content = content[4:].strip()
        data = json.loads(content)
    except Exception:
        data = {"is_regulatory": False, "summary": "LLM output parsing failed.", "raw": content}

    cache_set(ckey, data)
    return data