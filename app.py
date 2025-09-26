
import json
import os
from typing import Dict, Any, Optional, List, Tuple
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
            payload.setdefault("league_results", {})
            for p in payload["players"]:
                p.setdefault("team", "")
            return payload
        return {"players": [], "announcement": "", "announcements": [], "league_results": {}}
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
    path = LOCAL_DATA_PATH
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if not isinstance(payload, dict): payload = {}
            payload.setdefault("players", [])
            payload.setdefault("announcement", "")
            payload.setdefault("announcements", [])
            payload.setdefault("league_results", {})
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
    data = _load_from_gist_uncached() or _load_local() or {"players": [], "announcement": "", "announcements": [], "league_results": {}}
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

# ---------------- Domain (players) ----------------
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

# ---------------- League helpers (frames-as-points) ----------------
def _all_teams_from_fixtures() -> List[str]:
    teams = set()
    for f in FIXTURES:
        for m in f["matches"]:
            if " v " in m:
                h, a = m.split(" v ", 1)
                teams.add(h.strip()); teams.add(a.strip())
    return sorted(teams)

def _fixture_week(week: int) -> Optional[Dict[str, Any]]:
    for f in FIXTURES:
        if f["week"] == week:
            return f
    return None

def _parse_match(s: str) -> Tuple[str, str]:
    h, a = s.split(" v ", 1)
    return h.strip(), a.strip()

def _init_league_results(data: Dict[str, Any]):
    data.setdefault("league_results", {})  # {week: [{"home":..., "away":..., "hf": int|None, "af": int|None}]}
    return data["league_results"]

def _compute_league_table(data: Dict[str, Any]) -> pd.DataFrame:
    teams = _all_teams_from_fixtures()
    rows = {t: {"Team": t, "Played": 0, "Points": 0, "Frames For": 0, "Frames Against": 0} for t in teams}

    lres = data.get("league_results", {})
    for week, matches in lres.items():
        for m in matches:
            if m.get("hf") is None or m.get("af") is None:
                continue
            h, a, hf, af = m["home"], m["away"], int(m["hf"]), int(m["af"])
            rows[h]["Played"] += 1; rows[a]["Played"] += 1
            rows[h]["Frames For"] += hf; rows[h]["Frames Against"] += af
            rows[a]["Frames For"] += af; rows[a]["Frames Against"] += hf
            rows[h]["Points"] += hf; rows[a]["Points"] += af

    df = pd.DataFrame(rows.values())
    if not df.empty:
        df["Frame Diff"] = df["Frames For"] - df["Frames Against"]
        df = df.sort_values(["Points", "Frame Diff", "Frames For"], ascending=[False, False, False]).reset_index(drop=True)
        df.index = df.index + 1
        df.insert(0, "Pos", df.index)
    else:
        df = pd.DataFrame(columns=["Pos","Team","Played","Points","Frames For","Frames Against","Frame Diff"])
    return df

# ---------------- UI ----------------
st.set_page_config(page_title="Handicap Tracker", layout="wide")

# Sidebar: theme toggle + admin
with st.sidebar:
    st.markdown("### League")
    st.markdown(f"**{LEAGUE_NAME}**")
    hc = st.toggle("High contrast mode", key="high_contrast", value=False, help="Improves readability for some users")
    sidebar_admin()
    st.caption(f"Storage: {'Gist' if (_gist_url() and _gist_headers()) else 'Local/Session'}")

# CSS polish & contrast
base_css = """
<style>
.block-container {padding-top: 3.75rem; padding-bottom: 2rem; max-width: 1100px;}
.stTabs [role="tablist"] { margin-top: 0.75rem; }
section[data-testid="stSidebar"] { padding-top: 0.75rem; overflow:auto; }
.card { border: 1px solid #14532d; background: linear-gradient(180deg,#064e3b,#052e22); border-radius: 12px; padding: 12px 14px; margin-bottom: 10px; color: #ecfdf5;}
.card h4 { margin: 0 0 6px 0; }
.sub { opacity: 0.9; font-size: 0.9rem; }
.metric { display:inline-block; margin-right:12px; padding:4px 8px; border-radius:8px; background:#0b3d2e; }
.badge { display:inline-block;margin:2px 4px;padding:4px 10px;border-radius:999px;font-weight:700;background:#0b3d2e;color:#e5e7eb;}
.badge.win { background:#065f46; color:#f0fdf4; }
.badge.loss { background:#7f1d1d; color:#fee2e2; }
.tbl { overflow-x: auto; }
</style>
"""
high_contrast_css = """
<style>
.card { background: #0a0a0a; border-color: #22c55e; color: #fafafa; }
.metric { background: #111827; }
.badge { background: #0f172a; color: #f8fafc; }
</style>
"""
st.markdown(base_css, unsafe_allow_html=True)
if st.session_state.get("high_contrast"):
    st.markdown(high_contrast_css, unsafe_allow_html=True)

