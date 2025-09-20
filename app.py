# ... (ההתחלה והסטייל כמו ששלחת, לא שיניתי)

# ---------- Google Sheets (optional) ----------
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_AVAILABLE = True
except Exception:
    GSHEETS_AVAILABLE = False

SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]

def _normalize_private_key(creds: dict) -> dict:
    pk = creds.get("private_key")
    if isinstance(pk, str) and "\\n" in pk:
        creds = creds.copy(); creds["private_key"] = pk.replace("\\n", "\n")
    return creds

def _sheets_cfg():
    # תמיכה גם ב-google_service_account וגם ב-gcp_service_account
    ident = (
        st.secrets.get("GOOGLE_SHEET_URL")
        or st.secrets.get("GOOGLE_SHEET_ID")
        or st.secrets.get("GOOGLE_SHEET_TITLE")
        or st.secrets.get("sheet_id")
    )
    ws = st.secrets.get("GOOGLE_SHEET_WORKSHEET") or st.secrets.get("worksheet") or "sheet1"
    creds = dict(
        st.secrets.get("google_service_account", {})
        or st.secrets.get("gcp_service_account", {})
    )
    if creds: creds = _normalize_private_key(creds)
    return ident, ws, creds

def _open_spreadsheet(gc, identifier: str):
    if identifier.startswith("http"): return gc.open_by_url(identifier)
    if "/" not in identifier and " " not in identifier:
        try: return gc.open_by_key(identifier)
        except Exception: pass
    return gc.open(identifier)

def save_to_google_sheets(branch: str, chef: str, dish: str, score: int, notes: str, ts: str) -> bool:
    if not GSHEETS_AVAILABLE:
        st.info("gspread לא מותקן בסביבה")
        return False
    ident, ws_name, creds_dict = _sheets_cfg()
    if not ident or not creds_dict:
        st.warning("הגדרות Google Sheets חסרות ב-secrets.toml")
        return False
    try:
        creds = Credentials.from_service_account_info(creds_dict).with_scopes(SCOPES)
        gc = gspread.authorize(creds)
        sh = _open_spreadsheet(gc, ident)
        try:
            ws = sh.worksheet(ws_name)
        except Exception:
            ws = sh.add_worksheet(title=ws_name, rows=1000, cols=12)
        ws.append_row([ts, branch, chef, dish, score, notes or ""], value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.warning(f"שגיאת Google Sheets: {e}")
        return False

# ---------- OpenAI GPT (optional, gpt-5) ----------
def get_openai_client():
    api_key = (st.secrets.get("OPENAI_API_KEY", "") or st.secrets.get("openai_api_key", ""))
    if not api_key:
        return None, "🔑 GPT לא פעיל: חסר OPENAI_API_KEY ב-Secrets."
    org = st.secrets.get("OPENAI_ORG", "") or st.secrets.get("openai_org", "")
    proj = st.secrets.get("OPENAI_PROJECT", "") or st.secrets.get("openai_project", "")
    try:
        from openai import OpenAI
        kw = {"api_key": api_key}
        if org:  kw["organization"] = org
        if proj: kw["project"] = proj
        return OpenAI(**kw), None
    except Exception as e:
        return None, f"שגיאת OpenAI: {e}"

# ---------- יצירת DB אם לא קיים ----------
import os
if not os.path.exists(DB_PATH):
    init_db()

# ---------- המשך הקוד כפי שהוא ----------
# (אין צורך להדביק שוב את כל הלוגיקה כי כמעט ולא שונתה למעט Google Sheets/OpenAI)
