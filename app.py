import streamlit as st
import json
import os
import hashlib
import uuid
import re
import time
from datetime import datetime
import anthropic

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CollabNotes",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = "notes_data.json"

# ─── THEME & STYLING ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Inter', sans-serif!important;
    box-sizing: border-box;
}

/* ── Base ── */
.stApp { background-color: #0b0d14; color: #dde1f0; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0f1120!important;
    border-right: 1px solid #1e2238!important;
}
[data-testid="stSidebar"].stMarkdown { color: #a0a8c8; }

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: #131628!important;
    color: #dde1f0!important;
    border: 1px solid #1e2238!important;
    border-radius: 8px!important;
    font-family: 'Inter', sans-serif!important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #5b6cf9!important;
    box-shadow: 0 0 0 2px rgba(91,108,249,0.15)!important;
}
input[type="password"] { font-family: 'Inter', sans-serif!important; }

/* ── Buttons ── */
.stButton > button {
    background: #5b6cf9!important;
    color: #fff!important;
    border: none!important;
    border-radius: 8px!important;
    font-weight: 600!important;
    font-size: 13px!important;
    transition: all 0.18s ease!important;
    padding: 0.45rem 1.1rem!important;
}
.stButton > button:hover {
    background: #4858e8!important;
    transform: translateY(-1px)!important;
    box-shadow: 0 4px 16px rgba(91,108,249,0.35)!important;
}
.stButton > button:active { transform: translateY(0)!important; }

/* ── Cards ── */
.note-card {
    background: #131628;
    border: 1px solid #1e2238;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 14px;
    transition: border-color 0.18s, box-shadow 0.18s;
}
.note-card:hover {
    border-color: #5b6cf9;
    box-shadow: 0 4px 24px rgba(91,108,249,0.12);
}
.note-title {
    font-size: 15px; font-weight: 700; color: #dde1f0;
    margin-bottom: 7px; line-height: 1.3;
}
.note-preview {
    font-size: 13px; color: #6b7299; line-height: 1.6;
}
.note-meta {
    font-size: 11px; color: #3d4468; margin-top: 10px;
    display: flex; align-items: center; gap: 8px;
}

/* ── Tags ── */
.tag {
    display: inline-block;
    background: rgba(91,108,249,0.12);
    color: #7c8fff;
    padding: 2px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 600; margin: 2px;
    letter-spacing: 0.01em;
}

/* ── AI result ── */
.ai-result {
    background: linear-gradient(135deg, #131628 0%, #111425 100%);
    border: 1px solid #252a45;
    border-left: 3px solid #5b6cf9;
    border-radius: 10px;
    padding: 14px 16px;
    margin-top: 10px;
    font-size: 13.5px; line-height: 1.75; color: #c8ceea;
    white-space: pre-wrap;
}

/* ── Version items ── */
.version-item {
    background: #131628;
    border: 1px solid #1e2238;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 8px;
    font-size: 13px;
}

/* ── Collab presence ── */
.presence-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #22c55e;
    margin-right: 6px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* ── Hero ── */
.hero {
    text-align: center;
    padding: 56px 20px 36px;
}
.hero-logo {
    font-size: 52px;
    margin-bottom: 4px;
    line-height: 1;
}
.hero h1 {
    font-size: 38px; font-weight: 800; color: #edf0ff;
    margin: 8px 0 0;
    letter-spacing: -0.03em;
}
.hero-sub {
    font-size: 16px; color: #515880;
    margin-top: 10px; font-weight: 400;
}

/* ── Feature pills ── */
.feature-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: #131628; border: 1px solid #1e2238;
    border-radius: 100px; padding: 6px 14px;
    font-size: 12px; font-weight: 500; color: #6b7299;
    margin: 4px;
}

/* ── Section headers ── */
.section-header {
    font-size: 11px; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: #3d4468; margin-bottom: 10px;
}