# Initialize data
if "data" not in st.session_state:
    init_session_data()
data = get_data()

# Tabs
tab_home, tab_roster, tab_record, tab_player, tab_summary, tab_fixtures, tab_league, tab_import, tab_help = st.tabs(
    ["🏠 Home", "👥 Roster", "🎯 Record", "🧑 Player", "📊 Summary", "📅 Fixtures", "🏆 League", "📥 Import/Export", "❓ Help"]
)

with tab_home:
    st.markdown(f"## {LEAGUE_NAME}")
    st.caption("Snooker handicap tracker with rolling 4-game adjustments.")
    st.markdown("### 📣 Announcement")
    if admin_unlocked():
        new_msg = st.text_area("Edit announcement (visible to everyone):", value=data.get("announcement",""), height=100, key="ta_announce")
        can_save = len(new_msg.strip()) >= 0
        if st.button("Save Announcement", disabled=not can_save, key="btn_save_announce"):
            data["announcement"] = new_msg.strip()
            save_and_sync(True); st.rerun()
    else:
        msg = data.get("announcement","").strip()
        st.info(msg) if msg else st.caption("No announcement yet.")

    st.markdown("### 🌟 Highlights (last 7 days)")
    hs = active_highlights(data)
    if hs:
        for i, h in enumerate(hs[:10]):
            ts = h.get('ts','')
            dt = ts.split('T')[0] if ts else ''
            cols = st.columns([8,2]) if admin_unlocked() else [st.container()]
            if admin_unlocked():
                with cols[0]:
                    st.markdown(f"- {h['msg']}  \n  _since {dt}_")
                with cols[1]:
                    if st.button("Remove", key=f"rm_highlight_{i}", help="Remove this highlight"):
                        if remove_highlight_by_ts(data, ts):
                            save_and_sync(True); st.rerun()
            else:
                st.markdown(f"- {h['msg']}  \n  _since {dt}_")
    else:
        st.caption("No recent highlights.")

