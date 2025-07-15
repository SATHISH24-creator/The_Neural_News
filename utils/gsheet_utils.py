import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
from datetime import datetime

# Set your Google Sheets API credentials json path
CREDENTIALS_FILE = r"C:\Users\sathi\Desktop\ai-rss-feed-analyzer\credentials.json"

def connect_gspread_client():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    return client

def list_spreadsheets(client):
    sheets = client.list_spreadsheet_files()
    return [sheet['name'] for sheet in sheets]

def list_worksheets(sheet):
    return [ws.title for ws in sheet.worksheets()]

def save_analyzed_entries_to_sheets(worksheet, entries):
    """Save analyzed entries to Google Sheets with enhanced data"""
    try:
        headers = [
            "Original Title", "Enhanced Title", "Link", "Original Published Date",
            "Description", "Core Message", "Key Tags", "Sector", "Source", "Extracted Date"
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
                    current_date
                ]

                new_rows.append(new_row)

        if new_rows:
            worksheet.append_rows(new_rows)
            return len(new_rows)

        return 0

    except Exception as e:
        st.error(f"Error saving to sheets: {str(e)}")
        return 0