import requests
import json
import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime

class ContentGenerator:
    def __init__(self):
        # OpenRouter API configuration
        self.api_key = st.secrets["OPENROUTER_API_KEY"]
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "perplexity/sonar-pro"
        
        # Headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_content(self, prompt: str, platform: str = "general") -> str:
        """
        Generate content using OpenRouter API
        
        Args:
            prompt (str): The content generation prompt
            platform (str): Platform type for context (linkedin, youtube, newsletter)
        
        Returns:
            str: Generated content
        """
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are a professional content creator specialized in {platform} content. Generate high-quality, engaging content that follows best practices for {platform}."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            return f"Error generating content: {str(e)}"
        except KeyError as e:
            return f"Error parsing response: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    def generate_linkedin_content(self, entry_data: Dict) -> str:
        """
        Generate LinkedIn content from analyzed entry data
        
        Args:
            entry_data (Dict): Analyzed entry data
        
        Returns:
            str: LinkedIn post content
        """
        analysis = entry_data.get("analysis_data", {})
        
        prompt = f"""
        Create a professional LinkedIn post based on this analyzed news article:
        
        Title: {analysis.get('feed_title', entry_data.get('title', ''))}
        Core Message: {analysis.get('core_message', '')}
        Description: {analysis.get('description', '')}
        Key Tags: {analysis.get('key_tags', '')}
        Sector: {analysis.get('sector', '')}
        
        Requirements:
        - Professional tone but engaging
        - 2-3 paragraphs maximum
        - Include relevant hashtags (3-5)
        - Add a thought-provoking question or call-to-action
        - Make it valuable for professional network
        - Keep it concise and impactful
        - Reference the original article insights
        
        Format the post ready to copy-paste to LinkedIn.
        """
        
        return self.generate_content(prompt, "linkedin")
    
    def generate_youtube_content(self, entry_data: Dict) -> str:
        """
        Generate YouTube content from analyzed entry data
        
        Args:
            entry_data (Dict): Analyzed entry data
        
        Returns:
            str: YouTube content
        """
        analysis = entry_data.get("analysis_data", {})
        
        prompt = f"""
        Create YouTube video content based on this analyzed news article:
        
        Title: {analysis.get('feed_title', entry_data.get('title', ''))}
        Core Message: {analysis.get('core_message', '')}
        Description: {analysis.get('description', '')}
        Key Tags: {analysis.get('key_tags', '')}
        Sector: {analysis.get('sector', '')}
        
        Include:
        1. Engaging video title (60 characters or less)
        2. Video description (first 125 characters should be compelling)
        3. Tags (10-15 relevant tags)
        4. Brief video script outline or key points (5-7 main points)
        5. Call-to-action suggestions
        6. Thumbnail suggestions
        
        Make it optimized for YouTube SEO and engagement.
        """
        
        return self.generate_content(prompt, "youtube")
    
    def generate_newsletter_content(self, entry_data: Dict) -> str:
        """
        Generate Newsletter content from analyzed entry data
        
        Args:
            entry_data (Dict): Analyzed entry data
        
        Returns:
            str: Newsletter content
        """
        analysis = entry_data.get("analysis_data", {})
        
        prompt = f"""
        Create newsletter content based on this analyzed news article:
        
        Title: {analysis.get('feed_title', entry_data.get('title', ''))}
        Core Message: {analysis.get('core_message', '')}
        Description: {analysis.get('description', '')}
        Key Tags: {analysis.get('key_tags', '')}
        Sector: {analysis.get('sector', '')}
        Published: {entry_data.get('published_date', '')}
        
        Create a newsletter section that includes:
        1. Catchy headline
        2. Brief summary (2-3 sentences)
        3. Key insights and implications
        4. Why this matters to readers
        5. Link to original article
        6. Call-to-action or discussion prompt
        
        Format it for email newsletter with clear sections and engaging tone.
        Make it informative yet conversational.
        """
        
        return self.generate_content(prompt, "newsletter")


# Initialize the content generator
@st.cache_resource
def get_content_generator():
    return ContentGenerator()