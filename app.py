import json
import os
from typing import List, Dict, Any
import streamlit as st
import pandas as pd
import requests

MAX_GAMES = 28
LOCAL_DATA_PATH = "app_data/league.json"

# ---- Ultra-light health endpoint ----
if st.query_params.get("health") == "1":
    st.write("OK")
    st.stop()

# ------------------------ Admin PIN ------------------------
def is_admin_enabled() -> bool:
    return bool(st.secrets.get("ADMIN_PIN"))

def admin_unlocked() -> bool:
    return st.session_state.get("is_admin", False)

def admin_gate_ui():
    if not is_admin_enabled():
        st.caption("🔓 Admin PIN not set; editing is open.")
        st.session_state["is_admin"] = True
        return

    if admin_unlocked():
        st.caption("🔐 Admin mode unlocked for this session.")
        if st.button("Lock Admin"):
            st.session_state["is_admin"] = False
            st.rerun()
        return

    with st.expander("🔐 Unlock admin actions"):
        pin = st.text_input("Enter admin PIN", type="password")
        if st.button("Unlock"):
            if pin == st.secrets.get("ADMIN_PIN"):
                st.session_state["is_admin"] = True
                st.success("Admin unlocked.")
                st.rerun()
            else:
                st.error("Incorrect PIN.")

# ------------------------ Persistence Layer ------------------------
def _gist_headers():
    token = st.secrets.get("GITHUB_TOKEN", None)
    if not token:
        return None
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

def _gist_url():
    gist_id = st.secrets.get("GIST_ID", None)
    if not gist_id:
        return None
    return f"https://api.github.com/gists/{gist_id}"

@st.cache_data(ttl=60, show_spinner=False)
def _cached_gist_json(url: str, headers: Dict[str,str]):
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()

def _load_from_gist():
    url = _gist_url()
    headers = _gist_headers()
    if not url or not headers:
        return None
    try:
        data = _cached_gist_json(url, headers)
        files = data.get("files", {})
        if "league.json" in files:
            content = files["league.json"].get("content", "{}")
            payload = json.loads(content or "{}")
            if not isinstance(payload, dict) or "players" not in payload:
                payload = {"players": []}
            return payload
        return {"players": []}
    except Exception:
        return None

def _save_to_gist(payload: Dict[str, Any]) -> bool:
    url = _gist_url()
    headers = _gist_headers()
    if not url or not headers:
        return False
    try:
        body = {"files": {"league.json": {"content": json.dumps(payload, indent=2)}}}
        r = requests.patch(url, headers=headers, json=body, timeout=15)
        r.raise_for_status()
        _cached_gist_json.clear()
        return True
    except Exception:
        return False

def load_data() -> Dict[str, Any]:
    data = _load_from_gist()
    if data is not None:
        return data
    if os.path.exists(LOCAL_DATA_PATH):
        try:
            with open(LOCAL_DATA_PATH, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if not isinstance(payload, dict) or "players" not in payload:
                payload = {"players": []}
            return payload
        except Exception:
            pass
    return {"players": []}

def save_data(data: Dict[str, Any]) -> None:
    if not _save_to_gist(data):
        os.makedirs(os.path.dirname(LOCAL_DATA_PATH), exist_ok=True)
        with open(LOCAL_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

# ------------------------ Domain Logic ------------------------
def upsert_player(data, name: str, start_hc: int):
    data.setdefault("players", [])
    for p in data["players"]:
        if p.get("name","").lower() == name.lower():
            p["start_hc"] = int(start_hc)
            return
    data["players"].append({
        "name": name,
        "start_hc": int(start_hc),
        "results": [],
        "adjustments": [],
    })

def delete_player(data, name: str):
    data["players"] = [p for p in data.get("players", []) if p.get("name","").lower() != name.lower()]

def evaluate_adjustments(results: List[str]) -> Dict[str, Any]:
    adj_events = []
    lock_until = -1
    last_window = None
    for i in range(len(results)):
        if i < 3: continue
        if i <= lock_until: continue
        window = results[i-3:i+1]
        wins = window.count("W")
        losses = window.count("L")
        change = 0
        if wins >= 3: change = -7
        elif losses >= 3: change = +7
        if change != 0:
            adj_events.append({"game_index": i, "change": change})
            lock_until = i + 4
            last_window = (i-3, i)
    delta = sum(e["change"] for e in adj_events)
    return {"adjustments": adj_events, "delta": delta, "last_window": last_window}

def current_handicap(start_hc: int, results: List[str]) -> int:
    return start_hc + evaluate_adjustments(results)["delta"]

def roster_df(data):
    rows = []
    for p in data.get("players", []):
        res = p.get("results", [])
        cur = current_handicap(int(p.get("start_hc", 0)), res if isinstance(res, list) else [])
        rows.append({
            "Player": p.get("name",""),
            "Season Start HC": int(p.get("start_hc", 0)),
            "Current HC": cur,
            "Games": len(res) if isinstance(res, list) else 0,
            "Wins": res.count("W") if isinstance(res, list) else 0,
            "Losses": res.count("L") if isinstance(res, list) else 0,
            "Cuts": sum(1 for e in evaluate_adjustments(res)["adjustments"] if e["change"] == -7),
            "Increases": sum(1 for e in evaluate_adjustments(res)["adjustments"] if e["change"] == +7),
            "Net Change": cur - int(p.get("start_hc", 0)),
        })
    cols = ["Player","Season Start HC","Current HC","Games","Wins","Losses","Cuts","Increases","Net Change"]
    if not rows:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(rows)
    return df.sort_values(["Player"]).reset_index(drop=True)

# ------------------------ Streamlit UI ------------------------
st.set_page_config(page_title="Handicap Tracker", layout="wide")
st.title("Snooker Handicap Tracker")

if st.secrets.get("GITHUB_TOKEN") and st.secrets.get("GIST_ID"):
    st.caption("Storage: GitHub Gist (configured).")
else:
    st.caption("Storage: Local file (for local runs). Configure Streamlit Secrets for cloud persistence.")

admin_gate_ui()
data = load_data()

tab_roster, tab_record, tab_player, tab_summary, tab_import = st.tabs(
    ["Roster", "Record Result", "Player Detail", "Summary", "Import/Export"]
)

with tab_roster:
    st.subheader("Players")
    st.dataframe(roster_df(data), use_container_width=True)
    if admin_unlocked():
        with st.expander("Add / Update Player"):
            c1, c2, c3 = st.columns([2,1,1])
            with c1:
                name = st.text_input("Name")
            with c2:
                hc = st.number_input("Season Start HC", step=7, value=0)
            if st.button("Save Player"):
                if name:
                    upsert_player(data, name, hc)
                    save_data(data)
                    st.success("Player saved.")
                    st.rerun()
        with st.expander("Delete Player"):
            names = [p["name"] for p in data.get("players", [])]
            sel = st.selectbox("Select", names)
            if st.button("Delete") and sel:
                delete_player(data, sel)
                save_data(data)
                st.success("Deleted.")
                st.rerun()

# Add record/player/summary/import tabs UI as in earlier builds...
