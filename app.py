
import json
import os
from typing import List, Dict, Any, Optional
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

# ------------------------ Constants ------------------------
LEAGUE_NAME = "Belfast District Snooker League"
MAX_GAMES = 28
LOCAL_DATA_PATH = "app_data/league.json"

# ------------------------ Health Endpoint ------------------------
if st.query_params.get("health") == "1":
    st.write("OK")
    st.stop()

# ------------------------ Admin PIN ------------------------
def is_admin_enabled() -> bool:
    return bool(st.secrets.get("ADMIN_PIN"))

def admin_unlocked() -> bool:
    return st.session_state.get("is_admin", False)

def admin_gate_ui():
    st.markdown("##### 🔒 Admin")
    if not is_admin_enabled():
        st.caption("Admin PIN not set; editing is open. (Add ADMIN_PIN in Secrets to restrict edits.)")
        st.session_state["is_admin"] = True
        return

    if admin_unlocked():
        st.success("Admin mode unlocked for this session.")
        if st.button("Lock Admin", use_container_width=True):
            st.session_state["is_admin"] = False
            st.rerun()
        return

    pin = st.text_input("Enter admin PIN", type="password")
    if st.button("Unlock", use_container_width=True):
        if pin == st.secrets.get("ADMIN_PIN"):
            st.session_state["is_admin"] = True
            st.success("Admin unlocked.")
            st.rerun()
        else:
            st.error("Incorrect PIN.")

# ------------------------ Persistence (Gist or local) ------------------------
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
            if not isinstance(payload, dict):
                payload = {}
            payload.setdefault("players", [])
            payload.setdefault("announcement", "")
            payload.setdefault("announcements", [])  # auto highlights: [{msg, ts, expires}]
            return payload
        return {"players": [], "announcement": "", "announcements": []}
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
            if not isinstance(payload, dict):
                payload = {}
            payload.setdefault("players", [])
            payload.setdefault("announcement", "")
            payload.setdefault("announcements", [])
            return payload
        except Exception:
            pass
    return {"players": [], "announcement": "", "announcements": []}

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

def evaluate_adjustments(results):
    """Rolling 4, reset after change; re-evaluate at exactly +4 games."""
    adj_events = []
    lock_until = -1
    last_window = None
    for i in range(len(results)):
        if i < 3:
            continue
        if i < lock_until:
            continue
        window = results[i-3:i+1]
        wins = window.count("W")
        losses = window.count("L")
        change = 0
        if wins >= 3:
            change = -7
        elif losses >= 3:
            change = +7
        if change != 0:
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
            "Season Start HC": int(p.get("start_hc", 0)),
            "Current HC": cur,
            "Games": len(res) if isinstance(res, list) else 0,
            "Wins": res.count("W") if isinstance(res, list) else 0,
            "Losses": res.count("L") if isinstance(res, list) else 0,
            "Cuts": sum(1 for e in evaluate_adjustments(res)["adjustments"] if e["change"] == -7) if isinstance(res, list) else 0,
            "Increases": sum(1 for e in evaluate_adjustments(res)["adjustments"] if e["change"] == +7) if isinstance(res, list) else 0,
            "Net Change": cur - int(p.get("start_hc", 0)),
        })
    cols = ["Player","Season Start HC","Current HC","Games","Wins","Losses","Cuts","Increases","Net Change"]
    if not rows:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(rows)
    return df.sort_values(["Player"]).reset_index(drop=True)

def chip_html(results, last_window):
    chips = []
    for idx, r in enumerate(results or []):
        highlighted = last_window and last_window[0] <= idx <= last_window[1]
        base = "display:inline-block;margin:2px 4px;padding:4px 10px;border-radius:999px;font-weight:700;"
        color = "background:#065f46;color:#f0fdf4;" if (highlighted and r == "W") else ("background:#7f1d1d;color:#fee2e2;" if (highlighted and r == "L") else "background:#0b3d2e;color:#e5e7eb;")
        chips.append(f"<span style='{base}{color}'>{r}</span>")
    return " ".join(chips) if chips else "<em>No games yet</em>"

from datetime import datetime, timedelta, timezone

