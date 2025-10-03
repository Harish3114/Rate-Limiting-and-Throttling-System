import streamlit as st
import redis
import pandas as pd
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
import time
import os
from dotenv import load_dotenv

load_dotenv() 
# Auto-refresh every 10 sec
st_autorefresh(interval=10000, key="dashboard_counter")


REDIS_URL = os.getenv("REDIS_URL")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)



user_names = {
    "key_123": "Hari",
    "key_456": "Rajuu",
    "user_1": "Mike",
    "user_2": "Lara",
    "user_3": "Joe",
}


# Page config
st.set_page_config(page_title="API Rate Limit Dashboard", layout="wide")
st.title("🚦 API Rate Limit Dashboard")


# Violations Section
st.subheader("Recent Violations (Throttled / Blocked)")
violations = r.lrange("violations", 0, 20)  # last 20 violations

if violations:
    processed_violations = []
    for v in violations:
        try:
            api_part, ts = (v.split(" at ") + [""])[:2]
            username = user_names.get(api_part.split(":")[0], api_part.split(":")[0])
            event_type = api_part.split(":")[1] if ":" in api_part else api_part
            processed_violations.append([username, event_type, ts])
        except:
            processed_violations.append(["Unknown", v, ""])

    df_violations = pd.DataFrame(processed_violations, columns=["User", "Event", "Timestamp"])

    # Convert timestamp to IST
    ist_offset = timedelta(hours=5, minutes=30)
    def to_ist(ts):
        try:
            dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
            return (dt + ist_offset).strftime("%Y-%m-%d %H:%M:%S IST")
        except:
            return ts

    df_violations["Timestamp"] = df_violations["Timestamp"].apply(to_ist)
    st.table(df_violations)
else:
    st.write("✅ No violations yet")


# Current API Usage Section
st.subheader("Current API Requests (last minute)")

request_counts = defaultdict(int)
now = int(time.time())

# Fetch requests from sorted set (last 60 sec)
recent_requests = r.zrangebyscore("recent_requests", now-60, now, withscores=False)

for item in recent_requests:
    try:
        user_id = item.split(":")[0]  # "key_123:1696032000" → "key_123"
        request_counts[user_id] += 1
    except:
        continue

if request_counts:
    # Map to friendly names
    df_requests = pd.DataFrame(
        [(user_names.get(uid, uid), count) for uid, count in request_counts.items()],
        columns=["User", "Requests"]
    )
    st.table(df_requests)

    # Bar chart
    st.subheader("Requests per User")
    fig, ax = plt.subplots()
    for user, count in df_requests.values:
        ax.bar(user, count, color="skyblue")
    ax.set_ylabel("Requests")
    ax.set_title("API Requests in Last Minute")
    st.pyplot(fig)
else:
    st.write("No API requests logged in the last 60 seconds.")
