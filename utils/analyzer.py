import requests
import streamlit as st
from datetime import datetime
from utils.parser import parse_analysis_response
import json
import os

# OpenRouter API configuration
CRED_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials.json")
# Load credentials
with open(CRED_PATH, "r") as f:
    creds = json.load(f)

OPENROUTER_API_KEY = creds["OPENROUTER_API_KEY"]
OPENROUTER_API_URL = creds["OPENROUTER_API_URL"]
PERPLEXITY_MODEL = creds["PERPLEXITY_MODEL"]
def analyze_news_content(link, published_date):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        extracted_date = datetime.utcnow().strftime("%Y-%m-%d")

        prompt = f"""
# Technology News Analysis Prompt Template

## System Instructions
You are a specialized AI assistant designed to analyze technology news articles with precision and depth. Your role is to transform raw news content into structured, actionable insights that provide comprehensive understanding of technological developments, market movements, and industry trends.

## Required Output Format

Feed Title: [Your compelling 80-character headline]

Description: [Concise overview of main development]

Core Message: [Comprehensive summary covering all major points, context, implications from the entire article and Remove citation brackets like [1], [2], [3] from text.]

Key Tags: [keyword1, keyword2, keyword3, keyword4, keyword5]

Sector: [Selected primary technology sector]

Published Date: {published_date}


## Article to Analyze:
{link}
"""

        payload = {
            "model": PERPLEXITY_MODEL,
            "messages": [
                {"role": "system", "content": "You are a professional AI assistant for structured technology news analysis."},
                {"role": "user", "content": prompt.strip()}
            ],
            "max_tokens": 1000,
            "temperature": 0.3,
        }

        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        ai_response = data["choices"][0]["message"]["content"]
        return parse_analysis_response(ai_response)

    except Exception as e:
        st.error(f"❌ Failed to analyze news content: {e}")
        return None