import json
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


def analyze_news_content(link, published_date):
    try:
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

        raw_response = client.chat.completions.create(
            model=PERPLEXITY_MODEL,
            messages=[
                { "role": "system","content": "You are a professional AI assistant for structured technology news analysis." },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "technology_news_analysis",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "feed_title": {"type": "string"},
                            "description": {"type": "string"},
                            "core_message": {"type": "string"},
                            "key_tags": {"type": "string"},
                            "sector": {"type": "string"},
                            "published_date": {"type": "string"}
                        },
                        "required": ["feed_title", "description", "core_message", "key_tags", "sector", "published_date"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )

        content = raw_response.choices[0].message.content
        if not content:
            print(raw_response)
            st.error("❌ No content received from the analysis model.")
            return None

        print(f"Raw API response content: {content}")
        
        try:
            response = json.loads(content)
        except json.JSONDecodeError as json_error:
            st.error(f"❌ Failed to parse JSON response: {json_error}")
            st.error(f"Raw content: {content}")
            return None
            
        return TechnologyNewsAnalysis(**response)

    except Exception as e:
        st.error(f"❌ Failed to analyze news content: {e}")
        return None