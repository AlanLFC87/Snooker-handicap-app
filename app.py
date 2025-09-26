
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
        # Expect a file named league.json in the gist
        for fname, meta in files.items():
            if fname.lower() == "league.json":
                content = meta.get("content", "{}")
                return json.loads(content or "{}")
        return None
    except Exception as e:
        st.warning(f"Gist load failed (falling back to local): {e}")
        return None

def _save_to_gist(payload: Dict[str, Any]) -> bool:
    url = _gist_url()
    headers = _gist_headers()
    if not url or not headers:
        return False
    try:
        body = {
            "files": {
                "league.json": {
                    "content": json.dumps(payload, indent=2)
                }
            }
        }
        r = requests.patch(url, headers=headers, json=body, timeout=15)
        r.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Gist save failed: {e}")
        return False

def load_data() -> Dict[str, Any]:
    # Try Gist first (for Streamlit Cloud), then local file (for local runs)
    data = _load_from_gist()
    if data is not None:
        return data
    if os.path.exists(LOCAL_DATA_PATH):
        with open(LOCAL_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"players": []}

def save_data(data: Dict[str, Any]) -> None:
    # Try to save to Gist; if not configured, save locally
    ok = _save_to_gist(data)
    if not ok:
        os.makedirs(os.path.dirname(LOCAL_DATA_PATH), exist_ok=True)
        with open(LOCAL_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

# ------------------------ Domain Logic ------------------------

def upsert_player(data, name: str, start_hc: int):
    for p in data["players"]:
        if p["name"].lower() == name.lower():
            p["start_hc"] = int(start_hc)
            return
    data["players"].append({
        "name": name,
        "start_hc": int(start_hc),
        "results": [],
        "adjustments": [],
    })

def delete_player(data, name: str):
    data["players"] = [p for p in data["players"] if p["name"].lower() != name.lower()]

def evaluate_adjustments(results: List[str]) -> Dict[str, Any]:
    adj_events = []
    lock_until = -1
    last_window = None
    for i in range(len(results)):
        if i < 3:  # need 4 games
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
    for p in data["players"]:
        res = p.get("results", [])
        cur = current_handicap(p["start_hc"], res)
        rows.append({
            "Player": p["name"],
            "Season Start HC": p["start_hc"],
            "Current HC": cur,
            "Games": len(res),
            "Wins": res.count("W"),
            "Losses": res.count("L"),
            "Cuts": sum(1 for e in evaluate_adjustments(res)["adjustments"] if e["change"] == -7),
            "Increases": sum(1 for e in evaluate_adjustments(res)["adjustments"] if e["change"] == +7),
            "Net Change": cur - p["start_hc"],
        })
    return pd.DataFrame(rows).sort_values(["Player"]).reset_index(drop=True)

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
    st.dataframe(roster_df(data), use_container_width=True)

    with st.expander("Add / Update Player"):
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
        if data["players"]:
            to_del = st.selectbox("Select player to remove", [p["name"] for p in data["players"]])
            if st.button("Delete Player"):
                delete_player(data, to_del)
                save_data(data)
                st.warning(f"Deleted {to_del}")

with tab_record:
    st.subheader("Record W/L")
    if not data["players"]:
        st.info("Add players in the Roster tab first.")
    else:
        pnames = [p["name"] for p in data["players"]]
        sel = st.selectbox("Player", pnames)
        player = next(p for p in data["players"] if p["name"] == sel)

        st.write(f"Season Start HC: **{player['start_hc']}**")
        st.write(f"Current HC: **{current_handicap(player['start_hc'], player['results'])}**")
        st.write(f"Games played: **{len(player['results'])}/{MAX_GAMES}**")

        cA, cB, cC = st.columns(3)
        if cA.button("Add Win (W)"):
            if len(player["results"]) < MAX_GAMES:
                player["results"].append("W")
                save_data(data)
                st.success("Recorded W")
            else:
                st.warning("Max 28 games reached.")
        if cB.button("Add Loss (L)"):
            if len(player["results"]) < MAX_GAMES:
                player["results"].append("L")
                save_data(data)
                st.success("Recorded L")
            else:
                st.warning("Max 28 games reached.")
        if cC.button("Undo last game"):
            if player["results"]:
                player["results"].pop()
                save_data(data)
                st.info("Undid last game")

        details = evaluate_adjustments(player["results"])
        last_win = details["last_window"]
        if player["results"]:
            st.write("Results timeline (most recent right):")
            chips = []
            for idx, r in enumerate(player["results"]):
                if last_win and last_win[0] <= idx <= last_win[1]:
                    chips.append(f":white_check_mark: **{r}**" if r=="W" else f":x: **{r}**")
                else:
                    chips.append(r)
            st.write(" ".join(chips))

with tab_player:
    if not data["players"]:
        st.info("Add players first.")
    else:
        sel = st.selectbox("Select player", [p["name"] for p in data["players"]], key="player_detail")
        player = next(p for p in data["players"] if p["name"] == sel)

        st.header(sel)
        st.write(f"Season Start HC: **{player['start_hc']}**")
        st.write(f"Current HC: **{current_handicap(player['start_hc'], player['results'])}**")

        rows = []
        res = player["results"]
        evald = evaluate_adjustments(res)
        adjs = evald["adjustments"]
        adj_map = {e["game_index"]: e["change"] for e in adjs}

        cur_hc = player["start_hc"]
        for i, r in enumerate(res):
            change = adj_map.get(i, 0)
            cur_hc += change
            rows.append({
                "Game #": i+1,
                "Result": r,
                "Adj": change,
                "HC After": cur_hc
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

with tab_summary:
    st.subheader("Summary")
    df = roster_df(data)
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
    # CSV export for roster summary
    df = roster_df(data)
    st.download_button("Download Summary CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="summary.csv", mime="text/csv")
