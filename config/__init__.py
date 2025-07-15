import streamlit as st

from rss_sources import rss_sources


class Config:
    TYPE = "service_account"
    PROJECT_ID = "theneural-ai-news"

    class Credentials:
        CLIENT_ID = "107320439288964420848"
        CLIENT_EMAIL = st.secrets["client_email"]
        PRIVATE_KEY_ID = "247212d8193e448e92aa229295baefefa58e1dd7"
        PRIVATE_KEY = st.secrets["private_key"]
        AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
        TOKEN_URI = "https://oauth2.googleapis.com/token"
        AUTH_PROVIDER_X509_CERT_URL = "https://www.googleapis.com/oauth2/v1/certs"
        CLIENT_X509_CERT_URL = "https://www.googleapis.com/robot/v1/metadata/x509/news-api%40theneural-ai-news.iam.gserviceaccount.com"
        UNIVERSE_DOMAIN = "googleapis.com"

    class LLM:
        OPENROUTER_API_KEY = st.secrets["openrouter_api_key"]
        OPENROUTER_API_URL = "https://openrouter.ai/api/v1"
        OPENROUTER_MODEL = "perplexity/sonar-pro"


__all__ = ["Config", "rss_sources"]
