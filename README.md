# 🗂️ Google Drive Agent

A conversational AI agent that searches, filters, and discovers files in Google Drive through natural language chat.

---

## 🏗️ Architecture

```
User ──► Streamlit UI ──► FastAPI Backend ──► LangGraph Agent
                                                    │
                                                    ▼
                                           DriveSearchTool
                                                    │
                                                    ▼
                                         Google Drive API
```

**Stack:**
- **Backend:** Python · FastAPI · LangGraph · LangChain
- **LLM:** Groq (default) or Google Gemini 1.5 Flash (optional fallback)
- **Frontend:** Streamlit
- **Drive Integration:** Google Drive API v3 · Service Account

---

## ⚙️ Local Setup (Step-by-Step)

### Step 1 — Clone / Open the project

```bash
# If you have the folder already, just open it in VS Code
code tailortalk-drive-agent
```

---

### Step 2 — Get a Groq API Key (Recommended)

1. Go to → https://console.groq.com/keys
2. Click **"Create API Key"**
3. Copy the key — you'll paste it in `.env` shortly

Optional: If you want Gemini as a fallback, also create a Gemini API key at
https://aistudio.google.com/app/apikey

---

### Step 3 — Set up Google Cloud Service Account

This lets the agent read your Google Drive without any browser login.

1. **Go to** → https://console.cloud.google.com/
2. **Create a new project** (or select existing) → name it `TailorTalk`
3. **Enable the Drive API:**
   - In the search bar type: `Google Drive API`
   - Click it → click **"Enable"**
4. **Create a Service Account:**
   - Go to: `IAM & Admin` → `Service Accounts`
   - Click **"+ Create Service Account"**
   - Name: `tailortalk-drive-agent`
   - Click **"Create and Continue"** → skip role → click **"Done"**
5. **Download the JSON key:**
   - Click on the service account you just created
   - Go to **"Keys"** tab → **"Add Key"** → **"Create new key"** → **JSON**
   - A `.json` file will download automatically
6. **Move the key file:**
   ```bash
   mv ~/Downloads/your-key-file.json tailortalk-drive-agent/credentials/service_account.json
   ```

---

### Step 4 — Share your Google Drive folder with the Service Account

1. Open the downloaded `.json` file — find the `"client_email"` field.
   It looks like: `tailortalk-drive-agent@your-project.iam.gserviceaccount.com`
2. **Copy that email address**
3. Go to the sample Google Drive folder:
   → https://drive.google.com/drive/folders/1qkx58doSeYrcLjHPDysJyVJ36PsSqqlt
4. Click **"Add shortcut to Drive"** or open it
5. Make a **copy** of the folder to your own Drive
6. On your copied folder → right-click → **"Share"**
7. Paste the service account email → set permission to **"Viewer"** → click **"Share"**
8. **Copy the folder ID** from the URL:
   `https://drive.google.com/drive/folders/`**`THIS_IS_THE_FOLDER_ID`**

---

### Step 5 — Configure Environment Variables

Edit `backend/.env`:

```env
GROQ_API_KEY=paste_your_groq_key_here
GROQ_MODEL=llama-3.1-8b-instant
GEMINI_API_KEY=paste_your_gemini_key_here  # optional fallback
GOOGLE_SERVICE_ACCOUNT_FILE=../credentials/service_account.json
DRIVE_FOLDER_ID=paste_your_folder_id_here
```

---

### Step 6 — Install Backend Dependencies

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

---

### Step 7 — Run the Backend

```bash
# Make sure you're in the backend/ folder with venv activated
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Test it: open http://localhost:8000/health → should return `{"status":"ok"}`

---

### Step 8 — Install Frontend Dependencies

Open a **new terminal** (keep backend running):

```bash
cd frontend

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

---

### Step 9 — Run the Frontend

```bash
# Make sure you're in the frontend/ folder
streamlit run app.py
```

Streamlit will open automatically at → http://localhost:8501

---

## 🧪 Test Queries to Try

| What you type | What it searches |
|---|---|
| `Show me all PDFs` | All PDF files |
| `Find files named report` | Files with "report" in name |
| `List all Google Sheets` | Spreadsheet files |
| `Find images` | PNG and JPEG files |
| `Search for files about marketing` | Full-text content search |
| `Show files modified this month` | Recent files |
| `Find presentations` | Google Slides files |

---

## 📁 Project Structure

```
tailortalk-drive-agent/
├── backend/
│   ├── main.py           # FastAPI app & routes
│   ├── agent.py          # LangGraph agent + DriveSearchTool
│   ├── drive_service.py  # Google Drive API wrapper
│   ├── requirements.txt
│   └── .env              # ← your secrets go here
├── frontend/
│   ├── app.py            # Streamlit chat UI
│   └── requirements.txt
├── credentials/
│   └── service_account.json  # ← your downloaded key goes here
├── .gitignore
└── README.md
```

---

## 🚀 Deployment (Render / Railway)

### Backend on Render:
1. Push code to GitHub (make sure `.env` and `credentials/` are in `.gitignore`)
2. Go to render.com → New → Web Service
3. Connect your repo, set root directory to `backend/`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables in Render dashboard
7. Add your service account JSON as a secret file

### Frontend on Streamlit Cloud:
1. Push `frontend/` to GitHub
2. Go to share.streamlit.io
3. Connect repo, set `app.py` as main file
4. Set `BACKEND_URL` to your Render URL in secrets

---

## ❓ Troubleshooting

| Problem | Fix |
|---|---|
| `Backend Offline` in sidebar | Make sure `uvicorn main:app --reload` is running |
| `Google Drive API error` | Check service account has access to the folder |
| `Invalid API key` | Double-check `GEMINI_API_KEY` in `.env` |
| `No files found` | Verify folder ID and that folder is shared with service account |
| `ModuleNotFoundError` | Make sure venv is activated and `pip install -r requirements.txt` ran |
