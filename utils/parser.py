import re
import streamlit as st
from bs4 import BeautifulSoup

def clean_html_tags(text):
    """Remove HTML tags and return clean text."""
    soup = BeautifulSoup(text, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.insert_before("\n")
    return soup.get_text(separator=" ", strip=True)

def parse_analysis_response(content):
    """Parse AI response formatted by the Technology News Analysis Template."""
    try:
        analysis_data = {}

        patterns = {
            'feed_title': r'Feed Title:\s*(.*?)(?=\n[A-Z][a-z ]+:|$)',
            'description': r'Description:\s*(.*?)(?=\n[A-Z][a-z ]+:|$)',
            'core_message': r'Core Message:\s*(.*?)(?=\nKey Tags:|$)',
            'key_tags': r'Key Tags:\s*(.*?)(?=\n[A-Z][a-z ]+:|$)',
            'sector': r'Sector:\s*(.*?)(?=\n[A-Z][a-z ]+:|$)',
            'published_date': r'Published Date:\s*(.*?)(?=\n[A-Z][a-z ]+:|$)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            analysis_data[key] = match.group(1).strip() if match else ""

        if analysis_data['core_message']:
            analysis_data['core_message'] = re.sub(r'\s+', ' ', analysis_data['core_message']).strip()

        if not any(analysis_data.values()):
            st.error("❌ Could not parse analysis response properly")
            st.error(f"Raw response: {content}")
            return None

        return analysis_data

    except Exception as e:
        st.error(f"❌ Error parsing analysis response: {str(e)}")
        st.error(f"Content to parse: {content}")
        return None