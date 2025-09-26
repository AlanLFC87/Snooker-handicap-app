# Snooker Handicap Tracker with Teams, Highlights, Announcements, and PIN
import streamlit as st, pandas as pd, requests, json

# ---------------- Config ----------------
LEAGUE_NAME = "Belfast District Snooker League"
DATA_URL = st.secrets.get("DATA_URL","")
GIST_TOKEN = st.secrets.get("GIST_TOKEN","")
ADMIN_PIN = st.secrets.get("ADMIN_PIN","1234")

TEAMS = [
    "Ballygomartin A","Ballygomartin B","Ballygomartin C","East",
    "Premier","QE2 A","QE2 B","Shorts"
]

# ---------------- Fixtures (from 2025/26 images) ----------------
FIXTURES = [
    {"week":1,"date":"2025-09-18","matches":[
        ("Ballygomartin B","Ballygomartin A"),
        ("QE2 A","QE2 B"),
        ("Shorts","Ballygomartin C"),
        ("East","Premier")
    ]},
    {"week":2,"date":"2025-09-25","matches":[
        ("QE2 A","Ballygomartin B"),
        ("Ballygomartin A","QE2 B"),
        ("East","Shorts"),
        ("Premier","Ballygomartin C")
    ]},
    {"week":3,"date":"2025-10-02","matches":[
        ("Ballygomartin B","QE2 B"),
        ("QE2 A","Ballygomartin A"),
        ("Premier","Shorts"),
        ("Ballygomartin C","East")
    ]},
    {"week":4,"date":"2025-10-09","matches":[
        ("Shorts","Ballygomartin B"),
        ("Ballygomartin A","Ballygomartin C"),
        ("East","QE2 A"),
        ("QE2 B","Premier")
    ]},
    {"week":5,"date":"2025-10-16","matches":[
        ("Ballygomartin C","Ballygomartin B"),
        ("East","Ballygomartin A"),
        ("QE2 A","Premier"),
        ("Shorts","QE2 B")
    ]},
    {"week":6,"date":"2025-10-23","matches":[
        ("Ballygomartin B","East"),
        ("Premier","Ballygomartin A"),
        ("Shorts","QE2 A"),
        ("Ballygomartin C","QE2 B")
    ]},
    {"week":7,"date":"2025-10-30","matches":[
        ("Premier","Ballygomartin B"),
        ("Ballygomartin A","Shorts"),
        ("Ballygomartin C","QE2 A"),
        ("QE2 B","East")
    ]},
    {"week":8,"date":"2025-11-06","matches":[
        ("Ballygomartin A","Ballygomartin B"),
        ("QE2 B","QE2 A"),
        ("Ballygomartin C","Shorts"),
        ("Premier","East")
    ]},
    {"week":9,"date":"2025-11-13","matches":[
        ("Ballygomartin B","QE2 A"),
        ("QE2 B","Ballygomartin A"),
        ("Shorts","East"),
        ("Ballygomartin C","Premier")
    ]},
    {"week":10,"date":"2025-11-20","matches":[
        ("QE2 B","Ballygomartin B"),
        ("Ballygomartin A","QE2 A"),
        ("Shorts","Premier"),
        ("East","Ballygomartin C")
    ]},
    {"week":11,"date":"2025-11-27","matches":[
        ("Ballygomartin B","Shorts"),
        ("Ballygomartin C","Ballygomartin A"),
        ("QE2 A","East"),
        ("Premier","QE2 B")
    ]},
    {"week":12,"date":"2025-12-04","matches":[
        ("Ballygomartin B","Ballygomartin C"),
        ("Ballygomartin A","East"),
        ("Premier","QE2 A"),
        ("QE2 B","Shorts")
    ]},
    {"week":13,"date":"2025-12-11","matches":[
        ("East","Ballygomartin B"),
        ("Ballygomartin A","Premier"),
        ("QE2 A","Shorts"),
        ("QE2 B","Ballygomartin C")
    ]},
    {"week":14,"date":"2025-12-18","matches":[
        ("Ballygomartin B","Premier"),
        ("Shorts","Ballygomartin A"),
        ("QE2 A","Ballygomartin C"),
        ("East","QE2 B")
    ]},
    {"week":15,"date":"2026-02-05","matches":[
        ("Ballygomartin B","Ballygomartin A"),
        ("QE2 A","QE2 B"),
        ("Shorts","Ballygomartin C"),
        ("East","Premier")
    ]},
    {"week":16,"date":"2026-02-12","matches":[
        ("QE2 A","Ballygomartin B"),
        ("Ballygomartin A","QE2 B"),
        ("East","Shorts"),
        ("Premier","Ballygomartin C")
    ]},
    {"week":17,"date":"2026-02-19","matches":[
        ("Ballygomartin B","QE2 B"),
        ("QE2 A","Ballygomartin A"),
        ("Premier","Shorts"),
        ("Ballygomartin C","East")
    ]},
    {"week":18,"date":"2026-02-26","matches":[
        ("Shorts","Ballygomartin B"),
        ("Ballygomartin A","Ballygomartin C"),
        ("East","QE2 A"),
        ("QE2 B","Premier")
    ]},
    {"week":19,"date":"2026-03-05","matches":[
        ("Ballygomartin C","Ballygomartin B"),
        ("East","Ballygomartin A"),
        ("QE2 A","Premier"),
        ("Shorts","QE2 B")
    ]},
    {"week":20,"date":"2026-03-12","matches":[
        ("Ballygomartin B","East"),
        ("Premier","Ballygomartin A"),
        ("Shorts","QE2 A"),
        ("Ballygomartin C","QE2 B")
    ]},
    {"week":21,"date":"2026-03-19","matches":[
        ("Premier","Ballygomartin B"),
        ("Ballygomartin A","Shorts"),
        ("Ballygomartin C","QE2 A"),
        ("QE2 B","East")
    ]},
    {"week":22,"date":"2026-03-26","matches":[
        ("Ballygomartin A","Ballygomartin B"),
        ("QE2 B","QE2 A"),
        ("Ballygomartin C","Shorts"),
        ("Premier","East")
    ]},
    {"week":23,"date":"2026-04-02","matches":[
        ("Ballygomartin B","QE2 A"),
        ("QE2 B","Ballygomartin A"),
        ("Shorts","East"),
        ("Ballygomartin C","Premier")
    ]},
    {"week":24,"date":"2026-04-09","matches":[
        ("QE2 B","Ballygomartin B"),
        ("Ballygomartin A","QE2 A"),
        ("Shorts","Premier"),
        ("East","Ballygomartin C")
    ]},
    {"week":25,"date":"2026-04-16","matches":[
        ("Ballygomartin B","Shorts"),
        ("Ballygomartin C","Ballygomartin A"),
        ("QE2 A","East"),
        ("Premier","QE2 B")
    ]},
    {"week":26,"date":"2026-04-23","matches":[
        ("Ballygomartin B","Ballygomartin C"),
        ("Ballygomartin A","East"),
        ("Premier","QE2 A"),
        ("QE2 B","Shorts")
    ]},
    {"week":27,"date":"2026-04-30","matches":[
        ("East","Ballygomartin B"),
        ("Ballygomartin A","Premier"),
        ("QE2 A","Shorts"),
        ("QE2 B","Ballygomartin C")
    ]},
    {"week":28,"date":"2026-05-07","matches":[
        ("Ballygomartin B","Premier"),
        ("Shorts","Ballygomartin A"),
        ("QE2 A","Ballygomartin C"),
        ("East","QE2 B")
    ]},
]

