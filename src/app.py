import os
import re
import json
import csv
import requests
import time
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
load_dotenv()

Phantom_Buster = os.getenv('PHANTOM_BUSTER')
Session_Cookies = os.getenv('SESSION_COOKIES')
User_Agent = os.getenv('USER_AGENT')
groq_api_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    api_key=groq_api_key,
    model_name="llama-3.3-70b-versatile",  
    temperature=0.3
)


def fetch_message():
    date = datetime.now().strftime("%m-%d-%Y")
    url = "https://api.phantombuster.com/api/v2/agents/launch"
    headers = {
        "Content-Type": "application/json",
        "X-Phantombuster-Key-1": Phantom_Buster
    }
    payload = {
        "id": "5519115784887786",
        "argument": {
            "sessionCookie": Session_Cookies,
            "userAgent": User_Agent,
            "inboxFilter": "all",
            "before": date,
            "numberOfThreadsToScrape": 30
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    return response.json().get("containerId")


def fetch_output(container_id):
    url = f"https://api.phantombuster.com/api/v2/containers/fetch-output?id={container_id}"
    headers = {
        "X-Phantombuster-Key": Phantom_Buster
    }

    for attempt in range(10):
        time.sleep(5)
        response = requests.get(url, headers=headers)
        data = response.json()
        print(data)
        if "output" in data:
            output_text = data["output"]
            print("✅ Output received!")
            json_links = re.findall(r'https://[^ ]+?result\.json', output_text)
            csv_links = re.findall(r'https://[^\s]+?result\.csv', output_text)
            if json_links or csv_links:
                if json_links:
                    pass
                if csv_links:
                    pass
                return {
                    "json_url": json_links[0] if json_links else None,
                    "csv_url": csv_links[0] if csv_links else None
                }

            print("⚠️ Output received but no JSON URL found.")
            return output_text
        
        print(f"🔁 Attempt {attempt + 1} | Output not ready.")
    print("⏳ Timeout: Output not ready after 10 attempts.")
    return None


def download_file(url, save_folder, filename=None):
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    if filename is None:
        filename = url.split("/")[-1]

    filepath = os.path.join(save_folder, filename)
    response = requests.get(url)
    with open(filepath, "wb") as f:
        f.write(response.content)
    print(f"📁 File saved to: {filepath}")





def transform_and_save_json_to_csv(json_path, csv_path):
    with open(json_path, "r", encoding="utf-8") as f:
        items = json.load(f)
    transformed = []
    for item in items:
        # Flatten linkedInUrls
        item["linkedInUrls"] = "; ".join(item.get("linkedInUrls", []))
        # Add FullName
        firstname = item.get("firstnameFrom", "")
        lastname = item.get("lastnameFrom", "")
        item["FullName"] = f"{firstname} {lastname}".strip()
        transformed.append(item)

    if transformed:
        # Get all unique keys from all dictionaries to ensure complete CSV
        all_keys = set()
        for row in transformed:
            all_keys.update(row.keys())
        all_keys = sorted(all_keys)

        # Save to CSV
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_keys)
            writer.writeheader()
            writer.writerows(transformed)

        print(f"✅ Transformed CSV saved at: {csv_path}")
    else:
        print("⚠️ No data found to write to CSV.")




def download_google_sheet(sheet_id, dest_folder, filename="sheet.xlsx"):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    response = requests.get(url)

    if response.status_code == 200:
        filepath = f"{dest_folder}/{filename}"
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"✅ Google Sheet downloaded as Excel to: {filepath}")
        return filepath
    else:
        print(f"❌ Failed to download sheet. Status: {response.status_code}")
        return None


def compare_file():
    df1 = pd.read_csv("../data/linkedin_threads_transformed.csv")                     
    df2 = pd.read_excel("../data/linkedin_google_sheet.xlsx")   # From Google Sheet

    # Ensure 'FullName' exists and normalize for matching
    df1['FullName'] = df1['FullName'].str.strip().str.lower()
    df2['FullName'] = df2['FullName'].str.strip().str.lower()

    # Merge based on FullName and bring in 'message' column
    merged_df = df2.merge(df1[['FullName', 'message', 'readStatus', 'threadUrl']], on='FullName', how='left')

    # Save the updated second file
    merged_df.to_excel("../data/enriched_google_sheet.xlsx", index=False)

    print("✅ Merged data saved as 'enriched_google_sheet.xlsx'")



def linkedIn_fullName():
    df = pd.read_excel("../data/linkedin_google_sheet.xlsx") 
    df['FullName'] = df['first_name'].astype(str) + ' ' + df['last_name'].astype(str)
    df.to_excel('../data/linkedin_google_sheet.xlsx', index=False)
     



prompt = PromptTemplate(
    input_variables=["message", "fullname", "agency_info"],
    template="""
You’re just a normal human replying casually on LinkedIn.

Here is some info about agencies you can use in the reply:
{agency_info}

Message: "{message}"
From: {fullname}

How to reply:
- Sound like a real person talking to a friend.
- Be short (1–2 lines), warm, and natural.
- If they ask about agencies, use the agency info.
- Only say what fits the message.
- Match the person's tone:
  - If they say “hi”, reply like “Hey {fullname}, how’s it going?”
  - If they’re curious, give simple next steps + thread link.
  - If not interested, say “All good, no worries!”
  - If unclear, ask a chill, friendly question.

No robotic language. No formal lines. Be real.
"""
)



