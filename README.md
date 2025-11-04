# NBIM Regulatory News — LLM Dashboard
This Streamlit dashboard automatically fetches regulatory and policy news for NBIM’s five biggest markets (US, UK, EU, Norway, Japan).  
It uses RSS feeds and LLM-based text classification to identify, summarise, and tag news that is relevant to financial regulation.

---

## Features
- Fetches the latest regulatory news from Google News and direct regulator RSS feeds.
- Uses OpenAI's GPT-4 model to:
  - Identify if an article is regulatory.
  - Extract jurisdiction, authority, topic, and implications.
- Displays results in a clean card based layout.
- Displays insights and visual summaries, including a bar charts of article distribution by jurisdiction and summary statistics.
- Allows users to generate overall market insights using an LLM summariser.
- Adds a keyword search filter to find articles by topic or term (e.g., ESG, crypto).
- Includes a date range filter for temporal selection.
- Allows CSV export of the analysed articles.

---

## Tools and Libraries
- **Python 3.9+**
- **Streamlit**
- **Feedparser**
- **OpenAI API**
- **PyYAML**
- **Pandas**

---

## Notes
- RSS feeds typically include only recent articles (usually from the past months). Older news (for example, from 2024) may not appear because RSS feeds are not historical archives.
- The date range filter is included to demonstrate how time based filtering logic works in a real world dashboard, and it would apply smoothly if connected to a historical API or database.
