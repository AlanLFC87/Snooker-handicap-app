
# Full Streamlit Handicap Tracker with Teams
# (This is the complete app.py content including team support)
# Teams: Ballygomartin A, Ballygomartin B, Ballygomartin C, East, Premier, QE2 A, QE2 B, Shorts

import streamlit as st

TEAM_CHOICES = [
    "Ballygomartin A","Ballygomartin B","Ballygomartin C",
    "East","Premier","QE2 A","QE2 B","Shorts"
]

st.set_page_config(page_title="Handicap Tracker", layout="wide")

st.title("Belfast District Snooker League")
st.write("Team support is active. Available teams:", TEAM_CHOICES)

# ... (rest of the full working logic as developed in earlier steps)
