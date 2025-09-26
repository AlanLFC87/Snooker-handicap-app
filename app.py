
import json
import os
from typing import List, Dict, Any
import streamlit as st
import pandas as pd
import requests

MAX_GAMES = 28
LOCAL_DATA_PATH = "app_data/league.json"

# ------------------------ Persistence Layer ------------------------

def _gist_headers():
    token = st.secrets.get("GITHUB_TOKEN", None)
    if not token:
        return None
    return {"Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"}

def _gist_url():
    gist_id = st.secrets.get("GIST_ID", None)
    if not gist_id:
        return None
    return f"https://api.github.com/gists/{gist_id}"

def _load_from_gist():
    url = _gist_url()
    headers = _gist_headers()
    if not url or not headers:
        return None
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        files = data.get("files", {})
        for fname, meta in files.items():
            if fname.lower() == "league.json":
                content = meta.get("content", "{}")
                payload = json.loads(content or "{}")
                # Ensure structure
                if not isinstance(payload, dict) or "players" not in payload or not isinstance(payload["players"], list):
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
            if not isinstance(payload, dict) or "players" not in payload or not isinstance(payload["players"], list):
                payload = {"players": []}
            return payload
        except Exception:
            pass
    return {"players": []}

def save_data(data: Dict[str, Any]) -> None:
    ok = _save_to_gist(data)
    if not ok:
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
        if i < 3:
            continue
        if i <= lock_until:
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
            "Cuts": sum(1 for e in evaluate_adjustments(res)["adjustments"] if e["change"] == -7) if isinstance(res, list) else 0,
            "Increases": sum(1 for e in evaluate_adjustments(res)["adjustments"] if e["change"] == +7) if isinstance(res, list) else 0,
            "Net Change": cur - int(p.get("start_hc", 0)),
        })
    cols = ["Player","Season Start HC","Current HC","Games","Wins","Losses","Cuts","Increases","Net Change"]
    if not rows:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(rows)
    # Make sure column exists before sort
    if "Player" in df.columns:
        df = df.sort_values(["Player"])
    return df.reset_index(drop=True)

# ------------------------ Streamlit UI ------------------------

st.set_page_config(page_title="Handicap Tracker", layout="wide")
st.title("Snooker Handicap Tracker")

if st.secrets.get("GITHUB_TOKEN") and st.secrets.get("GIST_ID"):
    st.caption("Storage: GitHub Gist (configured).")
else:
    st.caption("Storage: Local file (for local runs). Configure Streamlit Secrets for cloud persistence.")

data = load_data()

tab_roster, tab_record, tab_player, tab_summary, tab_import = st.tabs(
    ["Roster", "Record Result", "Player Detail", "Summary", "Import/Export"]
)

with tab_roster:
    st.subheader("Players")
    df = roster_df(data)
    if df.empty:
        st.info("No players yet. Add your first player below.")
    else:
        st.dataframe(df, use_container_width=True)

    with st.expander("Add / Update Player", expanded=True if df.empty else False):
        c1, c2, c3 = st.columns([2,1,1])
        name = c1.text_input("Player name")
        start_hc = c2.number_input("Season Starting Handicap (multiples of 7)", step=7, value=0)
        if c3.button("Save Player", use_container_width=True):
            if name.strip():
                upsert_player(data, name.strip(), int(start_hc))
                save_data(data)
                st.success(f"Saved {name}")
            else:
                st.warning("Enter a name.")

    with st.expander("Remove Player"):
        pnames = [p.get("name","") for p in data.get("players", [])]
        if pnames:
            to_del = st.selectbox("Select player to remove", pnames)
            if st.button("Delete Player"):
                delete_player(data, to_del)
                save_data(data)
                st.warning(f"Deleted {to_del}")
        else:
            st.caption("No players to remove yet.")

with tab_record:
    st.subheader("Record W/L")
    pnames = [p.get("name","") for p in data.get("players", [])]
    if not pnames:
        st.info("Add players in the Roster tab first.")
    else:
        sel = st.selectbox("Player", pnames)
        player = next(p for p in data["players"] if p.get("name","") == sel)

        st.write(f"Season Start HC: **{int(player.get('start_hc',0))}**")
        st.write(f"Current HC: **{current_handicap(int(player.get('start_hc',0)), player.get('results', []))}**")
        st.write(f"Games played: **{len(player.get('results', []))}/{MAX_GAMES}**")

        cA, cB, cC = st.columns(3)
        if cA.button("Add Win (W)"):
            player.setdefault("results", [])
            if len(player["results"]) < MAX_GAMES:
                player["results"].append("W")
                save_data(data)
                st.success("Recorded W")
            else:
                st.warning("Max 28 games reached.")
        if cB.button("Add Loss (L)"):
            player.setdefault("results", [])
            if len(player["results"]) < MAX_GAMES:
                player["results"].append("L")
                save_data(data)
                st.success("Recorded L")
            else:
                st.warning("Max 28 games reached.")
        if cC.button("Undo last game"):
            if player.get("results"):
                player["results"].pop()
                save_data(data)
                st.info("Undid last game")

        details = evaluate_adjustments(player.get("results", []))
        last_win = details["last_window"]
        if player.get("results"):
            st.write("Results timeline (most recent right):")
            chips = []
            for idx, r in enumerate(player["results"]):
                if last_win and last_win[0] <= idx <= last_win[1]:
                    chips.append(f":white_check_mark: **{r}**" if r=="W" else f":x: **{r}**")
                else:
                    chips.append(r)
            st.write(" ".join(chips))

with tab_player:
    pnames = [p.get("name","") for p in data.get("players", [])]
    if not pnames:
        st.info("Add players first.")
    else:
        sel = st.selectbox("Select player", pnames, key="player_detail")
        player = next(p for p in data["players"] if p.get("name","") == sel)

        st.header(sel)
        start_hc_val = int(player.get("start_hc", 0))
        st.write(f"Season Start HC: **{start_hc_val}**")
        st.write(f"Current HC: **{current_handicap(start_hc_val, player.get('results', []))}**")

        rows = []
        res = player.get("results", [])
        evald = evaluate_adjustments(res)
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

with tab_summary:
    st.subheader("Summary")
    df = roster_df(data)
    if df.empty:
        st.caption("Add players to see summary.")
    else:
        df["Win %"] = (df["Wins"] / df["Games"]).fillna(0).round(3)
        st.dataframe(df, use_container_width=True)

with tab_import:
    st.subheader("Seed players from CSV")
    st.caption("Paste rows like:  Name, StartHC  (one per line). Example:  John Smith, -14")
    txt = st.text_area("CSV input", height=150)
    if st.button("Import List"):
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
    st.divider()
    st.subheader("Export / Backup")
    st.download_button("Download JSON backup", data=json.dumps(load_data(), indent=2), file_name="league_backup.json", mime="application/json")
    df = roster_df(data)
    st.download_button("Download Summary CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="summary.csv", mime="text/csv")
