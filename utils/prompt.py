import requests
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
from urllib.parse import urljoin, urlparse

from utils.credentials import credentials_manager

@dataclass
class ArticleData:
    """Data class for article information"""
    title: str
    link: str
    published_date: str
    description: str
    core_message: str
    key_tags: str
    sector: str

class ArticleScraper:
    """Handles web scraping functionality with improved content extraction"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title using multiple strategies"""
        title_selectors = [
            'h1',
            '.article-title',
            '.post-title',
            '.entry-title',
            '.headline',
            'title',
            '[class*="title"]',
            '[class*="headline"]'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        # Fallback to page title
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        return "Title not found"
    
    def _extract_publication_date(self, soup: BeautifulSoup) -> str:
        """Extract publication date using multiple strategies"""
        date_selectors = [
            'time[datetime]',
            '.published-date',
            '.post-date',
            '.article-date',
            '[class*="date"]',
            '[class*="time"]'
        ]
        
        # Try datetime attribute first
        time_element = soup.select_one('time[datetime]')
        if time_element and time_element.get('datetime'):
            return time_element.get('datetime')
        
        # Try other selectors
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_text = element.get_text(strip=True)
                if date_text:
                    return date_text
        
        # Try meta tags
        meta_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publishdate"]',
            'meta[name="date"]',
            'meta[property="og:updated_time"]'
        ]
        
        for selector in meta_selectors:
            element = soup.select_one(selector)
            if element and element.get('content'):
                return element.get('content')
        
        return "Date not specified"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content with improved accuracy"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 
                           '.advertisement', '.ads', '.social-share', '.comments',
                           '.related-articles', '.sidebar', '.navigation']):
            element.decompose()
        
        # Content selectors in order of preference
        content_selectors = [
            'article .content',
            'article .article-content',
            'article .post-content',
            'article .entry-content',
            '.article-body',
            '.post-body',
            '.entry-body',
            '.story-body',
            '.content-body',
            'article',
            '.article-content',
            '.post-content',
            '.entry-content',
            'main .content',
            'main',
            '.main-content'
        ]
        
        content = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                # Get the largest content block
                largest_element = max(elements, key=lambda x: len(x.get_text()))
                content = largest_element.get_text()
                break
        
        if not content:
            # Fallback to body content
            body = soup.find('body')
            if body:
                content = body.get_text()
        
        # Clean up the content
        if content:
            lines = (line.strip() for line in content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = ' '.join(chunk for chunk in chunks if chunk and len(chunk) > 3)
            
            # Remove excessive whitespace
            content = re.sub(r'\s+', ' ', content)
            
            # Limit content length for API efficiency
            return content[:8000] if content else ""
        
        return ""
    
    def scrape_content(self, url: str) -> Optional[Dict[str, str]]:
        """Scrape article content, title, and metadata from URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract components
            title = self._extract_title(soup)
            content = self._extract_content(soup)
            pub_date = self._extract_publication_date(soup)
            
            if not content or len(content) < 100:
                return None
            
            return {
                'title': title,
                'content': content,
                'published_date': pub_date,
                'url': url
            }
            
        except requests.exceptions.Timeout:
            return None
        except requests.exceptions.RequestException:
            return None
        except Exception:
            return None

class AIAnalyzer:
    """Handles AI-powered article analysis with improved prompting"""
    
    def __init__(self):
        self.api_key, self.api_url = credentials_manager.get_openrouter_credentials()
        self.model = credentials_manager.get_perplexity_model()
        
    def _create_analysis_prompt(self, scraped_data: Dict[str, str]) -> str:
        """Create comprehensive structured prompt for article analysis"""
        return f"""
You are a professional news analyst. Analyze the following news article and provide a comprehensive, structured response.

**ARTICLE INFORMATION:**
- URL: {scraped_data['url']}
- Extracted Title: {scraped_data['title']}
- Published Date: {scraped_data['published_date']}

**ARTICLE CONTENT:**
{scraped_data['content']}

**ANALYSIS REQUIREMENTS:**
Please provide your analysis in this EXACT format with proper labels:

TITLE: [Provide a clear, engaging title that captures the essence of the article. If the extracted title is good, use it; otherwise, create a better one]

DESCRIPTION: [Write a comprehensive 3-4 sentence summary that captures the key points, main stakeholders, and significance of the news]

CORE_MESSAGE: [Identify the single most important takeaway or message from this article in 1-2 clear sentences]

KEY_TAGS: [List 6-8 relevant, specific tags separated by commas. Include: industry terms, company names, technology types, geographic locations, and key concepts]

SECTOR: [Identify the primary business sector/industry this news relates to - be specific (e.g., "Financial Technology", "Renewable Energy", "Healthcare AI", etc.)]

PUBLISHED_DATE: [Use the extracted date: {scraped_data['published_date']}]

**IMPORTANT:** 
- Ensure each section is clearly labeled and properly formatted
- Be accurate and factual based on the article content
- Make the analysis comprehensive yet concise
- Focus on business and industry relevance
"""
    
    def analyze_article(self, scraped_data: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Analyze article using Perplexity API with enhanced error handling"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional news analyst who provides structured, accurate analysis of news articles. Always follow the exact format requested and provide comprehensive insights."
                    },
                    {
                        "role": "user",
                        "content": self._create_analysis_prompt(scraped_data)
                    }
                ],
                "max_tokens": 1500,
                "temperature": 0.3,
                "top_p": 0.9
            }

            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=headers, 
                json=data,
                timeout=45
            )
            
            if response.status_code != 200:
                return None
            
            if not response.text.strip():
                return None
            
            try:
                result = response.json()
            except json.JSONDecodeError:
                return None
            
            if 'choices' not in result or not result['choices']:
                return None
                
            if 'message' not in result['choices'][0]:
                return None
            
            analysis_text = result['choices'][0]['message']['content']
            
            parsed_analysis = self._parse_analysis_response(analysis_text)
            
            return parsed_analysis
            
        except requests.exceptions.Timeout:
            return None
        except requests.exceptions.RequestException:
            return None
        except Exception:
            return None
    
    def _parse_analysis_response(self, analysis_text: str) -> Dict[str, str]:
        """Parse structured response from AI analysis with improved parsing"""
        analysis = {}
        lines = analysis_text.split('\n')
        
        field_mappings = {
            'TITLE:': 'title',
            'DESCRIPTION:': 'description',
            'CORE_MESSAGE:': 'core_message',
            'KEY_TAGS:': 'key_tags',
            'SECTOR:': 'sector',
            'PUBLISHED_DATE:': 'published_date'
        }
        
        current_field = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Check if line starts with a field label
            found_field = False
            for prefix, field in field_mappings.items():
                if line.startswith(prefix):
                    # Save previous field if exists
                    if current_field and current_content:
                        analysis[current_field] = ' '.join(current_content).strip()
                    
                    # Start new field
                    current_field = field
                    current_content = [line.replace(prefix, '').strip()]
                    found_field = True
                    break
            
            # If not a field label and we have a current field, add to content
            if not found_field and current_field and line:
                current_content.append(line)
        
        # Don't forget the last field
        if current_field and current_content:
            analysis[current_field] = ' '.join(current_content).strip()
        
        # Set defaults for missing fields
        defaults = {
            'title': 'Title not found',
            'description': 'Description not available',
            'core_message': 'Core message not available',
            'key_tags': 'Tags not available',
            'sector': 'Sector not specified',
            'published_date': 'Not specified'
        }
        
        for field, default in defaults.items():
            if field not in analysis or not analysis[field]:
                analysis[field] = default
        
        return analysis

class GoogleSheetsManager:
    """Handles Google Sheets operations using credentials from secrets.toml"""
    
    def __init__(self):
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
    
    def connect(self) -> Optional[gspread.Client]:
        """Connect to Google Sheets using credentials manager"""
        try:
            # Create temporary credentials file
            temp_credentials_path = credentials_manager.create_temp_credentials_file()
            
            try:
                creds = ServiceAccountCredentials.from_json_keyfile_name(
                    temp_credentials_path, self.scope
                )
                client = gspread.authorize(creds)
                return client
            finally:
                # Clean up temporary file
                credentials_manager.cleanup_temp_file(temp_credentials_path)
                
        except Exception:
            return None
    
    def list_spreadsheets(self, client: gspread.Client) -> List[str]:
        """List all available spreadsheets"""
        try:
            sheets = client.list_spreadsheet_files()
            return [sheet['name'] for sheet in sheets]
        except Exception:
            return []
    
    def list_worksheets(self, sheet) -> List[str]:
        """List all worksheets in a spreadsheet"""
        try:
            return [ws.title for ws in sheet.worksheets()]
        except Exception:
            return []
    
    def save_articles(self, worksheet, articles: List[ArticleData]) -> int:
        """Save analyzed articles to Google Sheets"""
        try:
            headers = [
                "Original Title", "Link", "Published Date",
                "Description", "Core Message", "Key Tags", "Sector", "Extracted Date"
            ]

            existing = worksheet.get_all_values()
            if not existing or existing[0] != headers:
                worksheet.clear()
                worksheet.append_row(headers)

            existing_links = set(row[1] for row in existing[1:] if len(row) > 1)
            new_rows = []
            current_date = datetime.utcnow().strftime("%Y-%m-%d")

            for article in articles:
                if article.link not in existing_links:
                    new_row = [
                        article.title, article.link, article.published_date,
                        article.description, article.core_message,
                        article.key_tags, article.sector, current_date
                    ]
                    new_rows.append(new_row)

            if new_rows:
                worksheet.append_rows(new_rows)
                return len(new_rows)

            return 0

        except Exception:
            return 0

class NewsAnalysisWorkflow:
    """Main workflow orchestrator with improved processing"""
    
    def __init__(self):
        self.scraper = ArticleScraper()
        self.analyzer = AIAnalyzer()
        self.sheets_manager = GoogleSheetsManager()
    
    def process_urls(self, urls: List[str], progress_callback=None) -> List[ArticleData]:
        """Process multiple URLs and analyze them with improved error handling"""
        analyzed_articles = []
        
        for i, url in enumerate(urls):
            try:
                if progress_callback:
                    progress_callback(i, len(urls), f"Processing: {url[:50]}...")
                
                # Scrape content
                scraped_data = self.scraper.scrape_content(url)
                if not scraped_data:
                    continue
                
                # Analyze with AI
                analysis = self.analyzer.analyze_article(scraped_data)
                if not analysis:
                    continue
                
                # Create ArticleData object
                article = ArticleData(
                    title=analysis['title'],
                    link=url,
                    published_date=analysis['published_date'],
                    description=analysis['description'],
                    core_message=analysis['core_message'],
                    key_tags=analysis['key_tags'],
                    sector=analysis['sector']
                )
                
                analyzed_articles.append(article)
                
                # Rate limiting to avoid overwhelming the API
                if i < len(urls) - 1:  # Don't sleep after the last item
                    time.sleep(2)
                
            except Exception:
                continue
        
        return analyzed_articles
    
    def process_file_data(self, df: pd.DataFrame, url_column: str, 
                         title_column: Optional[str] = None, 
                         limit: int = 10) -> List[ArticleData]:
        """Process URLs from uploaded file"""
        urls = df[url_column].dropna().tolist()[:limit]
        return self.process_urls(urls)
    
    def save_to_sheets(self, articles: List[ArticleData], 
                      spreadsheet_name: str, worksheet_name: str) -> int:
        """Save articles to Google Sheets"""
        client = self.sheets_manager.connect()
        if not client:
            return 0
        
        try:
            sheet = client.open(spreadsheet_name)
            worksheet = sheet.worksheet(worksheet_name)
            return self.sheets_manager.save_articles(worksheet, articles)
        except Exception:
            return 0
    
    def export_to_csv(self, articles: List[ArticleData]) -> str:
        """Export articles to CSV format"""
        data = []
        for article in articles:
            data.append({
                'Title': article.title,
                'Link': article.link,
                'Published Date': article.published_date,
                'Description': article.description,
                'Core Message': article.core_message,
                'Key Tags': article.key_tags,
                'Sector': article.sector
            })
        
        df = pd.DataFrame(data)
        return df.to_csv(index=False)

# Global workflow instance
workflow = NewsAnalysisWorkflow()