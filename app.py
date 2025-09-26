import json
import os
from typing import List, Dict, Any
import streamlit as st
import pandas as pd
import requests

MAX_GAMES = 28
LOCAL_DATA_PATH = "app_data/league.json"

# ---- Ultra-light health endpoint ----
if st.query_params.get("health") == "1":
    st.write("OK")
    st.stop()
