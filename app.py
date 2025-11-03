import os, yaml, pandas as pd, streamlit as st
from typing import Dict, List, Any
from fetch import recent_articles_for_market
from llm import analyse_article
from ui import article_card
import datetime as dt
from dateutil import parser

st.set_page_config(page_title="Regulatory News (LLM)", layout="wide")

st.title("NBIM Regulatory News — LLM Dashboard")

with open("config/markets.yaml", "r", encoding="utf-8") as f:
    markets_cfg = yaml.safe_load(f)
with open("config/sources.yaml", "r", encoding="utf-8") as f:
    sources_cfg = yaml.safe_load(f)

# Sidebar controls -> markets, items per market, llm option, llm model
all_markets: List[str] = markets_cfg.get("markets", [])
selected = st.sidebar.multiselect("Select markets", options=all_markets, default=all_markets)
max_items = st.sidebar.slider("Max items per market", min_value=5, max_value=60, value=20, step=5)
run_llm = st.sidebar.checkbox("Run LLM classification/summaries", value=True)
model = st.sidebar.selectbox("LLM model", ["gpt-4.1-mini", "gpt-4o-mini", "o4-mini"], index=0)

# Date range filter
st.sidebar.markdown("### Date Range Filter")
apply_date_filter = st.sidebar.checkbox("Filter by date range", value=False)

default_start = dt.date.today() - dt.timedelta(days=730)  # last 2 years
default_end = dt.date.today()

if apply_date_filter:
    start_date, end_date = st.sidebar.date_input(
        "Select publication date range:",
        [default_start, default_end]
    )
else:
    start_date, end_date = None, None

# Safety check
if start_date and end_date and start_date > end_date:
    st.sidebar.error("Start date must be before end date.")
st.sidebar.caption("Note: RSS feeds typically include recent articles only.")

# Main button
if st.button("Fetch & Analyse"):
    rows = []
    st.caption(f"Showing news from {start_date} to {end_date}")

    for m in selected:
        st.subheader(m)

        queries = sources_cfg["google_news_queries"].get(m, [])
        direct = sources_cfg["direct_rss"].get(m, [])
        articles = recent_articles_for_market(m, queries, direct)[:max_items]

        # Filtering -> publication date
        filtered_articles = []
        for a in articles:
            pub_date = None
            if a.get("published_parsed"):
                t = a["published_parsed"]
                pub_date = dt.date(t.tm_year, t.tm_mon, t.tm_mday)
            elif a.get("published"):
                try:
                    pub_date = parser.parse(a["published"]).date()
                except Exception:
                    pub_date = None

            if not start_date or not end_date or (start_date <= pub_date <= end_date):
                filtered_articles.append(a)

        articles = filtered_articles

        # Article displaying
        for a in articles:
            llm_data = analyse_article(a, m, model=model) if run_llm else None
            article_card(a, llm_data)
            rows.append({
                "market": m,
                "title": a.get("title", ""),
                "source": a.get("source", ""),
                "published": a.get("published", ""),
                "url": a.get("link", ""),
                "is_regulatory": llm_data.get("is_regulatory") if llm_data else None,
                "jurisdiction": llm_data.get("jurisdiction") if llm_data else None,
                "authority": llm_data.get("authority") if llm_data else None,
                "topic": llm_data.get("topic") if llm_data else None,
                "summary": llm_data.get("summary") if llm_data else None,
                "implications": llm_data.get("implications") if llm_data else None,
                "risk_tags": ", ".join(llm_data.get("risk_tags", []))
                    if llm_data and isinstance(llm_data.get("risk_tags"), list)
                    else None,
            })

    # Table Finaal
    if rows:
        st.divider()
        st.write("### Table view / CSV export")
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        st.download_button(
            "Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="regulatory_news.csv",
            mime="text/csv"
        )
else:
    st.write("Select markets and click **Fetch & Analyse** to begin.")
