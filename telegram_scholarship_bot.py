import asyncio
import time
import re
import os
from telethon import TelegramClient
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Your Telegram API credentials
API_ID = 24112914  # Replace with your correct API ID
API_HASH = "ffd7e2bb8bcdf17468a20ae641cfa508"  # Replace with your correct API Hash
CHANNEL_USERNAME = "fullyfundedscholarshipsorg"  # Replace with your target channel

# Initialize Telegram Client
client = TelegramClient("anon", API_ID, API_HASH)

# Google Sheets setup
GOOGLE_SHEETS_CREDENTIALS = "/content/scholarship-449518-4eb0e3383b72.json"  # Ensure this file is uploaded
GOOGLE_SHEETS_NAME = "Scholarship Data"  # Name of your Google Sheet

# Authenticate Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
client_gsheets = gspread.authorize(creds)

# Open the Google Sheet
sheet = client_gsheets.open(GOOGLE_SHEETS_NAME).sheet1

# Function to extract structured data from a message
def extract_scholarship_details(message):
    """Extracts scholarship details from a structured message format."""
    
    # Improved regex to better capture scholarship details
    name_match = re.search(r'^(.*Scholarship.*\d{4})', message, re.MULTILINE)
    apply_link_match = re.search(r'Apply here:\s*(https?://\S+)', message)
    university_match = re.search(r'Host University:\s*(.+)', message)
    countries_match = re.search(r'Host Countries:\s*(.+)', message)
    applicants_match = re.search(r'Who can apply:\s*(.+)', message)
    deadline_match = re.search(r'Deadline:\s*(.+)', message)

    # Extract values or use "N/A" if not found
    scholarship_name = name_match.group(1) if name_match else "N/A"
    apply_link = apply_link_match.group(1) if apply_link_match else "N/A"
    university = university_match.group(1) if university_match else "N/A"
    countries = countries_match.group(1) if countries_match else "N/A"
    applicants = applicants_match.group(1) if applicants_match else "N/A"
    deadline = deadline_match.group(1) if deadline_match else "N/A"

    return [scholarship_name, university, countries, applicants, deadline, apply_link]

# Function to check if the message already exists
def is_duplicate(scholarship_name):
    """Checks if the scholarship name already exists in Google Sheets."""
    all_values = sheet.col_values(1)  # Fetch all values from the first column
    return scholarship_name in all_values  # Returns True if message exists, False otherwise

# Function to upload organized data to Google Sheets (only if not duplicate)
def upload_to_google_sheets(message):
    """Uploads structured scholarship data to Google Sheets if it's not already stored."""
    scholarship_data = extract_scholarship_details(message)

    # Prevent duplicate entries
    if not is_duplicate(scholarship_data[0]):  # Check using Scholarship Name
        try:
            sheet.append_row(scholarship_data)  # Append new row
            print("✅ New scholarship data uploaded to Google Sheets in an organized way!")
        except Exception as e:
            print(f"❌ Error uploading to Google Sheets: {e}")
    else:
        print("⚠️ Duplicate scholarship detected. Skipping upload.")

# Function to fetch the latest message from Telegram
async def get_latest_message():
    """Fetches the latest message from the specified Telegram channel."""
    async with TelegramClient("anon", API_ID, API_HASH) as client:
        messages = await client.get_messages(CHANNEL_USERNAME, limit=1)
        if messages:
            return messages[0].text
    return None

# Function to check for new messages every 5 minutes
def auto_run():
    """Continuously checks for new messages and uploads if new."""
    while True:
        print("🔍 Checking for new messages...")
        message = asyncio.run(get_latest_message())
        
        if message:
            print(f"📩 Latest message: {message}")
            upload_to_google_sheets(message)
        else:
            print("❌ No new messages found.")

        print("⏳ Waiting for the next check (5 min)...")
        time.sleep(300)  # Wait 5 minutes before checking again

# Start auto-run process
auto_run()
