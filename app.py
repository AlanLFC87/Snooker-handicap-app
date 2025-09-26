
import json
import os
from typing import Dict, Any, Optional, List
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

LEAGUE_NAME = "Belfast District Snooker League"
MAX_GAMES = 28
LOCAL_DATA_PATH = "app_data/league.json"
TEAM_CHOICES: List[str] = [
    "Ballygomartin A",
    "Ballygomartin B",
    "Ballygomartin C",
    "East",
    "Premier",
    "QE2 A",
    "QE2 B",
    "Shorts",
]

# ---------------- Fixtures (static) ----------------
FIXTURES = [
    {"week": 1, "date": "18/09/2025", "matches": [
        "Ballygomartin B v Ballygomartin A",
        "QE2 A v QE2 B",
        "Shorts v Ballygomartin C",
        "East v Premier"
    ]},
    {"week": 2, "date": "25/09/2025", "matches": [
        "QE2 A v Ballygomartin B",
        "Ballygomartin A v QE2 B",
        "East v Shorts",
        "Premier v Ballygomartin C"
    ]},
    {"week": 3, "date": "02/10/2025", "matches": [
        "Ballygomartin B v QE2 B",
        "QE2 A v Ballygomartin A",
        "Premier v Shorts",
        "Ballygomartin C v East"
    ]},
    {"week": 4, "date": "09/10/2025", "matches": [
        "Shorts v Ballygomartin B",
        "Ballygomartin A v Ballygomartin C",
        "East v QE2 A",
        "QE2 B v Premier"
    ]},
    {"week": 5, "date": "16/10/2025", "matches": [
        "Ballygomartin C v Ballygomartin B",
        "East v Ballygomartin A",
        "QE2 A v Premier",
        "Shorts v QE2 B"
    ]},
    {"week": 6, "date": "23/10/2025", "matches": [
        "Ballygomartin B v East",
        "Premier v Ballygomartin A",
        "Shorts v QE2 A",
        "Ballygomartin C v QE2 B"
    ]},
    {"week": 7, "date": "30/10/2025", "matches": [
        "Premier v Ballygomartin B",
        "Ballygomartin A v Shorts",
        "Ballygomartin C v QE2 A",
        "QE2 B v East"
    ]},
    {"week": 8, "date": "06/11/2025", "matches": [
        "Ballygomartin A v Ballygomartin B",
        "QE2 B v QE2 A",
        "Ballygomartin C v Shorts",
        "Premier v East"
    ]},
    {"week": 9, "date": "13/11/2025", "matches": [
        "Ballygomartin B v QE2 A",
        "QE2 B v Ballygomartin A",
        "Shorts v East",
        "Ballygomartin C v Premier"
    ]},
    {"week": 10, "date": "20/11/2025", "matches": [
        "QE2 B v Ballygomartin B",
        "Ballygomartin A v QE2 A",
        "Shorts v Premier",
        "East v Ballygomartin C"
    ]},
    {"week": 11, "date": "27/11/2025", "matches": [
        "Ballygomartin B v Shorts",
        "Ballygomartin C v Ballygomartin A",
        "QE2 A v East",
        "Premier v QE2 B"
    ]},
    {"week": 12, "date": "04/12/2025", "matches": [
        "Ballygomartin B v Ballygomartin C",
        "Ballygomartin A v East",
        "Premier v QE2 A",
        "QE2 B v Shorts"
    ]},
    {"week": 13, "date": "11/12/2025", "matches": [
        "East v Ballygomartin B",
        "Ballygomartin A v Premier",
        "QE2 A v Shorts",
        "QE2 B v Ballygomartin C"
    ]},
    {"week": 14, "date": "18/12/2025", "matches": [
        "Ballygomartin B v Premier",
        "Shorts v Ballygomartin A",
        "QE2 A v Ballygomartin C",
        "East v QE2 B"
    ]},
    {"week": 15, "date": "05/02/2026", "matches": [
        "Ballygomartin B v Ballygomartin A",
        "QE2 A v QE2 B",
        "Shorts v Ballygomartin C",
        "East v Premier"
    ]},
    {"week": 16, "date": "12/02/2026", "matches": [
        "QE2 A v Ballygomartin B",
        "Ballygomartin A v QE2 B",
        "East v Shorts",
        "Premier v Ballygomartin C"
    ]},
    {"week": 17, "date": "19/02/2026", "matches": [
        "Ballygomartin B v QE2 B",
        "QE2 A v Ballygomartin A",
        "Premier v Shorts",
        "Ballygomartin C v East"
    ]},
    {"week": 18, "date": "26/02/2026", "matches": [
        "Shorts v Ballygomartin B",
        "Ballygomartin A v Ballygomartin C",
        "East v QE2 A",
        "QE2 B v Premier"
    ]},
    {"week": 19, "date": "05/03/2026", "matches": [
        "Ballygomartin C v Ballygomartin B",
        "East v Ballygomartin A",
        "QE2 A v Premier",
        "Shorts v QE2 B"
    ]},
    {"week": 20, "date": "12/03/2026", "matches": [
        "Ballygomartin B v East",
        "Premier v Ballygomartin A",
        "Shorts v QE2 A",
        "Ballygomartin C v QE2 B"
    ]},
    {"week": 21, "date": "19/03/2026", "matches": [
        "Premier v Ballygomartin B",
        "Ballygomartin A v Shorts",
        "Ballygomartin C v QE2 A",
        "QE2 B v East"
    ]},
    {"week": 22, "date": "26/03/2026", "matches": [
        "Ballygomartin A v Ballygomartin B",
        "QE2 B v QE2 A",
        "Ballygomartin C v Shorts",
        "Premier v East"
    ]},
    {"week": 23, "date": "02/04/2026", "matches": [
        "Ballygomartin B v QE2 A",
        "QE2 B v Ballygomartin A",
        "Shorts v East",
        "Ballygomartin C v Premier"
    ]},
    {"week": 24, "date": "09/04/2026", "matches": [
        "QE2 B v Ballygomartin B",
        "Ballygomartin A v QE2 A",
        "Shorts v Premier",
        "East v Ballygomartin C"
    ]},
    {"week": 25, "date": "16/04/2026", "matches": [
        "Ballygomartin B v Shorts",
        "Ballygomartin C v Ballygomartin A",
        "QE2 A v East",
        "Premier v QE2 B"
    ]},
    {"week": 26, "date": "23/04/2026", "matches": [
        "Ballygomartin B v Ballygomartin C",
        "Ballygomartin A v East",
        "Premier v QE2 A",
        "QE2 B v Shorts"
    ]},
    {"week": 27, "date": "30/04/2026", "matches": [
        "East v Ballygomartin B",
        "Ballygomartin A v Premier",
        "QE2 A v Shorts",
        "QE2 B v Ballygomartin C"
    ]},
    {"week": 28, "date": "07/05/2026", "matches": [
        "Ballygomartin B v Premier",
        "Shorts v Ballygomartin A",
        "QE2 A v Ballygomartin C",
        "East v QE2 B"
    ]},
]

