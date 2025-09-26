
import json
import os
from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

LEAGUE_NAME = "Belfast District Snooker League"
MAX_GAMES = 28
LOCAL_DATA_PATH = "app_data/league.json"

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
    """Inline unlock with UNIQUE widget keys per tab/section via required suffix."""
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

# ---------------- Persistence (robust) ----------------
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
def upsert_player(data, name: str, start_hc: int):
    for p in data.get("players", []):
        if p.get("name","").lower() == name.lower():
            p["start_hc"] = int(start_hc)
            return
    data["players"].append({"name": name, "start_hc": int(start_hc), "results": [], "adjustments": []})

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
    """Remove highlight by its exact timestamp string; return True if removed."""
    arr = data.get("announcements", [])
    before = len(arr)
    data["announcements"] = [a for a in arr if a.get("ts") != ts_str]
    return len(data["announcements"]) < before

# ---------------- UI ----------------
st.set_page_config(page_title="Handicap Tracker", layout="wide")

with st.sidebar:
    st.markdown("### League")
    st.markdown(f"**{LEAGUE_NAME}**")
    sidebar_admin()
    st.caption(f"Storage: {'Gist' if (_gist_url() and _gist_headers()) else 'Local/Session'}")

init_session_data()
data = get_data()

# CSS fixes & theme polish
st.markdown("""
<style>
/* Keep Streamlit top menu clear */
.block-container {padding-top: 3.75rem; padding-bottom: 2rem; max-width: 1100px;}
.stTabs [role="tablist"] { margin-top: 0.75rem; }
/* Sidebar spacing + prevent overflow on mobile */
section[data-testid="stSidebar"] { padding-top: 0.75rem; overflow:auto; }
section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3, 
section[data-testid="stSidebar"] h4 { margin-bottom: 0.4rem; }
/* Cards and badges */
.card { border: 1px solid #14532d; background: linear-gradient(180deg,#064e3b,#052e22); border-radius: 12px; padding: 12px 14px; margin-bottom: 10px; color: #ecfdf5;}
.card h4 { margin: 0 0 6px 0; }
.sub { opacity: 0.9; font-size: 0.9rem; }
.metric { display:inline-block; margin-right:12px; padding:4px 8px; border-radius:8px; background:#0b3d2e; }
.btn-small button { padding: 0.25rem 0.5rem !important; }
.badge { display:inline-block;margin:2px 4px;padding:4px 10px;border-radius:999px;font-weight:700;background:#0b3d2e;color:#e5e7eb;}
.badge.win { background:#065f46; color:#f0fdf4; }
.badge.loss { background:#7f1d1d; color:#fee2e2; }
/* Touch targets */
button[kind="primary"], button[kind="secondary"] { min-height: 40px; }
div[data-baseweb="select"] { min-height: 40px; }
</style>
""", unsafe_allow_html=True)

tab_home, tab_roster, tab_record, tab_player, tab_summary, tab_import = st.tabs(
    ["🏠 Home", "👥 Roster", "🎯 Record", "🧑 Player", "📊 Summary", "📥 Import/Export"]
)

with tab_home:
    st.markdown(f"## {LEAGUE_NAME}")
    st.caption("Snooker handicap tracker with rolling 4-game adjustments.")
    st.markdown("### 📣 Announcement")
    if admin_unlocked():
        new_msg = st.text_area("Edit announcement (visible to everyone):", value=data.get("announcement",""), height=100, key="ta_announce")
        if st.button("Save Announcement", key="btn_save_announce"):
            data["announcement"] = new_msg.strip()
            save_and_sync(True); st.rerun()
    else:
        msg = data.get("announcement","").strip()
        if msg:
            st.info(msg)
        else:
            st.caption("No announcement yet.")
    st.markdown("### 🌟 Highlights (last 7 days)")
    hs = active_highlights(data)
    if hs:
        for i, h in enumerate(hs[:10]):
            ts = h.get('ts','')
            dt = ts.split('T')[0] if ts else ''
            cols = st.columns([8,2]) if admin_unlocked() else [None]
            text = f"- {h['msg']}  \n  _since {dt}_"
            if admin_unlocked():
                with cols[0]:
                    st.markdown(text)
                with cols[1]:
                    if st.button("Remove", key=f"rm_highlight_{i}", help="Remove this highlight"):
                        if remove_highlight_by_ts(data, ts):
                            save_and_sync(True); st.rerun()
            else:
                st.markdown(text)
    else:
        st.caption("No recent highlights.")
    st.divider()
    st.markdown("### Quick Stats")
    df = roster_df(data)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Players", len(df))
    c2.metric("Games", int(df["Games"].sum()) if not df.empty else 0)
    c3.metric("Cuts (-7)", int(df["Cuts"].sum()) if not df.empty else 0)
    c4.metric("Increases (+7)", int(df["Increases"].sum()) if not df.empty else 0)

