import os
import streamlit as st
import json
import tempfile
from dataclasses import dataclass
from typing import Optional

@dataclass
class APICredentials:
    """Data class to store API credentials"""
    openrouter_api_key: str
    openrouter_api_url: str
    perplexity_model: str
    google_credentials: dict

class CredentialsManager:
    """Manages all application credentials and configuration"""
    
    def __init__(self):
        self.api_credentials = self._load_credentials()
    
    def _load_credentials(self) -> APICredentials:
        """Load credentials from Streamlit secrets or environment variables"""
        # Load from Streamlit secrets (secrets.toml)
        try:
            google_creds = {
                "type": st.secrets["type"],
                "project_id": st.secrets["project_id"],
                "private_key_id": st.secrets["private_key_id"],
                "private_key": st.secrets["private_key"],
                "client_email": st.secrets["client_email"],
                "client_id": st.secrets["client_id"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": st.secrets["token_uri"],
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{st.secrets['client_email']}"
            }
            
            openrouter_key = st.secrets["OPENROUTER_API_KEY"]
            
        except (KeyError, AttributeError):
            # Fallback to environment variables
            google_creds = {
                "type": os.getenv("GOOGLE_TYPE", "service_account"),
                "project_id": os.getenv("GOOGLE_PROJECT_ID", ""),
                "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID", ""),
                "private_key": os.getenv("GOOGLE_PRIVATE_KEY", "").replace('\\n', '\n'),
                "client_email": os.getenv("GOOGLE_CLIENT_EMAIL", ""),
                "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('GOOGLE_CLIENT_EMAIL', '')}"
            }
            
            openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        
        return APICredentials(
            openrouter_api_key=openrouter_key,
            openrouter_api_url=os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1"),
            perplexity_model=os.getenv("PERPLEXITY_MODEL", "perplexity/sonar-pro"),
            google_credentials=google_creds
        )
    
    def get_openrouter_credentials(self) -> tuple[str, str]:
        """Get OpenRouter API credentials"""
        return self.api_credentials.openrouter_api_key, self.api_credentials.openrouter_api_url
    
    def get_perplexity_model(self) -> str:
        """Get Perplexity model name"""
        return self.api_credentials.perplexity_model
    
    def get_google_credentials_dict(self) -> dict:
        """Get Google credentials as dictionary"""
        return self.api_credentials.google_credentials
    
    def create_temp_credentials_file(self) -> str:
        """Create a temporary credentials file and return its path"""
        credentials_dict = self.get_google_credentials_dict()
        
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(credentials_dict, temp_file, indent=2)
        temp_file.close()
        
        return temp_file.name
    
    def cleanup_temp_file(self, file_path: str):
        """Clean up temporary credentials file"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass  # Ignore cleanup errors
    
    def validate_credentials(self) -> dict[str, bool]:
        """Validate if all required credentials are available"""
        google_creds = self.api_credentials.google_credentials
        
        validation_results = {
            "openrouter_api_key": bool(self.api_credentials.openrouter_api_key),
            "google_service_account": all([
                google_creds.get("type"),
                google_creds.get("project_id"),
                google_creds.get("private_key"),
                google_creds.get("client_email")
            ])
        }
        return validation_results
    
    def get_credentials_status(self) -> str:
        """Get human-readable credentials status"""
        validation = self.validate_credentials()
        if all(validation.values()):
            return "✅ All credentials configured"
        else:
            missing = [key for key, valid in validation.items() if not valid]
            return f"❌ Missing credentials: {', '.join(missing)}"

# Global credentials manager instance
credentials_manager = CredentialsManager()