# ---------------- Health ----------------
if st.query_params.get("health") == "1":
    st.write("OK")
    st.stop()

# ---------------- Admin / PIN ----------------
def is_admin_enabled() -> bool:
    return bool(st.secrets.get("ADMIN_PIN"))

def admin_unlocked() -> bool:
    return st.session_state.get("is_admin", False)

def set_unlocked(val: bool):
    st.session_state["is_admin"] = bool(val)

def sidebar_admin():
    st.markdown("### 🔒 Admin")
    if not is_admin_enabled():
        st.caption("Admin PIN not set; editing is open. (Add ADMIN_PIN in Secrets to restrict edits.)")
        set_unlocked(True)
        return
    if admin_unlocked():
        st.success("Admin mode unlocked")
        if st.button("Lock Admin", key="btn_lock_admin", help="Lock admin mode"):
            set_unlocked(False); st.rerun()
        return
    pin = st.text_input("Enter admin PIN", type="password", key="sidebar_pin")
    if st.button("Unlock", key="sidebar_unlock"):
        if pin == st.secrets.get("ADMIN_PIN"):
            set_unlocked(True); st.success("Unlocked"); st.rerun()
        else:
            st.error("Incorrect PIN.")

def inline_unlock(suffix: str):
    if not is_admin_enabled() or admin_unlocked():
        return
    st.warning("Editing is locked. Unlock to make changes.")
    c1, c2 = st.columns([3,1])
    with c1:
        pin = st.text_input("PIN", type="password", key=f"inline_pin_{suffix}")
    with c2:
        if st.button("Unlock", key=f"inline_unlock_{suffix}"):
            if pin == st.secrets.get("ADMIN_PIN"):
                set_unlocked(True); st.success("Admin unlocked."); st.rerun()
            else:
                st.error("Incorrect PIN.")