with tab_roster:
    st.subheader("Players")
    view = st.radio("View", ["Cards","Table"], horizontal=True, key="roster_view")
    inline_unlock("roster")
    if view == "Cards":
        for p in data.get("players", []):
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
</div>
""", unsafe_allow_html=True)
        # Buttons under cards removed per request.
    else:
        st.dataframe(roster_df(data))

    with st.expander("Add / Update Player", expanded=False):
        c1, c2, c3 = st.columns([2,1,1])
        name = c1.text_input("Name", disabled=not admin_unlocked(), key="name_add")
        hc = c2.number_input("Season Start HC (multiples of 7)", step=7, value=0, disabled=not admin_unlocked(), key="hc_add")
        if c3.button("Save Player", disabled=not admin_unlocked(), key="btn_save_player"):
            if name:
                upsert_player(data, name, int(hc)); save_and_sync(True); st.success("Player saved."); st.rerun()
            else:
                st.warning("Enter a name.")
    with st.expander("Delete Player", expanded=False):
        names = [p.get("name","") for p in data.get("players", [])]
        sel = st.selectbox("Select player to delete", names, disabled=not admin_unlocked(), key="sel_delete")
        if st.button("Delete", disabled=not admin_unlocked(), key="btn_delete") and sel:
            delete_player(data, sel); save_and_sync(True); st.warning(f"Deleted {sel}."); st.rerun()

with tab_record:
    st.subheader("Record W/L")
    inline_unlock("record")
    names = [p.get("name","") for p in data.get("players", [])]
    if not names:
        st.info("Add players in the Roster tab first.")
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
                res.append("W")
                evald_after = evaluate_adjustments(res); save_and_sync(True)
                if evald_after["last_window"] and evald_after["last_window"] != last_window:
                    change = evald_after["delta"] - evald_before["delta"]
                    if change < 0:
                        st.success("Cut applied (-7).")
                        add_highlight_announcement(data, player.get("name",""), -7); save_and_sync(False)
                    elif change > 0:
                        st.warning("Increase applied (+7).")
                        add_highlight_announcement(data, player.get("name",""), +7); save_and_sync(False)
                st.rerun()
            else:
                st.warning("Max 28 games reached.")
        if b2.button("❌ Add Loss (L)", disabled=not admin_unlocked(), key="btn_add_loss"):
            if len(res) < MAX_GAMES:
                res.append("L")
                evald_after = evaluate_adjustments(res); save_and_sync(True)
                if evald_after["last_window"] and evald_after["last_window"] != last_window:
                    change = evald_after["delta"] - evald_before["delta"]
                    if change < 0:
                        st.success("Cut applied (-7).")
                        add_highlight_announcement(data, player.get("name",""), -7); save_and_sync(False)
                    elif change > 0:
                        st.warning("Increase applied (+7).")
                        add_highlight_announcement(data, player.get("name",""), +7); save_and_sync(False)
                st.rerun()
            else:
                st.warning("Max 28 games reached.")
        if b3.button("↩️ Undo last game", disabled=not admin_unlocked(), key="btn_undo"):
            if res:
                res.pop(); save_and_sync(True); st.info("Undid last game"); st.rerun()

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
        df = pd.DataFrame(rows)
        if not df.empty:
            st.dataframe(df)
        else:
            st.caption("No games yet.")

with tab_summary:
    st.subheader("Summary")
    df = roster_df(data)
    if df.empty:
        st.caption("Add players to see summary.")
    else:
        mode = st.radio("Sort by", ["Player","Current HC","Win %","Cuts","Increases","Games"], horizontal=True, key="summary_sort")
        if mode == "Win %":
            df["Win %"] = (df["Wins"] / df["Games"]).fillna(0); df = df.sort_values("Win %", ascending=False); df["Win %"] = (df["Win %"]*100).round(1)
        else:
            df = df.sort_values(mode)
        st.dataframe(df)

with tab_import:
    st.subheader("Seed players from CSV")
    inline_unlock("import")
    st.caption("Paste rows like:  Name, StartHC  (one per line). Example:  John Smith, -14")
    txt = st.text_area("CSV input", height=150, disabled=not admin_unlocked(), key="csv_input")
    if st.button("Import List", disabled=not admin_unlocked(), key="btn_import"):
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
                        try: hc = int(parts[1].replace("+",""))
                        except: continue
                    upsert_player(data, name, hc); added += 1
            save_and_sync(True); st.success(f"Imported {added} players."); st.rerun()
    st.divider()
    st.subheader("Export / Backup")
    st.download_button("Download JSON backup", data=json.dumps(get_data(), indent=2), file_name="league_backup.json", mime="application/json", key="dl_json")
    df = roster_df(data)
    st.download_button("Download Summary CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="summary.csv", mime="text/csv", key="dl_csv")
