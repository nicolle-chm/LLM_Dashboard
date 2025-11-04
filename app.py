import os, yaml, pandas as pd, streamlit as st
from typing import Dict, List, Any
from fetch import recent_articles_for_market
from llm import analyse_article
from ui import article_card
import datetime as dt
from dateutil import parser
import re

st.set_page_config(page_title="Regulatory News (LLM)", layout="wide")

st.title("NBIM Regulatory News — LLM Dashboard")

if "df" not in st.session_state:
    st.session_state["df"] = None

# Loading config
with open("config/markets.yaml", "r", encoding="utf-8") as f:
    markets_cfg = yaml.safe_load(f)
with open("config/sources.yaml", "r", encoding="utf-8") as f:
    sources_cfg = yaml.safe_load(f)

# Sidebar controls
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

st.sidebar.caption("Note: RSS feeds usually include only recent updates (past few weeks or months)")

# Keyword filter 
st.sidebar.markdown("### Keyword Filter")
keyword_raw = st.sidebar.text_input(
    "Fetch only articles related to (comma-separated):",
    placeholder="e.g., crypto, MiCA, ESG, Finanstilsynet"
)
st.sidebar.caption("Tip: Increasing 'Max items per market' may improve keyword match results.")

# Typos/Synonyms -> keyword 
keyword_list = [k.strip().lower() for k in re.split(r'[;,]', keyword_raw) if k.strip()]
expanded_keywords = set()
synonyms = {
    "crypto": ["crypto", "cryptocurrency", "digital asset", "virtual asset", "mica"],
    "esg": ["esg", "sustainability", "sustainable finance", "csrd", "taxonomy", "sfdr"],
    "crpto": ["crypto"]  
}
for k in keyword_list:
    if k in synonyms:
        expanded_keywords.update(synonyms[k])
    else:
        expanded_keywords.add(k)

if start_date and end_date and start_date > end_date:
    st.sidebar.error("Start date must be before end date.")

# Main button
if st.button("Fetch & Analyse"):
    with st.spinner("Fetching and analysing news... Please wait."):
        rows = []
        if start_date and end_date:
            st.caption(f"Showing news from {start_date} to {end_date}")

        for m in selected:
            st.subheader(m)

            queries = sources_cfg["google_news_queries"].get(m, [])
            direct = sources_cfg["direct_rss"].get(m, [])

            # Auto-adjust max_items -> ESG keyword detected
            auto_max = max_items
            if expanded_keywords and any(
                k in ["esg", "sustainability", "csrd", "taxonomy", "sfdr"]
                for k in expanded_keywords
            ):
                auto_max = max(max_items, 35)
                st.sidebar.info(
                    "🔍 ESG-related search detected — fetching up to 35 articles per market for broader coverage."
                )

            articles = recent_articles_for_market(m, queries, direct)[:auto_max]


            # Filter -> publication date
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

            # keyword filter -> supports multiple terms + synonyms
            if expanded_keywords:
                def _match_article(a):
                    haystack = " ".join([
                        str(a.get("title", "")),
                        str(a.get("summary", "")),
                        str(a.get("source", "")),
                        str(a.get("link", "")),
                        str(a.get("query", "")),  
                    ]).lower()
                    return any(kw in haystack for kw in expanded_keywords)

                pre_count = len(articles)
                articles = [a for a in articles if _match_article(a)]
                post_count = len(articles)

                if post_count == 0:
                    st.warning(f"No articles in **{m}** matched keywords: {', '.join(sorted(expanded_keywords))}.")
                    continue
                else:
                    st.info(f"Keyword filter in **{m}**: {post_count}/{pre_count} articles matched.")

            if not articles:
                st.warning(f"No articles found for market '{m}' matching the selected filters.")
                continue

            # Display 
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

        if rows:
            df = pd.DataFrame(rows)
            st.session_state["df"] = df
        else:
            st.session_state["df"] = None

df = st.session_state.get("df")
if df is not None and not df.empty:
    st.divider()
    # Table Final
    st.markdown("### Table View / CSV Export")
    st.dataframe(df, use_container_width=True)
    st.download_button(
        "Download CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="regulatory_news.csv",
        mime="text/csv"
    )

    # Summary Metrics
    st.divider()
    st.subheader("Summary Statistics")

    total_articles = len(df)
    reg_articles = df["is_regulatory"].sum() if "is_regulatory" in df else 0
    perc_reg = (reg_articles / total_articles * 100) if total_articles > 0 else 0

    top_authority = (
        df["authority"].value_counts().idxmax()
        if "authority" in df and not df["authority"].isna().all()
        else "N/A"
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Articles", total_articles)
    col2.metric("Regulatory Articles", reg_articles, f"{perc_reg:.0f}%")
    col3.metric("Top Authority", top_authority)

    # Articles by Jurisdiction
    if "jurisdiction" in df and not df["jurisdiction"].isna().all():
        st.markdown("### Articles by Jurisdiction")
        import altair as alt
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("jurisdiction:N", title="Jurisdiction"),
                y=alt.Y("count():Q", title="Number of Articles"),
                color="jurisdiction:N",
                tooltip=["jurisdiction", "count()"],
            )
            .properties(width="container", height=350)
        )
        st.altair_chart(chart, use_container_width=True)

    # Regulatory Activity Over Time
    if "published" in df and not df["published"].isna().all():
        st.markdown("###  Regulatory Activity Over Time")
        df["published_dt"] = pd.to_datetime(df["published"], errors="coerce")
        df_timeline = (
            df.dropna(subset=["published_dt"])
            .groupby(pd.Grouper(key="published_dt", freq="M"))
            .size()
            .reset_index(name="count")
        )
        import altair as alt
        timeline_chart = (
            alt.Chart(df_timeline)
            .mark_line(point=True)
            .encode(
                x=alt.X("published_dt:T", title="Month"),
                y=alt.Y("count:Q", title="Number of Articles"),
                tooltip=["published_dt", "count"],
            )
            .properties(width="container", height=350)
        )
        st.altair_chart(timeline_chart, use_container_width=True)

    # Insights using LLM 
    if st.button("Generate Insights Summary"):
        with st.spinner("Analysing trends across articles..."):
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            context_text = "\n".join(
                f"[{r.get('jurisdiction','')}] {r.get('summary','')}"
                for _, r in df.iterrows()
                if isinstance(r.get("summary"), str)
            )
            prompt = (
                "Summarise the key regulatory themes and market focus across these news items. "
                "Identify any notable jurisdictions or recurring topics. "
                "Keep it concise (4-5 sentences).\n\n"
                f"{context_text}"
            )
            try:
                resp = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert analyst summarising global regulatory trends."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.4,
                    max_tokens=300,
                )
                insight = resp.choices[0].message.content.strip()
                st.success("### AI-Generated Insight")
                st.write(insight)
            except Exception as e:
                st.error(f"Insight generation failed: {e}")
else:
    st.write("Select markets and click **Fetch & Analyse** to begin.")