with tab_roster:
    st.subheader("Players")
    # Search and team filter
    q = st.text_input("Search players or teams", key="roster_search", placeholder="Start typing...")
    selected_teams = st.multiselect("Filter by team", TEAM_CHOICES, default=TEAM_CHOICES, key="roster_team_filter")
    view = st.radio("View", ["Cards","Table"], horizontal=True, key="roster_view")
    inline_unlock("roster")

    # Form: Add/Update with inline validation & Clear
    with st.expander("Add / Update Player", expanded=False):
        c1, c2 = st.columns([2,1])
        name = c1.text_input("Name (required)", key="name_add")
        hc = c2.number_input("Season Start HC (multiples of 7)", step=7, value=0, key="hc_add")
        tsel = st.selectbox("Team", ["(none)"] + TEAM_CHOICES, index=0, key="team_add")
        team_value = "" if tsel == "(none)" else tsel

        form_cols = st.columns([1,1,1])
        with form_cols[0]:
            save_disabled = (not admin_unlocked()) or (not name.strip())
            if st.button("Save Player", disabled=save_disabled, key="btn_save_player"):
                upsert_player(data, name.strip(), int(hc), team_value); save_and_sync(True); st.success("Player saved."); st.rerun()
        with form_cols[1]:
            if st.button("Clear", key="btn_clear_player"):
                st.session_state["name_add"] = ""
                st.session_state["hc_add"] = 0
                st.session_state["team_add"] = "(none)"
                st.rerun()
        with form_cols[2]:
            del_names = [p.get("name","") for p in data.get("players", [])]
            del_sel = st.selectbox("Delete player", ["(choose)"]+del_names, key="del_select")
            confirm = st.checkbox("Confirm delete", key="chk_del_confirm")
            if st.button("Delete", disabled=(not admin_unlocked()) or (del_sel=="(choose)") or (not confirm), key="btn_delete"):
                delete_player(data, del_sel); save_and_sync(True); st.warning(f"Deleted {del_sel}."); st.rerun()

    # Data
    players = [p for p in data.get("players", []) if (p.get("team","") in selected_teams)]
    if q:
        ql = q.lower().strip()
        players = [p for p in players if (ql in p.get("name","").lower() or ql in p.get("team","").lower())]

    if view == "Cards":
        for p in players:
            res = p.get("results", [])
            cur = current_handicap(int(p.get("start_hc",0)), res)
            wins = res.count("W"); losses = res.count("L")
            team = p.get("team","")
            st.markdown(f"""
<div class="card">
  <h4>{p.get('name','')} <span class="badge">{team or '(no team)'}</span></h4>
  <div class="sub">Start HC: <b>{int(p.get('start_hc',0))}</b> • Current HC: <b>{cur}</b> • Games: <b>{len(res)}/{MAX_GAMES}</b></div>
  <div style="margin:6px 0;">
    <span class="metric">W: {wins}</span> <span class="metric">L: {losses}</span>
  </div>
</div>
""", unsafe_allow_html=True)
            # Clickable: set selection for Player tab
            cols = st.columns([1,1,6])
            with cols[0]:
                if st.button("View", key=f"view_{p.get('name','')}"):
                    st.session_state["selected_player"] = p.get("name",""); st.toast("Open the Player tab to view details.")
            with cols[1]:
                if st.button("Record", key=f"record_{p.get('name','')}"):
                    st.session_state["selected_player"] = p.get("name",""); st.toast("Open the Record tab to add W/L.")
    else:
        df_r = roster_df({"players": players})
        st.dataframe(df_r, width="stretch")

with tab_record:
    st.subheader("Record W/L")
    inline_unlock("record")
    team_sel = st.selectbox("Team", ["All"] + TEAM_CHOICES, index=0, key="record_team")
    names = [p.get("name","") for p in data.get("players", []) if (team_sel == "All" or p.get("team","") == team_sel)]
    if not names:
        st.info("Add players in the Roster tab first, or adjust team filter.")
    else:
        default_idx = 0
        if "selected_player" in st.session_state and st.session_state["selected_player"] in names:
            default_idx = names.index(st.session_state["selected_player"])
        sel = st.selectbox("Player", names, index=default_idx, key="sel_record")

        player = next(p for p in data["players"] if p.get("name","") == sel)
        res = player.setdefault("results", [])
        evald_before = evaluate_adjustments(res); last_window = evald_before["last_window"]

        cA, cB, cC, cD = st.columns(4)
        cA.metric("Season Start HC", int(player.get("start_hc",0)))
        cB.metric("Current HC", current_handicap(int(player.get("start_hc",0)), res))
        cC.metric("Games", f"{len(res)}/{MAX_GAMES}")
        wins = res.count("W"); losses = res.count("L")
        cD.metric("W-L", f"{wins}-{losses}")

        st.markdown("**Timeline**")
        st.markdown(chip_html(res, last_window), unsafe_allow_html=True)

        b1, b2, b3 = st.columns(3)
        if b1.button("✅ Add Win (W)", disabled=not admin_unlocked(), key="btn_add_win"):
            if len(res) < MAX_GAMES:
                res.append("W"); save_and_sync(True); st.rerun()
            else:
                st.warning("Max 28 games reached.")
        if b2.button("❌ Add Loss (L)", disabled=not admin_unlocked(), key="btn_add_loss"):
            if len(res) < MAX_GAMES:
                res.append("L"); save_and_sync(True); st.rerun()
            else:
                st.warning("Max 28 games reached.")
        if b3.button("↩️ Undo last game", disabled=not admin_unlocked(), key="btn_undo"):
            if res:
                res.pop(); save_and_sync(True); st.info("Undid last game"); st.rerun()