# ---------------- Persistence ----------------
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

def _load_from_gist_uncached() -> Optional[Dict[str, Any]]:
    url = _gist_url(); headers = _gist_headers()
    if not url or not headers:
        return None
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
        files = data.get("files", {})
        if "league.json" in files:
            content = files["league.json"].get("content", "{}")
            payload = json.loads(content or "{}")
            if not isinstance(payload, dict):
                payload = {}
            payload.setdefault("players", [])
            payload.setdefault("announcement", "")
            payload.setdefault("announcements", [])
            for p in payload["players"]:
                p.setdefault("team", "")
            return payload
        return {"players": [], "announcement": "", "announcements": []}
    except Exception:
        return None

def _save_to_gist(payload: Dict[str, Any]) -> bool:
    url = _gist_url(); headers = _gist_headers()
    if not url or not headers:
        return False
    try:
        body = {"files": {"league.json": {"content": json.dumps(payload, indent=2)}}}
        r = requests.patch(url, headers=headers, json=body, timeout=25)
        r.raise_for_status()
        return True
    except Exception:
        return False

def _load_local() -> Optional[Dict[str, Any]]:
    if os.path.exists(LOCAL_DATA_PATH):
        try:
            with open(LOCAL_DATA_PATH, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if not isinstance(payload, dict): payload = {}
            payload.setdefault("players", [])
            payload.setdefault("announcement", "")
            payload.setdefault("announcements", [])
            for p in payload["players"]:
                p.setdefault("team", "")
            return payload
        except Exception:
            return None
    return None

def _save_local(payload: Dict[str, Any]) -> bool:
    try:
        os.makedirs(os.path.dirname(LOCAL_DATA_PATH), exist_ok=True)
        with open(LOCAL_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return True
    except Exception:
        return False

def init_session_data():
    if "data" in st.session_state:
        return
    data = _load_from_gist_uncached() or _load_local() or {"players": [], "announcement": "", "announcements": []}
    for p in data.get("players", []):
        p.setdefault("team", "")
    st.session_state["data"] = data
    st.session_state["storage_mode"] = "gist" if (_gist_url() and _gist_headers()) else ("local" if _load_local() is not None else "memory")

def get_data() -> Dict[str, Any]:
    return st.session_state["data"]

def save_and_sync(show_toast: bool = False) -> bool:
    payload = get_data()
    ok = _save_to_gist(payload)
    if not ok:
        _save_local(payload)
    if show_toast:
        st.toast("Saved" if ok else "Saved (cloud failed)")
    return ok

# ---------------- Domain ----------------
def upsert_player(data, name: str, start_hc: int, team: str = ""):
    team = team if team in TEAM_CHOICES or team == "" else ""
    for p in data.get("players", []):
        if p.get("name","").lower() == name.lower():
            p["start_hc"] = int(start_hc)
            p["team"] = team
            return
    data["players"].append({"name": name, "start_hc": int(start_hc), "team": team, "results": [], "adjustments": []})

def delete_player(data, name: str):
    data["players"] = [p for p in data.get("players", []) if p.get("name","").lower() != name.lower()]

def evaluate_adjustments(results):
    adj_events = []
    lock_until = -1
    last_window = None
    for i in range(len(results)):
        if i < 3: continue
        if i < lock_until: continue
        window = results[i-3:i+1]
        wins = window.count("W"); losses = window.count("L")
        change = -7 if wins >= 3 else (+7 if losses >= 3 else 0)
        if change:
            adj_events.append({"game_index": i, "change": change})
            lock_until = i + 4
            last_window = (i-3, i)
    delta = sum(e["change"] for e in adj_events)
    return {"adjustments": adj_events, "delta": delta, "last_window": last_window}

def current_handicap(start_hc: int, results):
    return start_hc + evaluate_adjustments(results)["delta"]

def roster_df(data):
    rows = []
    for p in data.get("players", []):
        res = p.get("results", [])
        cur = current_handicap(int(p.get("start_hc", 0)), res if isinstance(res, list) else [])
        rows.append({
            "Player": p.get("name",""),
            "Team": p.get("team",""),
            "Season Start HC": int(p.get("start_hc", 0)),
            "Current HC": cur,
            "Games": len(res) if isinstance(res, list) else 0,
            "Wins": res.count("W") if isinstance(res, list) else 0,
            "Losses": res.count("L") if isinstance(res, list) else 0,
            "Cuts": sum(1 for e in evaluate_adjustments(res)["adjustments"] if e["change"] == -7) if isinstance(res, list) else 0,
            "Increases": sum(1 for e in evaluate_adjustments(res)["adjustments"] if e["change"] == +7) if isinstance(res, list) else 0,
            "Net Change": cur - int(p.get("start_hc", 0)),
        })
    cols = ["Player","Team","Season Start HC","Current HC","Games","Wins","Losses","Cuts","Increases","Net Change"]
    return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)

def chip_html(results, last_window):
    chips = []
    for idx, r in enumerate(results or []):
        highlighted = last_window and last_window[0] <= idx <= last_window[1]
        base = "display:inline-block;margin:2px 4px;padding:4px 10px;border-radius:999px;font-weight:700;"
        color = "background:#065f46;color:#f0fdf4;" if (highlighted and r == "W") else ("background:#7f1d1d;color:#fee2e2;" if (highlighted and r == "L") else "background:#0b3d2e;color:#e5e7eb;")
        chips.append(f"<span style='{base}{color}'>{r}</span>")
    return " ".join(chips) if chips else "<em>No games yet</em>"

def add_highlight_announcement(data, player_name: str, change: int):
    ts = datetime.now(timezone.utc); expires = ts + timedelta(days=7)
    msg = f"🏆 {player_name} handicap cut by 7 after strong form." if change < 0 else f"📈 {player_name} handicap increased by 7 after recent results."
    data.setdefault("announcements", []).append({"msg": msg, "ts": ts.isoformat(), "expires": expires.isoformat()})

def active_highlights(data):
    out = []; now = datetime.now(timezone.utc)
    for a in data.get("announcements", []):
        try:
            exp = datetime.fromisoformat(a.get("expires"))
        except Exception:
            continue
        if exp.tzinfo is None: exp = exp.replace(tzinfo=timezone.utc)
        if exp > now: out.append(a)
    out.sort(key=lambda x: x.get("ts",""), reverse=True)
    return out

def remove_highlight_by_ts(data, ts_str: str) -> bool:
    arr = data.get("announcements", [])
    before = len(arr)
    data["announcements"] = [a for a in arr if a.get("ts") != ts_str]
    return len(data["announcements"]) < before

# Helpers for fixtures
def fixtures_dataframe():
    rows = []
    for f in FIXTURES:
        for i, m in enumerate(f["matches"], start=1):
            rows.append({
                "Week": f["week"],
                "Date": f["date"],
                "Match #": i,
                "Fixture": m
            })
    df = pd.DataFrame(rows, columns=["Week","Date","Match #","Fixture"])
    return df

# ---------------- UI ----------------
st.set_page_config(page_title="Handicap Tracker", layout="wide")

with st.sidebar:
    st.markdown("### League")
    st.markdown(f"**{LEAGUE_NAME}**")
    # Minimal admin area (PIN optional)
    if st.secrets.get("ADMIN_PIN"):
        if st.session_state.get("is_admin", False):
            st.success("Admin unlocked")
            if st.button("Lock Admin"):
                st.session_state["is_admin"] = False; st.rerun()
        else:
            pin = st.text_input("Enter admin PIN", type="password")
            if st.button("Unlock"):
                if pin == st.secrets.get("ADMIN_PIN"):
                    st.session_state["is_admin"] = True; st.rerun()
                else:
                    st.error("Incorrect PIN")
    st.caption("Storage: Gist if configured, else local/session")

# Load data (local/session or gist)
def _maybe_load():
    url = st.secrets.get("GIST_ID", None)
    token = st.secrets.get("GITHUB_TOKEN", None)
    if not url or not token:
        return None
    try:
        r = requests.get(f"https://api.github.com/gists/{url}", headers={"Authorization": f"token {token}"})
        r.raise_for_status()
        files = r.json().get("files", {})
        if "league.json" in files:
            return json.loads(files["league.json"]["content"])
    except Exception:
        pass
    return None

if "data" not in st.session_state:
    st.session_state["data"] = _maybe_load() or {"players": [], "announcement": "", "announcements": []}

data = st.session_state["data"]

tab_home, tab_roster, tab_record, tab_player, tab_summary, tab_fixtures, tab_import = st.tabs(
    ["🏠 Home", "👥 Roster", "🎯 Record", "🧑 Player", "📊 Summary", "📅 Fixtures", "📥 Import/Export"]
)

with tab_home:
    st.markdown(f"## {LEAGUE_NAME}")
    st.caption("Snooker handicap tracker with rolling 4-game adjustments.")
    st.markdown("### 📣 Announcement")
    msg = data.get("announcement","").strip()
    if st.session_state.get("is_admin", False):
        msg = st.text_area("Edit announcement", value=msg, height=100)
        if st.button("Save Announcement"):
            data["announcement"] = msg.strip()
            st.success("Saved")
    else:
        if msg: st.info(msg)
        else: st.caption("No announcement yet.")

with tab_roster:
    st.subheader("Players")
    df = pd.DataFrame(data.get("players", []))
    if not df.empty:
        team_filter = st.multiselect("Filter by team", TEAM_CHOICES, default=TEAM_CHOICES)
        df = df[df["team"].isin(team_filter)]
        st.dataframe(df, width="stretch")
    else:
        st.caption("No players yet.")

with tab_record:
    st.subheader("Record W/L")
    if not data.get("players"):
        st.info("Add players first.")
    else:
        names = [p["name"] for p in data["players"]]
        name = st.selectbox("Player", names)
        player = next(p for p in data["players"] if p["name"] == name)
        res = player.setdefault("results", [])
        c1, c2, c3 = st.columns(3)
        if c1.button("✅ Add Win (W)"):
            if len(res) < MAX_GAMES:
                res.append("W"); st.success("Win added"); st.rerun()
            else: st.warning("Max 28 games reached.")
        if c2.button("❌ Add Loss (L)"):
            if len(res) < MAX_GAMES:
                res.append("L"); st.warning("Loss added"); st.rerun()
            else: st.warning("Max 28 games reached.")
        if c3.button("↩️ Undo last game"):
            if res: res.pop(); st.info("Undone"); st.rerun()
        st.write("Timeline:", " ".join(res) if res else "—")

with tab_player:
    if not data.get("players"):
        st.info("Add players first.")
    else:
        sel = st.selectbox("Select player", [p["name"] for p in data["players"]])
        player = next(p for p in data["players"] if p["name"] == sel)
        st.header(sel)
        res = player.get("results", [])
        st.write("Games:", len(res))
        st.write("Results:", " ".join(res) if res else "—")

with tab_summary:
    st.subheader("Summary")
    df = pd.DataFrame(data.get("players", []))
    if not df.empty:
        st.dataframe(df, width="stretch")
    else:
        st.caption("No data yet.")

# -------- Fixtures tab with SINGLE combined dropdown --------
with tab_fixtures:
    st.subheader("Fixtures")
    # Build labels like "Week 1 — 18/09/2025"
    labels = [f"Week {f['week']} — {f['date']}" for f in FIXTURES]
    label_to_fixture = {f"Week {f['week']} — {f['date']}": f for f in FIXTURES}
    choice = st.selectbox("Select week", labels, index=0)
    fx = label_to_fixture[choice]
    st.markdown(f"### {choice}")
    # Show four matches
    show = pd.DataFrame({"Match #": [1,2,3,4], "Fixture": fx["matches"]})
    st.dataframe(show, width="stretch")

with tab_import:
    st.subheader("Import/Export (basic)")
    st.download_button("Download JSON backup", data=json.dumps(data, indent=2), file_name="league_backup.json", mime="application/json")
