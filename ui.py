import streamlit as st
from typing import List, Dict, Any, Optional
import re

FLAGS = {
    "US": "🇺🇸",
    "UK": "🇬🇧",
    "EU": "🇪🇺",
    "NO": "🇳🇴",
    "JP": "🇯🇵"
}

def article_card(a: Dict[str, Any], llm: Optional[Dict[str, Any]] = None):
    def clean_html(text: str) -> str:
        text = re.sub(r'<a[^>]*>.*?</a>', '', text, flags=re.DOTALL)
        text = re.sub(r'<font[^>]*>.*?</font>', '', text, flags=re.DOTALL)

        text = re.sub(r'<.*?>', '', text)
        return text.strip()
    
    raw_title = a.get("title", "(no title)")
    clean_title = clean_html(raw_title)
    link = a.get('link', '')
    
    raw_source = a.get("source", "")
    clean_source = clean_html(raw_source)
    published = a.get('published', '')

    raw_summary = a.get("summary", "") or ""
    clean_summary = clean_html(raw_summary)

    with st.container():
        st.markdown(
            """
            <style>
            .article-container {
                max-width: 1150px;
                margin: 15px auto;
                padding: 3px 10px; 
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.4;
                color: #222;
            }
            .article-title {
                font-weight: 700;
                font-size: 1.6rem;
                margin-bottom: 0.4rem;
                text-align: center;
            }
            .article-meta {
                font-style: italic;
                font-size: 0.85rem;
                color: #555;
                margin-bottom: 0.3rem;
                text-align: left; 
            }
            .article-summary {
                margin-top: -0.4em;
                margin-bottom: 0.8em;
                font-size: 1rem;
                color: #333;
            }
            .divider {
                border-top: 1px solid #ddd;
                margin: 0.3em 0;
            }
            .metrics-row {
                display: flex;
                justify-content: space-around;
                font-size: 0.95rem;
                margin-bottom: 0.4em;
                font-weight: 600;
                color: #444;
            }
            .metrics-row div {
                flex: 1;
                text-align: center;
            }
            .llm-text {
                margin-top: 0.1em;
                font-size: 0.95rem;
                color: #333;
                line-height: 1.3;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown(f"<div class='article-container'>", unsafe_allow_html=True)
        st.markdown(f"<a href='{link}' target='_blank' rel='noopener noreferrer' class='article-title'>{clean_title}</a>", unsafe_allow_html=True)
        if clean_source or published:
            meta_text = f"{clean_source} — {published}".strip(" —")
            st.markdown(f"<div class='article-meta'>{meta_text}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='article-summary'>{clean_summary}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='divider'></div>", unsafe_allow_html=True)

        if llm:
            is_reg = llm.get("is_regulatory")
            reg_icon = "✅" if is_reg else "❌"
            jurisdiction = llm.get('jurisdiction','-').upper()
            flag = FLAGS.get(jurisdiction, '')
            authority = llm.get('authority','-')
            topic = llm.get('topic','-')
            summary_llm = llm.get('summary','')
            implications = llm.get('implications','')
            tags = llm.get("risk_tags") or []

            st.markdown("<div class='metrics-row'>", unsafe_allow_html=True)
            st.markdown(f"<div>Regulatory? {reg_icon}</div>", unsafe_allow_html=True)
            st.markdown(f"<div>Jurisdiction: {flag} {jurisdiction if jurisdiction != '-' else '-'}</div>", unsafe_allow_html=True)
            st.markdown(f"<div>Authority: {authority}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if is_reg or any([topic, summary_llm, implications, tags]):
                if topic:
                    st.markdown(f"<div class='llm-text'><strong>Topic:</strong> {topic}</div>", unsafe_allow_html=True)
                if summary_llm:
                    st.markdown(f"<div class='llm-text'><strong>Summary (LLM):</strong> {summary_llm}</div>", unsafe_allow_html=True)
                if implications:
                    st.markdown(f"<div class='llm-text'><strong>Implications:</strong> {implications}</div>", unsafe_allow_html=True)
                if isinstance(tags, list) and tags:
                    st.markdown(f"<div class='llm-text'><strong>Risk tags:</strong> {', '.join(tags)}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='llm-text' style='color:#777;font-style:italic;'>No regulatory content detected.</div>", unsafe_allow_html=True)
                
        st.markdown("</div>", unsafe_allow_html=True)