with tab_player:
    team_sel_p = st.selectbox("Team", ["All"] + TEAM_CHOICES, index=0, key="player_team")
    names = [p.get("name","") for p in data.get("players", []) if (team_sel_p == "All" or p.get("team","") == team_sel_p)]
    if not names:
        st.info("Add players first or change team filter.")
    else:
        default_idx = 0
        if "selected_player" in st.session_state and st.session_state["selected_player"] in names:
            default_idx = names.index(st.session_state["selected_player"])
        sel = st.selectbox("Select player", names, key="player_detail", index=default_idx)
        player = next(p for p in data["players"] if p.get("name","") == sel)

        st.header(f"{sel}  ·  {player.get('team','')}")
        start_hc_val = int(player.get("start_hc", 0)); res = player.get("results", [])
        evald = evaluate_adjustments(res)
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Season Start HC", start_hc_val)
        m2.metric("Current HC", current_handicap(start_hc_val, res))
        m3.metric("Games", f"{len(res)}/{MAX_GAMES}")
        win_pct = (res.count("W")/len(res)*100) if res else 0.0
        m4.metric("Win %", f"{win_pct:.1f}%")

        st.markdown("#### Timeline")
        st.markdown(chip_html(res, evald["last_window"]), unsafe_allow_html=True)

        rows = []; adjs = evald["adjustments"]; adj_map = {e["game_index"]: e["change"] for e in adjs}
        cur_hc = start_hc_val
        for i, r in enumerate(res):
            change = adj_map.get(i, 0); cur_hc += change
            rows.append({"Game #": i+1, "Result": r, "Adj": change, "HC After": cur_hc})
        dfp = pd.DataFrame(rows)
        if not dfp.empty:
            st.dataframe(dfp, width="stretch")
        else:
            st.caption("No games yet.")

with tab_summary:
    st.subheader("Summary")
    selected_teams_sum = st.multiselect("Filter by team", TEAM_CHOICES, default=TEAM_CHOICES, key="summary_team_filter")
    df = roster_df(data)
    if df.empty:
        st.caption("Add players to see summary.")
    else:
        df = df[df["Team"].isin(selected_teams_sum)]
        # quick stats
        st.markdown("#### Quick stats")
        colA, colB, colC = st.columns(3)
        df_ = df.copy()
        df_["Win %"] = (df_["Wins"]/df_["Games"]).fillna(0)
        top_win = df_.sort_values("Win %", ascending=False).head(1)
        biggest_cut = df.sort_values("Net Change").head(1)  # most negative
        biggest_increase = df.sort_values("Net Change", ascending=False).head(1)
        colA.write("Best Win %"); colA.dataframe(top_win[["Player","Team","Wins","Losses"]], width="stretch")
        colB.write("Biggest Cut"); colB.dataframe(biggest_cut[["Player","Team","Net Change"]], width="stretch")
        colC.write("Biggest Increase"); colC.dataframe(biggest_increase[["Player","Team","Net Change"]], width="stretch")

        st.markdown("#### Table")
        mode = st.radio("Sort by", ["Player","Team","Current HC","Cuts","Increases","Games"], horizontal=True, key="summary_sort")
        df = df.sort_values(mode)
        st.dataframe(df, width="stretch")

with tab_fixtures:
    st.subheader("Fixtures")
    labels = [f"Week {f['week']} — {f['date']}" for f in FIXTURES]
    label_to_fixture = {f"Week {f['week']} — {f['date']}": f for f in FIXTURES}
    choice = st.selectbox("Select week", labels, index=0)
    fx = label_to_fixture[choice]
    st.markdown(f"### {choice}")
    show = pd.DataFrame({"Match #": [1,2,3,4], "Fixture": fx["matches"]})
    st.dataframe(show, width="stretch")

