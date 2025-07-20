import gspread
import streamlit as st
from datetime import datetime
from google.oauth2 import service_account
import json

from config import Config

def get_credentials_dict():
    """Create credentials dictionary with proper format"""
    # Clean and format private key properly
    private_key = Config.Credentials.PRIVATE_KEY
    
    # Handle different private key formats
    if isinstance(private_key, str):
        # Replace literal \n with actual newlines
        private_key = private_key.replace('\\n', '\n')
        
        # Ensure proper BEGIN/END format
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            # If key is just the base64 content, wrap it
            lines = private_key.strip().split('\n')
            if len(lines) == 1:  # Single line key
                # Split into 64-char lines
                key_content = lines[0]
                formatted_lines = []
                for i in range(0, len(key_content), 64):
                    formatted_lines.append(key_content[i:i+64])
                private_key = '-----BEGIN PRIVATE KEY-----\n' + '\n'.join(formatted_lines) + '\n-----END PRIVATE KEY-----'
    
    return {
        "type": "service_account",
        "project_id": Config.PROJECT_ID,
        "private_key_id": Config.Credentials.PRIVATE_KEY_ID,
        "private_key": private_key,
        "client_email": Config.Credentials.CLIENT_EMAIL,
        "client_id": Config.Credentials.CLIENT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": Config.Credentials.TOKEN_URI,
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{Config.Credentials.CLIENT_EMAIL}"
    }

def connect_gspread_client():
    """Connect to Google Sheets with proper error handling"""
    try:
        # Use Google's official auth library
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly"
        ]
        
        credentials_dict = get_credentials_dict()
        
        # Use google.oauth2.service_account instead of oauth2client
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict, scopes=scope
        )
        
        client = gspread.authorize(credentials)
        
        # Test connection with a simple call
        try:
            client.list_spreadsheet_files()
        except Exception as test_error:
            st.error(f"Connection test failed: {str(test_error)}")
            return None
        
        return client
        
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {str(e)}")
        st.error("Check your service account key format and permissions.")
        
        # Debug info (remove in production)
        if st.checkbox("Show debug info"):
            st.json({
                "project_id": Config.PROJECT_ID,
                "client_email": Config.Credentials.CLIENT_EMAIL,
                "private_key_preview": Config.Credentials.PRIVATE_KEY[:50] + "..."
            })
        
        return None

def list_spreadsheets(client):
    """List available spreadsheets with error handling"""
    if not client:
        return []
    
    try:
        sheets = client.list_spreadsheet_files()
        return [sheet["name"] for sheet in sheets]
    except Exception as e:
        st.error(f"Error listing spreadsheets: {str(e)}")
        return []

def list_worksheets(sheet):
    """List worksheets in a spreadsheet"""
    try:
        return [ws.title for ws in sheet.worksheets()]
    except Exception as e:
        st.error(f"Error listing worksheets: {str(e)}")
        return []

def save_analyzed_entries_to_sheets(worksheet, entries):
    """Save analyzed entries to Google Sheets with enhanced data"""
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
            "Extracted Date",
        ]

        existing = worksheet.get_all_values()
        if not existing or existing[0] != headers:
            worksheet.clear()
            worksheet.append_row(headers)

        existing_links = set(row[2] for row in existing[1:] if len(row) > 2)

        new_rows = []
        current_date = datetime.utcnow().strftime("%Y-%m-%d")

        for entry in entries:
            if entry["link"] not in existing_links and entry.get("analyzed", False):
                analysis = entry.get("analysis_data", {})
                new_row = [
                    entry["title"],
                    analysis.get("feed_title", ""),
                    entry["link"],
                    entry["published_date"],
                    analysis.get("description", ""),
                    analysis.get("core_message", ""),
                    analysis.get("key_tags", ""),
                    analysis.get("sector", ""),
                    entry["source"],
                    current_date,
                ]
                new_rows.append(new_row)

        if new_rows:
            worksheet.append_rows(new_rows)
            return len(new_rows)

        return 0

    except Exception as e:
        st.error(f"Error saving to sheets: {str(e)}")
        return 0