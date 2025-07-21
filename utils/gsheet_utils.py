import gspread
import streamlit as st
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
from config import Config

CREDENTIALS_JSON = {
    "type": "service_account",
    "client_id": Config.Credentials.CLIENT_ID,
    "client_email": Config.Credentials.CLIENT_EMAIL,
    "private_key": Config.Credentials.PRIVATE_KEY,
    "private_key_id": Config.Credentials.PRIVATE_KEY_ID,
    "token_uri": Config.Credentials.TOKEN_URI,
    "project_id": Config.PROJECT_ID,
}

def connect_gspread_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDENTIALS_JSON, scope)
    print("Connecting to Google Sheets with credentials:", creds)
    client = gspread.authorize(creds)
    print("############",client)
    return client

def list_spreadsheets(client):
    sheets = client.list_spreadsheet_files()
    return [sheet["name"] for sheet in sheets]

def list_worksheets(sheet):
    return [ws.title for ws in sheet.worksheets()]

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