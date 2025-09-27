import streamlit as st
import pandas as pd

# Demo fixtures
FIXTURES = [
    {"week": 1, "date": "18/09/2025", "matches": [
        "Team A v Team B", "Team C v Team D", "Team E v Team F", "Team G v Team H"
    ]}
]

def _all_teams_from_fixtures():
    teams = set()
    for f in FIXTURES:
        for m in f["matches"]:
            if " v " in m:
                h, a = m.split(" v ", 1)
                teams.add(h.strip()); teams.add(a.strip())
    return sorted(teams)

def _parse_match(s: str):
    h, a = s.split(" v ", 1)
    return h.strip(), a.strip()

def _fixture_week(week: int):
    for f in FIXTURES:
        if f["week"] == week:
            return f
    return None

def _compute_league_table(data: dict) -> pd.DataFrame:
    teams = _all_teams_from_fixtures()
    rows = {t: {"Team": t, "Played": 0, "Points": 0, "Games For": 0, "Games Against": 0} for t in teams}

    lres = data.get("league_results", {})
    for week, matches in lres.items():
        for m in matches:
            h, a, hf, af = m["home"], m["away"], int(m["hf"]), int(m["af"])
            rows[h]["Played"] += 1
            rows[a]["Played"] += 1
            rows[h]["Games For"] += hf
            rows[h]["Games Against"] += af
            rows[a]["Games For"] += af
            rows[a]["Games Against"] += hf
            rows[h]["Points"] += hf
            rows[a]["Points"] += af

    df = pd.DataFrame(rows.values())
    if not df.empty:
        df["Game Diff"] = df["Games For"] - df["Games Against"]
        df = df.sort_values(["Points", "Game Diff", "Games For"], ascending=[False, False, False]).reset_index(drop=True)
        df.index = df.index + 1
        df.insert(0, "Pos", df.index)
    else:
        df = pd.DataFrame(columns=["Pos","Team","Played","Points","Games For","Games Against","Game Diff"])
    return df

# ---------------- UI ----------------
st.title("League results")

data = {"league_results": {1:[{"home":"Team A","away":"Team B","hf":3,"af":1},
                              {"home":"Team C","away":"Team D","hf":2,"af":2},
                              {"home":"Team E","away":"Team F","hf":4,"af":0},
                              {"home":"Team G","away":"Team H","hf":1,"af":3}]}
       }

week = 1
fx = _fixture_week(week)
st.subheader(f"Week {week} — {fx['date']}")

for i, m in enumerate(data["league_results"][week]):
    st.write(f"Match {i+1}: {m['home']} {m['hf']}–{m['af']} {m['away']}")

st.markdown("### League Table")
df_table = _compute_league_table(data)
st.dataframe(df_table, width="stretch")
