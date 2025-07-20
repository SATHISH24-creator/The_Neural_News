import streamlit as st

from config.rss_sources import rss_sources

class Config:
    TYPE = "service_account"
    PROJECT_ID = "eng-pulsar-466105-g5"

    class Credentials:
        CLIENT_ID = "115510078425093279793"
        CLIENT_EMAIL = st.secrets["client_email"]
        PRIVATE_KEY_ID = "f951f5767fc7138732a890cfac27fc75b3ee37a7"
        PRIVATE_KEY = st.secrets["private_key"]
        AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
        TOKEN_URI = "https://oauth2.googleapis.com/token"
        AUTH_PROVIDER_X509_CERT_URL = "https://www.googleapis.com/oauth2/v1/certs"
        CLIENT_X509_CERT_URL = "https://www.googleapis.com/robot/v1/metadata/x509/the-neural-872%40eng-pulsar-466105-g5.iam.gserviceaccount.com"
        UNIVERSE_DOMAIN = "googleapis.com"

    class LLM:
        OPENROUTER_API_KEY = st.secrets["openrouter_api_key"]
        OPENROUTER_API_URL = "https://openrouter.ai/api/v1"
        OPENROUTER_MODEL = "perplexity/sonar"


__all__ = ["Config", "rss_sources"]
