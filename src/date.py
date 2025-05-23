import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests

# CONFIG
PHANTOM_ID = "7304922881433312"
PHANTOMBUSTER_API_KEY = "your_phantombuster_key"
SERVICE_ACCOUNT_FILE = "your_google_service_account.json"
SHEET_NAME = "LinkedIn Message Auto"

PROFILE_MESSAGE_LIST = [
    {
        "ProfileUrl": "https://www.linkedin.com/in/noman-ishfaq-5750b4238/",
        "ResponseMessage": "Hi Noman, how can I help you today?"
    },
    {
        "ProfileUrl": "https://www.linkedin.com/in/other-person/",
        "ResponseMessage": "Hello! I saw your profile and wanted to connect."
    }
]

def upload_to_google_sheet(data):
    df = pd.DataFrame(data)
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)
    sheet = client.create(SHEET_NAME)
    sheet.share(None, perm_type='anyone', role='writer')  # Make sheet public (Phantom can access)
    worksheet = sheet.sheet1
    worksheet.update([df.columns.tolist()] + df.values.tolist())
    print("✅ Google Sheet created and shared")
    sheet_url = sheet.url
    return sheet_url

def launch_phantom(sheet_url):
    csv_url = sheet_url.replace("/edit", "/export?format=csv")
    url = "https://api.phantombuster.com/api/v2/agents/launch"
    payload = {
        "id": PHANTOM_ID,
        "output": "first-result-object",
        "arguments": {
            "spreadsheetUrl": csv_url,
            "messageColumnName": "ResponseMessage",
            "profileUrlColumnName": "ProfileUrl",
            "sendMessageOnlyIfLastFromRecipient": True
        }
    }
    headers = {
        "X-Phantombuster-Key-1": PHANTOMBUSTER_API_KEY,
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.ok:
        print("✅ Phantom launched")
        print("Output:", response.json())
    else:
        print("❌ Phantom launch failed:", response.text)

def main():
    sheet_url = upload_to_google_sheet(PROFILE_MESSAGE_LIST)
    launch_phantom(sheet_url)

if __name__ == "__main__":
    main()
