import streamlit as st
import plotly.graph_objects as go
import numpy as np
import time

st.set_page_config(layout="wide")
st.title("BE-Kundencenter Energy Dashboard")
st.markdown("<br>", unsafe_allow_html=True) 

# Helper to generate random values
def random_values(n):
    return np.random.randint(10, 100, size=n)

# --- "Database" for the dashboard ---
dashboard_db = [
    {"sensor_id": "21820", "name": "Mattersburg",    "live_usage": 3.2, "past_7_days_usage": 120.5, "carbon_footprint": 15.3, "color": "indianred"},
    {"sensor_id": "21189", "name": "Eisenstadt",     "live_usage": 2.7, "past_7_days_usage": 110.2, "carbon_footprint": 13.8, "color": "royalblue"},
    {"sensor_id": "22097", "name": "Jennersdorf",    "live_usage": 4.1, "past_7_days_usage": 130.9, "carbon_footprint": 17.2, "color": "seagreen"},
    {"sensor_id": "21821", "name": "Oberwart",       "live_usage": 3.5, "past_7_days_usage": 125.0, "carbon_footprint": 16.0, "color": "orange"},
    {"sensor_id": "21822", "name": "Oberpullendorf", "live_usage": 2.9, "past_7_days_usage": 115.7, "carbon_footprint": 14.5, "color": "purple"},
    {"sensor_id": "22096", "name": "Güssing",        "live_usage": 3.8, "past_7_days_usage": 128.3, "carbon_footprint": 16.8, "color": "gold"},
]

def plot_gauges(items):
    fig = go.Figure()
    for i, item in enumerate(items):
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=item["live_usage"],
            title={'text': item["name"], 'font': {'size': 14}},
            domain={'row': 0, 'column': i}
        ))
    fig.update_layout(
        grid={'rows': 1, 'columns': 6, 'pattern': "independent"},
        margin=dict(l=10, r=10, t=40, b=10),
        height=200
    )
    return fig

def plot_bar(items, value_key, title):
    fig = go.Figure(go.Bar(
        y=[item["name"] for item in items],
        x=[item[value_key] for item in items],
        orientation='h',
        marker_color=[item["color"] for item in items],
        text=[item[value_key] for item in items],
        textposition='outside'
    ))
    fig.update_layout(
        title=title,
        xaxis=dict(range=[0, max(item[value_key] for item in items) * 1.15]),
        height=500
    )
    return fig

# --- SESSION STATE FOR TIMERS ---
if 'last_gauge_update' not in st.session_state:
    st.session_state.last_gauge_update = 0
if 'dashboard_db' not in st.session_state:
    st.session_state.dashboard_db = dashboard_db.copy()

if 'last_bar_update' not in st.session_state:
    st.session_state.last_bar_update = 0

now = time.time()
# Gauges: update every 10s (simulate new live_usage values)
if now - st.session_state.last_gauge_update > 10:
    for item in st.session_state.dashboard_db:
        item["live_usage"] = np.random.uniform(2.5, 4.5)
    st.session_state.last_gauge_update = now

# Bars: update every 20s (simulate new past_7_days_usage and carbon_footprint)
if now - st.session_state.last_bar_update > 20:
    for item in st.session_state.dashboard_db:
        item["past_7_days_usage"] = np.random.uniform(100, 140)
        item["carbon_footprint"] = np.random.uniform(12, 18)
    st.session_state.last_bar_update = now

# --- LAYOUT ---
st.plotly_chart(plot_gauges(st.session_state.dashboard_db), use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(
        plot_bar(st.session_state.dashboard_db, "past_7_days_usage", "Gesamtverbrauch letzten 7 Tage [kWh]"),
        use_container_width=True
    )
with col2:
    st.plotly_chart(
        plot_bar(st.session_state.dashboard_db, "carbon_footprint", "CO2-Abdruck letztes Monat [Bäume]"),
        use_container_width=True
    )

import time

time.sleep(10)
print("finishe")
# --- AUTO REFRESH ---
st.rerun()