def add_highlight_announcement(data, player_name: str, change: int):
    ts = datetime.now(timezone.utc)
    expires = ts + timedelta(days=7)
    if change < 0:
        msg = f"🏆 {player_name} handicap cut by 7 after strong form."
    else:
        msg = f"📈 {player_name} handicap increased by 7 after recent results."
    data.setdefault("announcements", []).append({
        "msg": msg,
        "ts": ts.isoformat(),
        "expires": expires.isoformat(),
    })

def active_highlights(data):
    out = []
    now = datetime.now(timezone.utc)
    for a in data.get("announcements", []):
        try:
            exp = datetime.fromisoformat(a.get("expires"))
        except Exception:
            continue
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp > now:
            out.append(a)
    out.sort(key=lambda x: x.get("ts",""), reverse=True)
    return out

# ------------------------ Page Setup ------------------------
st.set_page_config(page_title="Handicap Tracker", layout="wide")

# Sidebar admin controls
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Snooker_table.svg/320px-Snooker_table.svg.png", use_column_width=True)
    st.header("League")
    st.subheader(LEAGUE_NAME)
    st.divider()
    admin_gate_ui()

data = load_data()

# Custom CSS for mobile & cards
st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1100px;}
.card {
  border: 1px solid #14532d;
  background: linear-gradient(180deg,#064e3b,#052e22);
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 10px;
  color: #ecfdf5;
}
.card h4 { margin: 0 0 6px 0; }
.sub { opacity: 0.9; font-size: 0.9rem; }
.metric { display:inline-block; margin-right:12px; padding:4px 8px; border-radius:8px; background:#0b3d2e; }
.btn-small button { padding: 0.25rem 0.5rem !important; }
.badge { display:inline-block;margin:2px 4px;padding:4px 10px;border-radius:999px;font-weight:700;background:#0b3d2e;color:#e5e7eb;}
.badge.win { background:#065f46; color:#f0fdf4; }
.badge.loss { background:#7f1d1d; color:#fee2e2; }
</style>
""", unsafe_allow_html=True)

# Tabs
tab_home, tab_roster, tab_record, tab_player, tab_summary, tab_import = st.tabs(
    ["🏠 Home", "👥 Roster", "🎯 Record", "🧑 Player", "📊 Summary", "📥 Import/Export"]
)

# ---- Home ----
with tab_home:
    st.markdown(f"## {LEAGUE_NAME}")
    st.caption("Snooker handicap tracker with rolling 4-game adjustments.")

    # Manual single announcement
    st.markdown("### 📣 Announcement")
    if admin_unlocked():
        new_msg = st.text_area("Edit announcement (visible to everyone):", value=data.get("announcement",""), height=100)
        if st.button("Save Announcement", use_container_width=True):
            data["announcement"] = new_msg.strip()
            save_data(data)
            st.success("Announcement saved.")
            st.rerun()
    else:
        msg = data.get("announcement","").strip()
        if msg:
            st.info(msg)
        else:
            st.caption("No announcement yet.")

    # Auto highlights (last 7 days)
    highlights = active_highlights(data)
    st.markdown("### 🌟 Highlights (last 7 days)")
    if highlights:
        for h in highlights[:10]:
            dt = h.get('ts','').split('T')[0]
            st.markdown(f"- {h['msg']}  \n  _since {dt}_")
    else:
        st.caption("No recent highlights.")

    st.divider()
    st.markdown("### Quick Stats")
    df = roster_df(data)
    total_players = len(df)
    total_games = int(df["Games"].sum()) if not df.empty else 0
    total_cuts = int(df["Cuts"].sum()) if not df.empty else 0
    total_incs = int(df["Increases"].sum()) if not df.empty else 0
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Players", total_players)
    c2.metric("Games", total_games)
    c3.metric("Cuts (-7)", total_cuts)
    c4.metric("Increases (+7)", total_incs)

# ---- Roster (cards) ----
with tab_roster:
    st.subheader("Players")
    view = st.radio("View", ["Cards","Table"], horizontal=True)
    players = data.get("players", [])
    if view == "Cards":
        for p in players:
            res = p.get("results", [])
            cur = current_handicap(int(p.get("start_hc",0)), res)
            wins = res.count("W"); losses = res.count("L")
            st.markdown(f"""
<div class="card">
  <h4>{p.get('name','')}</h4>
  <div class="sub">Start HC: <b>{int(p.get('start_hc',0))}</b> • Current HC: <b>{cur}</b> • Games: <b>{len(res)}/{MAX_GAMES}</b></div>
  <div style="margin:6px 0;">
    <span class="metric">W: {wins}</span> <span class="metric">L: {losses}</span>
  </div>
  <div class="btn-small">
</div></div>
""", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button("🎯 Record", key=f"rec_{p['name']}"):
                st.session_state["selected_player"] = p['name']
                st.session_state["active_tab"] = "record"
                st.rerun()
            if c2.button("📊 Detail", key=f"det_{p['name']}"):
                st.session_state["selected_player"] = p['name']
                st.session_state["active_tab"] = "player"
                st.rerun()
    else:
        st.dataframe(roster_df(data), use_container_width=True)

    with st.expander("Add / Update Player", expanded=False):
        c1, c2, c3 = st.columns([2,1,1])
        name = c1.text_input("Name", disabled=not admin_unlocked())
        hc = c2.number_input("Season Start HC (multiples of 7)", step=7, value=0, disabled=not admin_unlocked())
        if c3.button("Save Player", disabled=not admin_unlocked()):
            if name:
                upsert_player(data, name, int(hc))
                save_data(data)
                st.success("Player saved.")
                st.rerun()
            else:
                st.warning("Enter a name.")

    with st.expander("Delete Player", expanded=False):
        names = [p.get("name","") for p in data.get("players", [])]
        sel = st.selectbox("Select player to delete", names, disabled=not admin_unlocked())
        if st.button("Delete", disabled=not admin_unlocked()) and sel:
            delete_player(data, sel)
            save_data(data)
            st.warning(f"Deleted {sel}.")
            st.rerun()

# ---- Record ----
with tab_record:
    st.subheader("Record W/L")
    names = [p.get("name","") for p in data.get("players", [])]
    if not names:
        st.info("Add players in the Roster tab first.")
    else:
        default_idx = 0
        if "selected_player" in st.session_state and st.session_state["selected_player"] in names:
            default_idx = names.index(st.session_state["selected_player"])
        sel = st.selectbox("Player", names, index=default_idx)

        player = next(p for p in data["players"] if p.get("name","") == sel)
        res = player.setdefault("results", [])
        evald_before = evaluate_adjustments(res)
        last_window = evald_before["last_window"]

        cA, cB, cC, cD = st.columns(4)
        cA.metric("Season Start HC", int(player.get("start_hc",0)))
        cB.metric("Current HC", current_handicap(int(player.get("start_hc",0)), res))
        cC.metric("Games", f"{len(res)}/{MAX_GAMES}")
        wins = res.count("W"); losses = res.count("L")
        cD.metric("W-L", f"{wins}-{losses}")

        st.markdown("**Timeline**")
        st.markdown(chip_html(res, last_window), unsafe_allow_html=True)

        b1, b2, b3 = st.columns(3)
        if b1.button("✅ Add Win (W)", disabled=not admin_unlocked()):
            if len(res) < MAX_GAMES:
                res.append("W")
                evald_after = evaluate_adjustments(res)
                save_data(data)
                if evald_after["last_window"] and evald_after["last_window"] != last_window:
                    change = evald_after["delta"] - evald_before["delta"]
                    if change < 0:
                        st.success("Cut applied (-7).")
                        add_highlight_announcement(data, player.get("name",""), -7)
                        save_data(data)
                    elif change > 0:
                        st.warning("Increase applied (+7).")
                        add_highlight_announcement(data, player.get("name",""), +7)
                        save_data(data)
                st.rerun()
            else:
                st.warning("Max 28 games reached.")
        if b2.button("❌ Add Loss (L)", disabled=not admin_unlocked()):
            if len(res) < MAX_GAMES:
                res.append("L")
                evald_after = evaluate_adjustments(res)
                save_data(data)
                if evald_after["last_window"] and evald_after["last_window"] != last_window:
                    change = evald_after["delta"] - evald_before["delta"]
                    if change < 0:
                        st.success("Cut applied (-7).")
                        add_highlight_announcement(data, player.get("name",""), -7)
                        save_data(data)
                    elif change > 0:
                        st.warning("Increase applied (+7).")
                        add_highlight_announcement(data, player.get("name",""), +7)
                        save_data(data)
                st.rerun()
            else:
                st.warning("Max 28 games reached.")
        if b3.button("↩️ Undo last game", disabled=not admin_unlocked()):
            if res:
                res.pop()
                save_data(data)
                st.info("Undid last game")
                st.rerun()

# ---- Player Detail ----
with tab_player:
    names = [p.get("name","") for p in data.get("players", [])]
    if not names:
        st.info("Add players first.")
    else:
        default_idx = 0
        if "selected_player" in st.session_state and st.session_state["selected_player"] in names:
            default_idx = names.index(st.session_state["selected_player"])
        sel = st.selectbox("Select player", names, key="player_detail", index=default_idx)
        player = next(p for p in data["players"] if p.get("name","") == sel)

        st.header(sel)
        start_hc_val = int(player.get("start_hc", 0))
        res = player.get("results", [])
        evald = evaluate_adjustments(res)
        st.markdown("#### Key Metrics")
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Season Start HC", start_hc_val)
        m2.metric("Current HC", current_handicap(start_hc_val, res))
        m3.metric("Games", f"{len(res)}/{MAX_GAMES}")
        win_pct = (res.count("W")/len(res)*100) if res else 0.0
        m4.metric("Win %", f"{win_pct:.1f}%")

        st.markdown("#### Timeline")
        st.markdown(chip_html(res, evald["last_window"]), unsafe_allow_html=True)

        rows = []
        adjs = evald["adjustments"]
        adj_map = {e["game_index"]: e["change"] for e in adjs}
        cur_hc = start_hc_val
        for i, r in enumerate(res):
            change = adj_map.get(i, 0)
            cur_hc += change
            rows.append({"Game #": i+1, "Result": r, "Adj": change, "HC After": cur_hc})
        df = pd.DataFrame(rows)
        if df.empty:
            st.caption("No games yet.")
        else:
            st.dataframe(df, use_container_width=True)

# ---- Summary ----
with tab_summary:
    st.subheader("Summary")
    df = roster_df(data)
    if df.empty:
        st.caption("Add players to see summary.")
    else:
        mode = st.radio("Sort by", ["Player","Current HC","Win %","Cuts","Increases","Games"], horizontal=True)
        if mode == "Win %":
            df["Win %"] = (df["Wins"] / df["Games"]).fillna(0)
            df = df.sort_values("Win %", ascending=False)
            df["Win %"] = (df["Win %"]*100).round(1)
        else:
            df = df.sort_values(mode)
        st.dataframe(df, use_container_width=True)

# ---- Import / Export ----
with tab_import:
    st.subheader("Seed players from CSV")
    st.caption("Paste rows like:  Name, StartHC  (one per line). Example:  John Smith, -14")
    txt = st.text_area("CSV input", height=150, disabled=not admin_unlocked())
    if st.button("Import List", disabled=not admin_unlocked()):
        if txt.strip():
            lines = [ln.strip() for ln in txt.strip().splitlines() if ln.strip()] 
            added = 0
            for ln in lines:
                parts = [p.strip() for p in ln.split(",")]
                if len(parts) >= 2:
                    name = parts[0]
                    try:
                        hc = int(parts[1])
                    except:
                        try:
                            hc = int(parts[1].replace("+",""))
                        except:
                            continue
                    upsert_player(data, name, hc)
                    added += 1
            save_data(data)
            st.success(f"Imported {added} players.")
            st.rerun()
    st.divider()
    st.subheader("Export / Backup")
    st.download_button("Download JSON backup", data=json.dumps(load_data(), indent=2), file_name="league_backup.json", mime="application/json")
    df = roster_df(data)
    st.download_button("Download Summary CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="summary.csv", mime="text/csv")
