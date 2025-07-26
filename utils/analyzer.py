import json
import re
import openai
import streamlit as st
from pydantic import BaseModel, Field

from config import Config

OPENROUTER_API_KEY = Config.LLM.OPENROUTER_API_KEY
OPENROUTER_API_URL = Config.LLM.OPENROUTER_API_URL
PERPLEXITY_MODEL = Config.LLM.OPENROUTER_MODEL

client = openai.OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_API_URL)


class TechnologyNewsAnalysis(BaseModel):
    feed_title: str = Field(..., description="Compelling 80-character headline")
    description: str = Field(..., description="Concise overview of main development")
    core_message: str = Field(..., description="Comprehensive summary covering all major points, context, implications from the entire article")
    key_tags: str = Field(..., description="Comma-separated keywords related to the news")
    sector: str = Field(..., description="Selected primary technology sector")
    published_date: str = Field(..., description="Published date of the news article in YYYY-MM-DD format")


def extract_json_from_text(text):
    """Extract JSON object from text response"""
    # Try to find JSON object in the text
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    return None


def parse_structured_text(content, published_date):
    """Parse structured text format into JSON"""
    data = {"published_date": published_date}
    
    patterns = {
        'feed_title': r'Feed Title:\s*(.+?)(?:\n|$)',
        'description': r'Description:\s*(.+?)(?:\n|$)',
        'core_message': r'Core Message:\s*(.+?)(?=\nKey Tags:|$)',
        'key_tags': r'Key Tags:\s*(.+?)(?:\n|$)',
        'sector': r'Sector:\s*(.+?)(?:\n|$)'
    }
    
    for field, pattern in patterns.items():
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            data[field] = match.group(1).strip()
    
    # Set defaults for missing fields
    data.setdefault('feed_title', 'Technology News Update')
    data.setdefault('description', 'Latest technology development')
    data.setdefault('core_message', 'Technology industry update')
    data.setdefault('key_tags', 'technology, news')
    data.setdefault('sector', 'Technology')
    
    return data


def analyze_news_content(link, published_date):
    try:
        prompt = f"""
            Analyze the following technology news link and return a JSON response with this exact structure:
            
            {{
                "feed_title": "Compelling 80-character headline",
                "description": "Concise overview of main development", 
                "core_message": "Comprehensive summary covering all major points, context, implications from the entire article. Remove citation brackets like [1], [2], [3] from text.",
                "key_tags": "keyword1, keyword2, keyword3, keyword4, keyword5",
                "sector": "Selected primary technology sector",
                "published_date": "{published_date}"
            }}

            Article to analyze: {link}
            
            Return only valid JSON without any markdown formatting or additional text.
        """

        raw_response = client.chat.completions.create(
            model=PERPLEXITY_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional AI assistant for structured technology news analysis. Always return valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )

        content = raw_response.choices[0].message.content
        if not content:
            st.error("❌ No content received from the analysis model.")
            return None

        
        # Try multiple parsing strategies
        response_data = None
        
        # Strategy 1: Direct JSON parsing
        try:
            response_data = json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON from text
        if not response_data:
            response_data = extract_json_from_text(content)
        
        # Strategy 3: Parse structured text format
        if not response_data:
            response_data = parse_structured_text(content, published_date)
        
        if not response_data:
            st.error("❌ Failed to parse response in any format")
            st.error(f"Raw content: {content}")
            return None
            
        return TechnologyNewsAnalysis(**response_data)

    except Exception as e:
        st.error(f"❌ Failed to analyze news content: {e}")
        return None