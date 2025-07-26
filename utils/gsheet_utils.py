import gspread
import streamlit as st
from datetime import datetime
import os
import tempfile

# Try to import both credential approaches
try:
    from google.oauth2.service_account import Credentials as GoogleCredentials
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False

try:
    from oauth2client.service_account import ServiceAccountCredentials
    OAUTH2CLIENT_AVAILABLE = True
except ImportError:
    OAUTH2CLIENT_AVAILABLE = False

# Try to import config modules
try:
    from config import Config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

try:
    from credentials import credentials_manager
    CREDENTIALS_MANAGER_AVAILABLE = True
except ImportError:
    CREDENTIALS_MANAGER_AVAILABLE = False


def connect_gspread_client():
    """
    Connect to Google Sheets using available authentication method.
    Tries multiple approaches based on available modules and configuration.
    """
    # Method 1: Using google.oauth2.service_account with Config class
    if GOOGLE_AUTH_AVAILABLE and CONFIG_AVAILABLE:
        try:
            credentials_json = {
                "type": "service_account",
                "client_id": Config.Credentials.CLIENT_ID,
                "client_email": Config.Credentials.CLIENT_EMAIL,
                "private_key": Config.Credentials.PRIVATE_KEY,
                "private_key_id": Config.Credentials.PRIVATE_KEY_ID,
                "token_uri": Config.Credentials.TOKEN_URI,
                "project_id": Config.PROJECT_ID,
            }
            
            scope = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            
            creds = GoogleCredentials.from_service_account_info(credentials_json, scopes=scope)
            client = gspread.authorize(creds)
            return client
            
        except Exception as e:
            st.warning(f"Config-based authentication failed: {str(e)}")
    
    # Method 2: Using oauth2client with credentials manager
    if OAUTH2CLIENT_AVAILABLE and CREDENTIALS_MANAGER_AVAILABLE:
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Create temporary credentials file
            temp_credentials_path = credentials_manager.create_temp_credentials_file()
            
            try:
                creds = ServiceAccountCredentials.from_json_keyfile_name(temp_credentials_path, scope)
                client = gspread.authorize(creds)
                return client
            finally:
                # Clean up temporary file
                if os.path.exists(temp_credentials_path):
                    os.unlink(temp_credentials_path)
                    
        except Exception as e:
            st.warning(f"Credentials manager authentication failed: {str(e)}")
    
    # Method 3: Using streamlit secrets with google.oauth2.service_account
    if GOOGLE_AUTH_AVAILABLE:
        try:
            # Try to get credentials from streamlit secrets
            secrets = st.secrets.get("gcp_service_account", {})
            if secrets:
                scope = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
                
                creds = GoogleCredentials.from_service_account_info(secrets, scopes=scope)
                client = gspread.authorize(creds)
                return client
                
        except Exception as e:
            st.warning(f"Streamlit secrets authentication failed: {str(e)}")
    
    # Method 4: Using streamlit secrets with oauth2client
    if OAUTH2CLIENT_AVAILABLE:
        try:
            secrets = st.secrets.get("gcp_service_account", {})
            if secrets:
                scope = [
                    'https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive'
                ]
                
                # Create temporary file for oauth2client
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    import json
                    json.dump(dict(secrets), f)
                    temp_path = f.name
                
                try:
                    creds = ServiceAccountCredentials.from_json_keyfile_name(temp_path, scope)
                    client = gspread.authorize(creds)
                    return client
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        
        except Exception as e:
            st.warning(f"OAuth2Client with secrets authentication failed: {str(e)}")
    
    # If all methods fail
    st.error("Unable to connect to Google Sheets. Please check your credentials configuration.")
    return None


def list_spreadsheets(client):
    """List all available spreadsheets"""
    if not client:
        return []
    
    try:
        sheets = client.list_spreadsheet_files()
        return [sheet['name'] for sheet in sheets]
    except Exception as e:
        st.error(f"Error listing spreadsheets: {str(e)}")
        return []


def list_worksheets(sheet):
    """List all worksheets in a spreadsheet"""
    if not sheet:
        return []
    
    try:
        return [ws.title for ws in sheet.worksheets()]
    except Exception as e:
        st.error(f"Error listing worksheets: {str(e)}")
        return []


def save_analyzed_entries_to_sheets(worksheet, entries):
    """Save analyzed entries to Google Sheets with enhanced data"""
    if not worksheet or not entries:
        return 0
    
    try:
        headers = [
            "Original Title",
            "Enhanced Title", 
            "Link",
            "Original Published Date",
            "Description",
            "Core Message",
            "Key Tags",
            "Sector",
            "Source",
            "Extracted Date"
        ]
        
        # Get existing data
        existing = worksheet.get_all_values()
        
        # Set headers if not present or different
        if not existing or existing[0] != headers:
            worksheet.clear()
            worksheet.append_row(headers)
            existing = [headers]
        
        # Get existing links to avoid duplicates
        existing_links = set(row[2] for row in existing[1:] if len(row) > 2)
        
        # Prepare new rows
        new_rows = []
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        for entry in entries:
            # Only add analyzed entries that don't already exist
            if (entry.get("link") not in existing_links and 
                entry.get("analyzed", False)):
                
                analysis = entry.get("analysis_data", {})
                new_row = [
                    entry.get("title", ""),
                    analysis.get("feed_title", ""),
                    entry.get("link", ""),
                    entry.get("published_date", ""),
                    analysis.get("description", ""),
                    analysis.get("core_message", ""),
                    analysis.get("key_tags", ""),
                    analysis.get("sector", ""),
                    entry.get("source", ""),
                    current_date
                ]
                new_rows.append(new_row)
        
        # Add new rows if any
        if new_rows:
            worksheet.append_rows(new_rows)
            return len(new_rows)
        
        return 0
        
    except Exception as e:
        st.error(f"Error saving to sheets: {str(e)}")
        return 0


def get_spreadsheet_url():
    """Get the spreadsheet URL from various sources"""
    try:
        # Try streamlit secrets first
        url = st.secrets.get("spreadsheet", "")
        if url:
            return url
            
        # Try config module if available
        if CONFIG_AVAILABLE and hasattr(Config, 'SPREADSHEET_URL'):
            return Config.SPREADSHEET_URL
            
        return ""
        
    except Exception as e:
        st.warning(f"Could not retrieve spreadsheet URL: {str(e)}")
        return ""


def get_spreadsheet_by_url(client, url):
    """Get spreadsheet by URL"""
    if not client or not url:
        return None
        
    try:
        return client.open_by_url(url)
    except Exception as e:
        st.error(f"Error opening spreadsheet by URL: {str(e)}")
        return None


def get_spreadsheet_by_name(client, name):
    """Get spreadsheet by name"""
    if not client or not name:
        return None
        
    try:
        return client.open(name)
    except Exception as e:
        st.error(f"Error opening spreadsheet '{name}': {str(e)}")
        return None