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

# ---------------- Fixtures Data ----------------
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
    st.subheader("League Fixtures")
    week_labels = [f"Week {f['week']:02d} ({f['date']})" for f in FIXTURES]
    wk = st.selectbox("Select Week", options=range(len(FIXTURES)), format_func=lambda i: week_labels[i])
    chosen = FIXTURES[wk]
    st.write(f"### Week {chosen['week']} – {chosen['date']}")
    for m in chosen["matches"]:
        st.write("• " + m)

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