# ---------------- Data helpers ----------------
def load_data():
    try:
        r = requests.get(DATA_URL)
        if r.status_code==200:
            return r.json()
    except Exception as e:
        st.error(f"Load error: {e}")
    return {"players":[],"highlights":[],"announcement":""}

def save_data(data):
    if not DATA_URL or not GIST_TOKEN: return
    try:
        gist_id = DATA_URL.split("/")[-1]
        headers={"Authorization":f"token {GIST_TOKEN}"}
        requests.patch(f"https://api.github.com/gists/{gist_id}",
                       headers=headers,json={"files":{"data.json":{"content":json.dumps(data)}}})
    except Exception as e:
        st.error(f"Save error: {e}")

data = load_data()

# ---------------- Unlock ----------------
if "unlocked" not in st.session_state: st.session_state.unlocked=False
def inline_unlock(label="PIN"):
    if not st.session_state.unlocked:
        c1,c2 = st.columns([3,1])
        with c1:
            pin=st.text_input(label,type="password",key=f"pin_{label}")
        with c2:
            if st.button("Unlock",key=f"unlock_{label}"):
                if pin==ADMIN_PIN: st.session_state.unlocked=True
                else: st.error("Wrong PIN")

# ---------------- Tabs ----------------
tab_home, tab_roster, tab_record, tab_fix, tab_ann = st.tabs(["🏠 Home","👥 Roster","✍️ Record","📅 Fixtures","📢 Announcements"])

