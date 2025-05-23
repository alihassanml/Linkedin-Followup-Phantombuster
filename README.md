# 🤖 LinkedIn Follow-Up Automation using PhantomBuster + Google Sheets

This project automates sending follow-up messages on LinkedIn using [PhantomBuster's LinkedIn Message Sender](https://phantombuster.com/phantoms/automation/linkedin-message-sender), driven by a Google Sheet populated with responses and LinkedIn profile URLs.

> 🔧 Built by [Ali Hassan](https://github.com/alihassanml) —  Data Science | Automating outreach at scale

---

## 🚀 Features

- ✅ Auto-send follow-up messages on LinkedIn
- ✅ Dynamically read message content from a Google Sheet
- ✅ Skip rows already processed
- ✅ Filter replies to ensure only last-message-from-recipient are followed up
- ✅ Local Python script to push messages from Excel to Google Sheets

---

## 🗂️ Project Structure

```bash
.
├── data/
│   ├── linkedIn_responses_groq.xlsx         # Excel file with outbound messages
│   └── n8nproje-459415-290a813ce38b.json    # Google Service Account credentials
├── sheet_update.py                          # Python script to update Google Sheet from Excel
└── README.md                                # This file
````

---

## 📋 Google Sheet Format

You must structure your Google Sheet like this:

| FullName | Response     | OriginalMessage    | threadurl                                                       |
| -------- | ------------ | ------------------ | --------------------------------------------------------------- |
| Noman    | Hey Noman... | Can you tell me... | [https://www.linkedin.com/in/](https://www.linkedin.com/in/)... |

* `Response`: the message you want to send
* `threadurl`: recipient's LinkedIn profile or conversation thread

---

## 🧠 How It Works

1. `sheet_update.py` reads the local Excel and pushes it to the target Google Sheet.
2. PhantomBuster's **LinkedIn Message Sender** Phantom is configured with:

   * `spreadsheetUrl`: your Google Sheet URL
   * `messageColumnName`: `Response`
   * `profileColumnName`: `threadurl`
   * `onlyIfLastMessageFromRecipient`: `true`
   * `customMessageModel`: leave empty or use `##Response#`
3. Phantom runs and sends each message automatically, skipping processed rows.

---

## 📦 Requirements

### Python

Install dependencies:

```bash
pip install pandas gspread oauth2client openpyxl
```

### Google API

1. Create a Service Account in Google Cloud
2. Share your Google Sheet with the service account email
3. Place the credentials JSON file at `data/n8nproje-459415-290a813ce38b.json`

---

## ⚙️ Running the Sheet Update Script

```bash
python sheet_update.py
```

This will:

* Clear the Google Sheet
* Upload data from `linkedIn_responses_groq.xlsx`

---

## 🔍 PhantomBuster Setup

In PhantomBuster:

* Phantom: `LinkedIn Message Sender`
* Session Cookie: get it from your LinkedIn browser session
* Launch settings:

  ```json
  {
    "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID",
    "messageColumnName": "Response",
    "profileColumnName": "threadurl",
    "onlyIfLastMessageFromRecipient": true,
    "sendConnectionRequests": false,
    "customMessageModel": "",
    "numberOfLinesPerLaunch": 10,
    "sessionCookie": "YOUR_SESSION_COOKIE"
  }
  ```

---

## 🧪 Debugging Tips

* ❗ Make sure the sheet is public to the service account or shared with it.
* ✅ Ensure `Response` and `threadurl` have **no empty rows**
* 🧼 To "reset" processed rows, duplicate the sheet or use a new tab

---

## 📌 Todo

* [ ] Add email fallback for bounced LinkedIn messages
* [ ] Store message history for audit
* [ ] Create a web frontend with Streamlit

---

## 📎 License

MIT — use it freely, no liability.

---

## ✨ Author

**Ali Hassan**
*Data Science Enthusiast | LinkedIn Automation Architect*

GitHub: [alihassanml](https://github.com/alihassanml)
LinkedIn: [Ali Hassan](https://www.linkedin.com/in/alihassanml/)

---

## 🤔 Want to contribute?

Open an issue or submit a PR. Ideas and improvements are welcome!