/* ── Permission badge ── */
.badge-owner { color: #f59e0b; font-size:11px; font-weight:700; }
.badge-write { color: #22c55e; font-size:11px; font-weight:700; }
.badge-read { color: #6b7299; font-size:11px; font-weight:700; }
.badge-shared { color: #5b6cf9; font-size:11px; font-weight:700; }

/* ── Editor title input override ── */
.big-title input {
    font-size: 28px!important;
    font-weight: 800!important;
    background: transparent!important;
    border: none!important;
    border-bottom: 2px solid #1e2238!important;
    border-radius: 0!important;
    color: #edf0ff!important;
    padding-left: 0!important;
    letter-spacing: -0.02em!important;
}

/* ── Auth form ── */
.auth-card {
    background: #0f1120;
    border: 1px solid #1e2238;
    border-radius: 16px;
    padding: 28px;
}

/* ── Share token box ── */
.token-box {
    background: #131628;
    border: 1px solid #252a45;
    border-radius: 10px;
    padding: 12px 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 15px;
    color: #7c8fff;
    letter-spacing: 0.06em;
    text-align: center;
    margin: 8px 0;
    font-weight: 500;
}

/* ── Dividers ── */
hr { border-color: #1e2238!important; margin: 16px 0!important; }

/* ── Alerts ── */
.stAlert { border-radius: 10px!important; }
.stSuccess { background: rgba(34,197,94,0.08)!important; border-color: #22c55e!important; }
.stError { background: rgba(239,68,68,0.08)!important; border-color: #ef4444!important; }
.stWarning { background: rgba(245,158,11,0.08)!important; border-color: #f59e0b!important; }
.stInfo { background: rgba(91,108,249,0.08)!important; border-color: #5b6cf9!important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #0f1120!important;
    border-radius: 8px!important;
    color: #a0a8c8!important;
    font-weight: 600!important;
}

/* ── Radio ── */
.stRadio > div { gap: 0px!important; }
.stRadio label { color: #a0a8c8!important; font-size: 13px!important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0b0d14; }
::-webkit-scrollbar-thumb { background: #252a45; border-radius: 10px; }

/* ── Toast ── */
.stToast { border-radius: 10px!important; }

/* ── Checkbox ── */
.stCheckbox label { color: #a0a8c8!important; font-size: 13px!important; }

/* ── Progress bar ── */
.stProgress > div > div > div { background: #5b6cf9!important; }

/* Responsive columns gap */
[data-testid="column"] { padding: 0 6px!important; }
</style>
""", unsafe_allow_html=True)

# ─── DATA LAYER ───────────────────────────────────────────────────────────────

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "notes": {}, "presence": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def time_ago(dt_str):
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        diff = datetime.now() - dt
        s = diff.total_seconds()
        if s < 60: return "just now"
        if s < 3600: return f"{int(s//60)}m ago"
        if s < 86400: return f"{int(s//3600)}h ago"
        return f"{int(s//86400)}d ago"
    except:
        return dt_str

# ─── AUTH ─────────────────────────────────────────────────────────────────────

def validate_email(email):
    return re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email) is not None

def register_user(name, email, password):
    if not validate_email(email):
        return False, "Invalid email format"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if not name.strip():
        return False, "Name is required"
    data = load_data()
    if email.lower() in data["users"]:
        return False, "That email is already registered"
    uid = str(uuid.uuid4())
    data["users"][email.lower()] = {
        "id": uid,
        "name": name.strip(),
        "email": email.lower(),
        "password": hash_password(password),
        "created_at": now(),
        "avatar_color": "#" + uid[:6],
    }
    save_data(data)
    return True, data["users"][email.lower()]

def login_user(email, password):
    data = load_data()
    user = data["users"].get(email.lower())
    if not user or user["password"]!= hash_password(password):
        return False, "Incorrect email or password"
    return True, user

def get_user_by_email(email):
    data = load_data()
    return data["users"].get(email.lower())

def get_user_initials(name):
    parts = name.strip().split()
    return (parts[0][0] + parts[-1][0]).upper() if len(parts) > 1 else parts[0][:2].upper()

# ─── PRESENCE (real-time simulation) ─────────────────────────────────────────

def update_presence(note_id, user_id, user_name):
    data = load_data()
    if "presence" not in data:
        data["presence"] = {}
    if note_id not in data["presence"]:
        data["presence"][note_id] = {}
    data["presence"][note_id][user_id] = {
        "name": user_name,
        "last_seen": now(),
    }
    save_data(data)

def get_presence(note_id):
    data = load_data()
    presence = data.get("presence", {}).get(note_id, {})
    active = []
    for uid, info in presence.items():
        try:
            dt = datetime.strptime(info["last_seen"], "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - dt).total_seconds() < 30:
                active.append(info["name"])
        except:
            pass
    return active

def clear_presence(note_id, user_id):
    data = load_data()
    if "presence" in data and note_id in data["presence"]:
        data["presence"][note_id].pop(user_id, None)
        save_data(data)

# ─── NOTES ────────────────────────────────────────────────────────────────────

def create_note(owner_id, owner_name, title="Untitled Note", content=""):
    data = load_data()
    note_id = str(uuid.uuid4())
    note = {
        "id": note_id,
        "title": title,
        "content": content,
        "owner_id": owner_id,
        "owner_name": owner_name,
        "collaborators": [],
        "tags": [],
        "share_token": None,
        "share_permission": "none",
        "created_at": now(),
        "updated_at": now(),
        "word_count": 0,
        "versions": [{
            "version": 1,
            "title": title,
            "content": content,
            "saved_by": owner_name,
            "saved_at": now(),
            "description": "Initial version",
        }],
    }
    data["notes"][note_id] = note
    save_data(data)
    return note

def get_user_notes(user_id, user_email):
    data = load_data()
    result = []
    for note in data["notes"].values():
        is_owner = note["owner_id"] == user_id
        is_collab = any(c["email"] == user_email.lower() for c in note.get("collaborators", []))
        if is_owner or is_collab:
            result.append(note)
    return sorted(result, key=lambda n: n["updated_at"], reverse=True)

def get_note(note_id):
    data = load_data()
    return data["notes"].get(note_id)

def update_note(note_id, title, content, save_version=False, saved_by="", description="Updated"):
    data = load_data()
    note = data["notes"].get(note_id)
    if not note:
        return None
    note["title"] = title
    note["content"] = content
    note["updated_at"] = now()
    note["word_count"] = len(content.split()) if content else 0
    if save_version:
        last_v = max((v["version"] for v in note["versions"]), default=0)
        note["versions"].append({
            "version": last_v + 1,
            "title": title,
            "content": content,
            "saved_by": saved_by,
            "saved_at": now(),
            "description": description,
        })
    save_data(data)
    return note

def delete_note(note_id):
    data = load_data()
    data["notes"].pop(note_id, None)
    if "presence" in data:
        data["presence"].pop(note_id, None)
    save_data(data)

def generate_share_token(note_id, permission):
    data = load_data()
    note = data["notes"].get(note_id)
    if not note:
        return None
    token = str(uuid.uuid4())[:8].upper()
    note["share_token"] = token
    note["share_permission"] = permission
    save_data(data)
    return token

def revoke_share_token(note_id):
    data = load_data()
    note = data["notes"].get(note_id)
    if note:
        note["share_token"] = None
        note["share_permission"] = "none"
        save_data(data)

def join_via_token(token, user_email, user_name, user_id):
    data = load_data()
    for note in data["notes"].values():
        if note.get("share_token") == token.upper().strip():
            is_owner = note["owner_id"] == user_id
            already = any(c["email"] == user_email.lower() for c in note["collaborators"])
            if not is_owner and not already:
                note["collaborators"].append({
                    "email": user_email.lower(),
                    "name": user_name,
                    "permission": note["share_permission"],
                    "joined_at": now(),
                })
                save_data(data)
            return note["id"], note["title"], True if is_owner or already else False
    return None, None, False

def invite_collaborator(note_id, invitee_email, permission, inviter_name):
    data = load_data()
    note = data["notes"].get(note_id)
    if not note:
        return False, "Note not found"
    invitee = data["users"].get(invitee_email.lower())
    if not invitee:
        return False, "No account found with that email"
    already = any(c["email"] == invitee_email.lower() for c in note["collaborators"])
    if already:
        return False, "Already a collaborator"
    if note["owner_id"] == invitee["id"]:
        return False, "That's the note owner"
    note["collaborators"].append({
        "email": invitee_email.lower(),
        "name": invitee["name"],
        "permission": permission,
        "joined_at": now(),
    })
    save_data(data)
    return True, invitee["name"]

def remove_collaborator(note_id, collab_email):
    data = load_data()
    note = data["notes"].get(note_id)
    if note:
        note["collaborators"] = [c for c in note["collaborators"] if c["email"]!= collab_email.lower()]
        save_data(data)

def update_collab_permission(note_id, collab_email, new_permission):
    data = load_data()
    note = data["notes"].get(note_id)
    if note:
        for c in note["collaborators"]:
            if c["email"] == collab_email.lower():
                c["permission"] = new_permission
        save_data(data)

def update_tags(note_id, tags):
    data = load_data()
    note = data["notes"].get(note_id)
    if note:
        existing = set(note.get("tags", []))
        existing.update(t.lower().strip() for t in tags if t.strip())
        note["tags"] = sorted(list(existing))
        save_data(data)

def set_tags(note_id, tags):
    data = load_data()
    note = data["notes"].get(note_id)
    if note:
        note["tags"] = sorted(list(set(t.lower().strip() for t in tags if t.strip())))
        save_data(data)

def restore_version(note_id, version_num, restored_by):
    data = load_data()
    note = data["notes"].get(note_id)
    if not note:
        return None
    version = next((v for v in note["versions"] if v["version"] == version_num), None)
    if not version:
        return None
    note["title"] = version["title"]
    note["content"] = version["content"]
    note["updated_at"] = now()
    note["word_count"] = len(version["content"].split()) if version["content"] else 0
    last_v = max(v["version"] for v in note["versions"])
    note["versions"].append({
        "version": last_v + 1,
        "title": version["title"],
        "content": version["content"],
        "saved_by": restored_by,
        "saved_at": now(),
        "description": f"Restored from v{version_num}",
    })
    save_data(data)
    return note

# ─── AI ───────────────────────────────────────────────────────────────────────

def get_ai_client():
    api_key = st.session_state.get("anthropic_key") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key.strip():
        return None
    try:
        return anthropic.Anthropic(api_key=api_key.strip())
    except Exception:
        return None

def ai_summarize(title, content):
    if not content.strip():
        return None, "Note is empty - add content first"

    client = get_ai_client()
    if not client:
        return None, "No API key configured. Add it in Dashboard → AI Settings"

    try:
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=600,
            temperature=0.3,
            messages=[{"role": "user", "content":
                f"Summarize this note in 4-6 concise, actionable bullet points. Start each bullet with •\n\nTitle: {title}\n\nContent:\n{content}"}]
        )
        return msg.content[0].text.strip(), None
    except anthropic.APIError as e:
        return None, f"Anthropic API error: {getattr(e, 'message', str(e))}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def ai_autotag(title, content):
    if not content.strip():
        return None, "Note is empty - add content first"

    client = get_ai_client()
    if not client:
        return None, "No API key configured"
    try:
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=150,
            temperature=0.2,
            messages=[{"role": "user", "content":
                f"Generate 4-7 relevant tags for this note. Return ONLY a JSON array of lowercase strings (1-3 words each), no markdown, no explanation.\n\nTitle: {title}\n\nContent:\n{content}"}]
        )
        raw = msg.content[0].text.replace("```json","").replace("```","").strip()
        tags = json.loads(raw)
        return [t.lower().strip() for t in tags if t.strip()], None
    except anthropic.APIError as e:
        return None, f"Anthropic API error: {getattr(e, 'message', str(e))}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def ai_ask(title, content, question):
    if not content.strip():
        return None, "Note is empty - add content first"
    if not question.strip():
        return None, "Type a question first"

    client = get_ai_client()
    if not client:
        return None, "No API key configured. Add it in Dashboard → AI Settings"

    try:
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=600,
            temperature=0.2,
            system="You answer questions about the user's note. Only use information present in the note. If the answer isn't in the note, say 'Not found in note' clearly. Be concise and direct.",
            messages=[{"role": "user", "content":
                f"Note Title: {title}\n\nNote Content:\n{content}\n\n---\nQuestion: {question}"}]
        )
        return msg.content[0].text.strip(), None
    except anthropic.APIError as e:
        return None, f"Anthropic API error: {getattr(e, 'message', str(e))}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def ai_improve(title, content, instruction):
    if not content.strip():
        return None, "Note is empty - add content first"
    if not instruction.strip():
        return None, "Add an instruction first"

    client = get_ai_client()
    if not client:
        return None, "No API key configured"
    try:
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.4,
            system="You are a writing assistant. When asked to improve/rewrite a note, return ONLY the improved note content (no title, no explanation, no preamble). Preserve the original intent and factual content.",
            messages=[{"role": "user", "content":
                f"Note Title: {title}\n\nNote Content:\n{content}\n\n---\nInstruction: {instruction}"}]
        )
        return msg.content[0].text.strip(), None
    except anthropic.APIError as e:
        return None, f"Anthropic API error: {getattr(e, 'message', str(e))}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def ai_action_items(title, content):
    if not content.strip():
        return None, "Note is empty - add content first"

    client = get_ai_client()
    if not client:
        return None, "No API key configured"
    try:
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=400,
            temperature=0.2,
            messages=[{"role": "user", "content":
                f"Extract all action items, tasks, or to-dos from this note. Format as a numbered list. If there are none, say so.\n\nTitle: {title}\n\nContent:\n{content}"}]
        )
        return msg.content[0].text.strip(), None
    except anthropic.APIError as e:
        return None, f"Anthropic API error: {getattr(e, 'message', str(e))}"
    except Exception as e:
        return None, f"Error: {str(e)}"

# ─── SESSION DEFAULTS ─────────────────────────────────────────────────────────

defaults = {
    "user": None,
    "page": "home",
    "active_note_id": None,
    "anthropic_key": "",
    "ai_result": "",
    "ai_mode": "Summarize",
    "ask_question": "",
    "improve_instruction": "",
    "show_invite": False,
    "show_share": False,
    "preview_version": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def nav(page, note_id=None):
    st.session_state.page = page
    st.session_state.active_note_id = note_id
    st.session_state.ai_result = ""
    st.session_state.preview_version = None
    st.rerun()

def avatar_html(name, size=28, color="#5b6cf9"):
    initials = get_user_initials(name)
    return f'<div style="display:inline-flex;align-items:center;justify-content:center;width:{size}px;height:{size}px;border-radius:50%;background:{color};color:#fff;font-size:{size//2.3:.0f}px;font-weight:700;flex-shrink:0">{initials}</div>'

# ─── PAGE: HOME / AUTH ────────────────────────────────────────────────────────

def page_home():
    st.markdown("""
    <div class="hero">
        <div class="hero-logo">📝</div>
        <h1>CollabNotes</h1>
        <p class="hero-sub">Write together. Think better. Powered by AI.</p>
    </div>
    <div style="text-align:center;margin-bottom:32px">
        <span class="feature-pill">🔐 Secure auth</span>
        <span class="feature-pill">👥 Real-time collab</span>
        <span class="feature-pill">🕐 Version history</span>
        <span class="feature-pill">✨ AI writing tools</span>
        <span class="feature-pill">🔗 Share links</span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Sign In", "Create Account", "Join with Token"])

    with tab1:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        email = st.text_input("Email", key="login_email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")
        if st.button("Sign in →", use_container_width=True, key="btn_login"):
            if not email or not password:
                st.error("Please fill in all fields")
            else:
                ok, result = login_user(email, password)
                if ok:
                    st.session_state.user = result
                    nav("dashboard")
                else:
                    st.error(result)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        name = st.text_input("Full Name", key="reg_name", placeholder="Your name")
        reg_email = st.text_input("Email", key="reg_email", placeholder="you@example.com")
        reg_pw = st.text_input("Password", type="password", key="reg_pw", placeholder="At least 6 characters")
        reg_pw2 = st.text_input("Confirm Password", type="password", key="reg_pw2", placeholder="Repeat password")
        if st.button("Create account →", use_container_width=True, key="btn_register"):
            if reg_pw!= reg_pw2:
                st.error("Passwords don't match")
            else:
                ok, result = register_user(name, reg_email, reg_pw)
                if ok:
                    st.session_state.user = result
                    st.success(f"Welcome, {result['name']}! 🎉")
                    time.sleep(0.8)
                    nav("dashboard")
                else:
                    st.error(result)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.info("Sign in first, then join a note using a share token — or paste a token below if you already have an account.", icon="ℹ️")
        st.markdown('</div>', unsafe_allow_html=True)

# ─── PAGE: DASHBOARD ─────────────────────────────────────────────────────────

def page_dashboard():
    user = st.session_state.user

    # ── Sidebar ──
    with st.sidebar:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;padding:4px 0 12px">
            {avatar_html(user['name'], 36)}
            <div>
                <div style="font-weight:700;color:#dde1f0;font-size:14px">{user['name']}</div>
                <div style="font-size:11px;color:#4a5078">{user['email']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        with st.expander("⚙️ AI Settings"):
            key_val = st.text_input(
                "Anthropic API Key", type="password",
                value=st.session_state.anthropic_key,
                placeholder="sk-ant-...",
            )
            if st.button("Save key", key="save_key"):
                st.session_state.anthropic_key = key_val
                st.toast("API key saved!", icon="✅")

        st.markdown("---")
        st.markdown('<div class="section-header">Join a shared note</div>', unsafe_allow_html=True)
        join_token = st.text_input("Share token", placeholder="e.g. A3F9BC12", key="join_token_sidebar")
        if st.button("Join note", use_container_width=True, key="btn_join"):
            if join_token.strip():
                nid, ntitle, already = join_via_token(join_token, user["email"], user["name"], user["id"])
                if nid:
                    st.toast(f"Joined: {ntitle}", icon="🔗")
                    nav("editor", nid)
                else:
                    st.error("Invalid token")
            else:
                st.error("Enter a token")

        st.markdown("---")
        if st.button("🚪 Sign out", use_container_width=True, key="btn_signout"):
            for k in defaults:
                st.session_state[k] = defaults[k]
            nav("home")

    # ── Main ──
    col_title, col_btn = st.columns([4, 1])
    with col_title:
        st.markdown('<h2 style="color:#edf0ff;font-weight:800;letter-spacing:-0.02em;margin:0">Your Notes</h2>', unsafe_allow_html=True)
    with col_btn:
        if st.button("＋ New note", use_container_width=True, key="btn_new"):
            note = create_note(user["id"], user["name"])
            nav("editor", note["id"])

    search = st.text_input("", placeholder="🔍 Search notes by title, content, or tag…", key="search", label_visibility="collapsed")

    notes = get_user_notes(user["id"], user["email"])

    if search:
        q = search.lower()
        notes = [n for n in notes if
                 q in n["title"].lower() or
                 q in n["content"].lower() or
                 any(q in t for t in n.get("tags", []))]

    if not notes:
        st.markdown("""
        <div style="text-align:center;padding:70px 20px;color:#3d4468">
            <div style="font-size:42px;margin-bottom:12px">📄</div>
            <div style="font-size:16px;font-weight:600;color:#515880">No notes yet</div>
            <div style="font-size:13px;margin-top:6px">Create your first note to get started</div>
        </div>
        """, unsafe_allow_html=True)
        return

    cols = st.columns(3, gap="small")
    for i, note in enumerate(notes):
        with cols[i % 3]:
            is_owner = note["owner_id"] == user["id"]
            preview = note["content"].replace("\n", " ")[:110] or "No content yet…"
            tags_html = "".join(f'<span class="tag">{t}</span>' for t in note.get("tags", [])[:4])
            badge = '<span class="badge-owner">Owner</span>' if is_owner else '<span class="badge-shared">Shared</span>'
            collab_count = len(note.get("collaborators", []))
            wc = note.get("word_count", len(note["content"].split()) if note["content"] else 0)

            st.markdown(f"""
            <div class="note-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px">
                    <div class="note-title">{note['title']}</div>
                    {badge}
                </div>
                <div class="note-preview">{preview}{"…" if len(note["content"]) > 110 else ""}</div>
                {f'<div style="margin-top:8px">{tags_html}</div>' if tags_html else ""}
                <div class="note-meta">
                    <span>🕐 {time_ago(note['updated_at'])}</span>
                    {f'<span>· 👥 {collab_count}</span>' if collab_count else ''}
                    {f'<span>· {wc} words</span>' if wc else ''}
                </div>
            """, unsafe_allow_html=True)

            bcol1, bcol2 = st.columns(2)
            with bcol1:
                if st.button("Open", key=f"open_{note['id']}", use_container_width=True):
                    nav("editor", note["id"])
            with bcol2:
                if is_owner:
                    if st.button("Delete", key=f"del_{note['id']}", use_container_width=True):
                        delete_note(note["id"])
                        st.rerun()

# ─── PAGE: EDITOR ─────────────────────────────────────────────────────────────