# ---------------- League tab (frames-as-points with confirmations) ----------------
with tab_league:
    st.subheader("League — Frames-as-Points")
    league_results = _init_league_results(data)

    labels = [f"Week {f['week']} — {f['date']}" for f in FIXTURES]
    label_to_week = {lab: f["week"] for lab, f in zip(labels, FIXTURES)}
    choice = st.selectbox("Select week to edit", labels, index=0, key="lg_week_combined")
    week = label_to_week[choice]
    fx = _fixture_week(week)

    # Seed week if missing
    existing = league_results.get(week, [])
    if not existing:
        seeded = []
        for s in fx["matches"]:
            h, a = _parse_match(s)
            seeded.append({"home": h, "away": a, "hf": None, "af": None})
        league_results[week] = seeded

    # Input rows
    valid_all = True
    for i, m in enumerate(league_results[week]):
        st.markdown(f"**Match {i+1}: {m['home']} vs {m['away']}**")
        c1, c2 = st.columns(2)
        with c1:
            hf = st.number_input(f"{m['home']} frames", min_value=0, max_value=4, value=(m["hf"] if m["hf"] is not None else 0), key=f"lg_hf_{week}_{i}", step=1)
        with c2:
            af = st.number_input(f"{m['away']} frames", min_value=0, max_value=4, value=(m["af"] if m["af"] is not None else 0), key=f"lg_af_{week}_{i}", step=1)

        total = int(hf) + int(af)
        if total != 4:
            st.error("Total frames must be 4 (valid results: 4–0, 3–1, 2–2, 1–3, 0–4).")
            valid_all = False
        else:
            st.caption(f"Result: **{m['home']} {int(hf)}–{int(af)} {m['away']}**")
        m["hf"], m["af"] = int(hf), int(af)
        st.divider()

    csave, cclear = st.columns([1,1])
    confirm_save = csave.checkbox("Confirm save", key=f"lg_confirm_save_{week}")
    if csave.button("💾 Save week results", disabled=(not admin_unlocked()) or (not valid_all) or (not confirm_save), key=f"lg_save_{week}"):
        save_and_sync(True); st.success("Week saved."); st.rerun()

    confirm_clear = cclear.checkbox("Confirm clear", key=f"lg_confirm_clear_{week}")
    if cclear.button("🗑 Clear week results", disabled=(not admin_unlocked()) or (not confirm_clear), key=f"lg_clear_{week}"):
        reset = []
        for s in fx["matches"]:
            h, a = _parse_match(s)
            reset.append({"home": h, "away": a, "hf": None, "af": None})
        league_results[week] = reset
        save_and_sync(True)
        st.warning("Week cleared.")
        st.rerun()

    st.markdown("### League Table")
    df_table = _compute_league_table(data)
    st.dataframe(df_table, width="stretch")

with tab_import:
    st.subheader("Import / Export")
    st.download_button("⬇️ Download JSON backup", data=json.dumps(get_data(), indent=2), file_name="league_backup.json", mime="application/json", key="dl_json")
    df = roster_df(data)
    st.download_button("⬇️ Download Summary CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="summary.csv", mime="text/csv", key="dl_csv")

    st.markdown("#### Import JSON")
    inline_unlock("import")
    up = st.file_uploader("Choose a JSON backup exported from this app", type=["json"], accept_multiple_files=False, key="upload_json")
    if up and admin_unlocked():
        try:
            payload = json.load(up)
            if isinstance(payload, dict):
                # basic shape fixups
                payload.setdefault("players", [])
                payload.setdefault("announcement", "")
                payload.setdefault("announcements", [])
                payload.setdefault("league_results", {})
                for p in payload["players"]:
                    p.setdefault("team","")
                st.success("File parsed. Click 'Apply Import' to overwrite current data.")
                if st.button("Apply Import", key="btn_apply_import"):
                    st.session_state["data"] = payload
                    save_and_sync(True)
                    st.success("Import applied.")
                    st.rerun()
            else:
                st.error("Invalid file: top-level JSON must be an object.")
        except Exception as e:
            st.error(f"Failed to parse JSON: {e}")

with tab_help:
    st.subheader("About & Help")
    st.markdown("""
**What is this?**  
Snooker handicap tracker for the **Belfast District Snooker League**. Handicaps adjust in a **rolling 4-game window**:  
- **Cut -7** if a player wins **3 or 4** of the last 4.  
- **Increase +7** if a player loses **3 or 4** of the last 4.  
- **No change** at 2–2.  
Once adjusted, the next possible change is after a **minimum of 4 more games**. Max games per player: **28**.

**Tabs**  
- **Roster**: manage players (name, start handicap, team). Search and filter by team.  
- **Record**: add W/L per player; timeline highlights the last 4-game window that triggered a change.  
- **Player**: detailed stats per player.  
- **Summary**: overview table + quick stats.  
- **Fixtures**: published league fixtures by week.  
- **League**: enter weekly **team results** where **frames = points** (e.g., 3–1 ⇒ 3 pts / 1 pt). Auto league table.  
- **Import/Export**: backup and restore data.  

**Admin PIN**  
Add `ADMIN_PIN` in Streamlit secrets to restrict editing. Unlock via the sidebar to enable save/clear/delete actions.
""")