# ---------------- Home ----------------
with tab_home:
    st.title(LEAGUE_NAME)
    st.header("Announcements")
    msg=data.get("announcement","").strip()
    if msg: st.success(msg)
    else: st.caption("No announcements.")
    st.header("Recent Highlights")
    highs=data.get("highlights",[])[:5]
    if highs:
        for h in highs:
            st.info(h)
    else: st.caption("No highlights yet.")

# ---------------- Roster ----------------
with tab_roster:
    st.subheader("Players")
    df=pd.DataFrame(data.get("players",[]))
    if not df.empty:
        team_filter=st.selectbox("Filter by Team",["All"]+TEAMS)
        if team_filter!="All":
            df=df[df["team"]==team_filter]
        st.dataframe(df,width="stretch")
    else: st.caption("No players yet.")

# ---------------- Record ----------------
with tab_record:
    st.subheader("Record W/L")
    inline_unlock("Record")
    if st.session_state.unlocked:
        names=[p["name"] for p in data.get("players",[])]
        if names:
            name=st.selectbox("Player",names)
            result=st.radio("Result",["Win","Loss"],horizontal=True)
            if st.button("Submit Result"):
                for p in data["players"]:
                    if p["name"]==name:
                        p.setdefault("results","")
                        p["results"]+= "W" if result=="Win" else "L"
                        change=f"{name} recorded a {result}"
                        data.setdefault("highlights",[]).insert(0,change)
                        save_data(data)
                        st.success(change)
                        st.experimental_rerun()
        else: st.caption("Add players first.")


# ---------------- Fixtures ----------------
with tab_fix:
    st.subheader("League Fixtures by Team")
    # Build week selector
    wk_labels = [f"Week {d['week']:02d} ({d['date']})" for d in FIXTURES]
    wk_idx = st.selectbox("Select week", options=list(range(len(FIXTURES))), format_func=lambda i: wk_labels[i])
    sel_week = FIXTURES[wk_idx]

    # Build per-team view
    rows = []
    for home, away in sel_week["matches"]:
        rows.append({"Team": home, "Opponent": away, "Home/Away": "Home", "Fixture": f"{home} v {away}", "Date": sel_week["date"]})
        rows.append({"Team": away, "Opponent": home, "Home/Away": "Away", "Fixture": f"{home} v {away}", "Date": sel_week["date"]})

    df_fx = pd.DataFrame(rows)
    # Ensure teams shown in consistent order
    df_fx["Team"] = pd.Categorical(df_fx["Team"], categories=TEAMS, ordered=True)
    df_fx = df_fx.sort_values(["Team","Home/Away"]).reset_index(drop=True)

    # Optional team filter for quick lookup
    team_pick = st.selectbox("Filter by team (optional)", ["All"] + TEAMS)
    if team_pick != "All":
        df_fx = df_fx[df_fx["Team"] == team_pick]

    st.dataframe(df_fx, use_container_width=True)

# ---------------- Announcements ----------------
with tab_ann:
    st.subheader("Announcements")
    inline_unlock("Announce")
    if st.session_state.unlocked:
        txt=st.text_area("Set Announcement",value=data.get("announcement",""))
        if st.button("Save Announcement"):
            data["announcement"]=txt
            save_data(data)
            st.success("Announcement saved")
