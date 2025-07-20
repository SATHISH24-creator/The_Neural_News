import gspread
import streamlit as st
from datetime import datetime
from google.oauth2.service_account import ServiceAccountCredentials

from config import Config

def get_credentials_dict():
    """Create credentials dictionary with proper format"""
    return {
        "type": "service_account",
        "project_id": Config.PROJECT_ID,
        "private_key_id": Config.Credentials.PRIVATE_KEY_ID,
        "private_key": Config.Credentials.PRIVATE_KEY.replace('\\n', '\n'),  # Fix newlines
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
        # Updated scope - more specific and current
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly"
        ]
        
        credentials_dict = get_credentials_dict()
        creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        client = gspread.authorize(creds)
        
        # Test connection
        client.list_spreadsheet_files()
        
        return client
        
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {str(e)}")
        st.error("Please check your service account credentials and permissions.")
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