def load_agency_data(file_path="../data/agency_data.txt"):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()



# Response function
def respond_to_messages(csv_path):
    agency_info = load_agency_data()
    chain = LLMChain(llm=llm, prompt=prompt)
    df = pd.read_excel(csv_path)

    responses = []
    for _, row in df.iterrows():
        message = row.get("message", "")
        fullname = row.get("FullName", "User")
        threadurl = row.get("linkedin_url", "#")

        if pd.isna(message): continue

        result = chain.run(message=message, fullname=fullname,agency_info=agency_info)
        responses.append({
            "FullName": fullname,
            "Response": result,
            "OriginalMessage": message,
            "threadurl":threadurl
        })

    df_response = pd.DataFrame(responses)
    df_response.to_excel("../data/linkedIn_responses_groq.xlsx", index=False)
    print("✅ Groq responses saved in 'linkedIn_responses_groq.xlsx'")


def sheet_update():
    import pandas as pd
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    # --- Config ---
    XLSX_PATH = "../data/linkedIn_responses_groq.xlsx"
    GOOGLE_SHEET_ID = "1tCr_Dz1Tb9Wwr3SFG2nggplGct1hk1PnxPYjCYKcTkc"
    TARGET_SHEET_NAME = "messageback"
    CREDENTIALS_FILE = "../data/n8nproje-459415-290a813ce38b.json"

    # --- Auth ---
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    gc = gspread.authorize(credentials)

    # --- Open the spreadsheet ---
    sh = gc.open_by_key(GOOGLE_SHEET_ID)

    # --- Try to get the worksheet by name ---
    try:
        worksheet = sh.worksheet(TARGET_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        print(f"⚠️ Sheet '{TARGET_SHEET_NAME}' not found. Creating it.")
        worksheet = sh.add_worksheet(title=TARGET_SHEET_NAME, rows="1000", cols="20")

    # --- Clear old content ---
    worksheet.clear()

    # --- Load and clean Excel data ---
    df = pd.read_excel(XLSX_PATH)

    # Ensure all required columns exist
    required_columns = ["Response", "threadurl"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"❌ Required column '{col}' is missing from the Excel file.")

    # Drop fully empty rows
    df = df.dropna(subset=["Response", "threadurl"])

    # Convert all to string and strip spaces
    df = df.fillna("").astype(str)
    df = df.applymap(lambda x: x.strip())

    # --- Set headers first ---
    worksheet.append_row(df.columns.tolist(), value_input_option="USER_ENTERED")

    # --- Write all rows ---
    rows = df.values.tolist()
    for row in rows:
        worksheet.append_row(row, value_input_option="USER_ENTERED")

    print(f"✅ Sheet cleared and updated: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/edit#gid={worksheet.id}")




def send_messages_from_sheet():
    sheet_url = 'https://docs.google.com/spreadsheets/d/1tCr_Dz1Tb9Wwr3SFG2nggplGct1hk1PnxPYjCYKcTkc'
    PHANTOM_ID = "2141574223274199"
    
    endpoint = "https://api.phantombuster.com/api/v2/agents/launch"
    headers = {
        "Content-Type": "application/json",
        "X-Phantombuster-Key-1": Phantom_Buster  # Make sure this is defined
    }

    argument_payload = {
    "spreadsheetUrl": sheet_url,
    "profileColumnName": "threadurl",        # ✅ must match column header exactly
    "messageColumnName": "Response",         # ✅ must match column header exactly
    "sessionCookie": Session_Cookies
    }


    payload = {
        "id": PHANTOM_ID,
        "argument": json.dumps(argument_payload)
    }

    response = requests.post(endpoint, json=payload, headers=headers)
    
    print("🔗 Launching Phantom:", response.status_code)
    try:
        print("📦 Response:", json.dumps(response.json(), indent=2))
    except Exception as e:
        print("⚠️ Failed to decode response JSON:", response.text)




   


def main():
    container_id = fetch_message()
    time.sleep(20)
    if container_id:
        result = fetch_output(container_id)
        if result:
            csv_url = result.get("csv_url")
            json_url = result.get("json_url")

            print("✅ JSON:", json_url)
            print("✅ CSV:", csv_url)

            if json_url:
                json_file_path = "../data/linkedin_threads.json"
                csv_output_path = "../data/linkedin_threads_transformed.csv"
                download_file(json_url, "../data", "linkedin_threads.json")
                transform_and_save_json_to_csv(json_file_path, csv_output_path)
                sheet_id = "1tglmSFFT05M3Xb9DIShBFGFUPotz3r7epSFwatY5pew"
                download_google_sheet(sheet_id, "../data", "linkedin_google_sheet.xlsx")
                linkedIn_fullName()
                compare_file()
                respond_to_messages('../data/enriched_google_sheet.xlsx')
                sheet_update()
                send_messages_from_sheet()

    else:
        print("Failed to launch agent.")


if __name__ == '__main__':
    main()
