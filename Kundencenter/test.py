import streamlit as st
import numpy as np
import time

st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    .main {background-color: #181818;}
    div[data-testid="stMetric"] {background: #222; border-radius: 10px; padding: 10px;}
    .big-font {font-size:32px !important;}
    .yellow {color: #ffe066;}
    .red {color: #ff4d4d;}
    .green {color: #4dff88;}
    .grey {color: #cccccc;}
    .box {background: #222; border-radius: 10px; padding: 20px; margin-bottom: 10px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Gesamtübersicht Kundencenter Burgenland Energie")

# --- CUSTOMER CENTER DEFINITIONS ---
customer_centers = [
    {"sensor_id": "21820", "name": "Kundencenter 1"},
    {"sensor_id": "21189", "name": "Kundencenter 2"},
    {"sensor_id": "22097", "name": "Kundencenter 3"},
    {"sensor_id": "21821", "name": "Kundencenter 4"},
    {"sensor_id": "21822", "name": "Kundencenter 5"},
    {"sensor_id": "22096", "name": "Kundencenter 6"},
]

def random_usage_per_day(days=7):
    today = time.time()
    return [
        {
            "date": time.strftime("%Y-%m-%d", time.localtime(today - 86400 * i)),
            "consumption": float(np.random.uniform(10, 35))
        }
        for i in range(days)
    ][::-1]

def calc_stats(usage_per_day):
    if not usage_per_day:
        return 0, 0, None, None
    sum_usage = sum(x["consumption"] for x in usage_per_day)
    avg_usage = sum_usage / len(usage_per_day)
    min_usage = min(usage_per_day, key=lambda x: x["consumption"])
    max_usage = max(usage_per_day, key=lambda x: x["consumption"])
    return sum_usage, avg_usage, min_usage, max_usage

def random_live_usage():
    return float(np.random.uniform(10, 40))

def build_dashboard_db():
    db = []
    for cc in customer_centers:
        usage_per_day = random_usage_per_day()
        sum_usage, avg_usage, min_usage, max_usage = calc_stats(usage_per_day)
        db.append({
            "sensor_id": cc["sensor_id"],
            "name": cc["name"],
            "usage_per_day": usage_per_day,
            "min_usage": min_usage,
            "max_usage": max_usage,
            "sum_usage": sum_usage,
            "avg_usage": avg_usage,
            "live_usage": random_live_usage(),
        })
    # Gesamt (total)
    usage_per_day_total = [
        {
            "date": d["date"],
            "consumption": sum(
                cc["usage_per_day"][i]["consumption"] for cc in db
            )
        }
        for i, d in enumerate(db[0]["usage_per_day"])
    ]
    sum_usage, avg_usage, min_usage, max_usage = calc_stats(usage_per_day_total)
    db.append({
        "sensor_id": "00000",
        "name": "Gesamt",
        "usage_per_day": usage_per_day_total,
        "min_usage": min_usage,
        "max_usage": max_usage,
        "sum_usage": sum_usage,
        "avg_usage": avg_usage,
        "live_usage": sum(cc["live_usage"] for cc in db),
    })
    return db

# --- SESSION STATE ---
if "dashboard_db" not in st.session_state:
    st.session_state.dashboard_db = build_dashboard_db()
if "last_update" not in st.session_state:
    st.session_state.last_update = 0
if "single_cc_idx" not in st.session_state:
    st.session_state.single_cc_idx = 0

# --- UPDATE RANDOM VALUES EVERY 10s ---
now = time.time()
if now - st.session_state.last_update > 10:
    st.session_state.dashboard_db = build_dashboard_db()
    st.session_state.single_cc_idx = (st.session_state.single_cc_idx + 1) % len(customer_centers)
    st.session_state.last_update = now
    st.rerun()

db = st.session_state.dashboard_db
gesamt = db[-1]
ccs = db[:-1]
single_idx = st.session_state.single_cc_idx
single_cc = ccs[single_idx]

# --- LAYOUT ---
col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    st.markdown("#### Gesamtverbrauch über gewählten Zeitraum")
    st.metric(label="Gesamtverbrauch", value=f"{gesamt['sum_usage']:.0f} kWh", delta=None)
    st.markdown("#### Täglicher Durchschnitt")
    st.metric(label="Durchschnitt", value=f"{gesamt['avg_usage']:.2f} kWh", delta=None)
    st.markdown("#### Höchster Verbrauch")
    max_cc = max(ccs, key=lambda x: x["sum_usage"])
    st.metric(label=f"{max_cc['name']}", value=f"{max_cc['sum_usage']:.1f} KWH")
    st.markdown("#### Niedrigster Verbrauch")
    min_cc = min(ccs, key=lambda x: x["sum_usage"])
    st.metric(label=f"{min_cc['name']}", value=f"{min_cc['sum_usage']:.1f} KWH")

with col2:
    st.markdown("#### Live")
    st.metric(label="Aktueller Verbrauch", value=f"{gesamt['live_usage']:.1f} kW")
    st.markdown("#### Minimalster Verbrauch")
    st.metric(label=f"{min_cc['name']} (in Zeitraum)", value=f"{min_cc['min_usage']['consumption']:.1f} kWh")
    st.markdown("#### Maximalster Verbrauch")
    st.metric(label=f"{max_cc['name']} (in Zeitraum)", value=f"{max_cc['max_usage']['consumption']:.1f} kWh")

with col3:
    st.markdown("#### Differenz Vorwoche")
    diff_kw = np.random.uniform(-30, 30)
    st.metric(label="KW Differenz", value=f"{diff_kw:+.2f}%", delta=f"{diff_kw:+.2f}%")
    st.markdown("#### Differenz gleicher Vorwoche im letzten Jahr")
    diff_last_year = np.random.uniform(-30, 30)
    st.metric(label="Jahr Differenz", value=f"{diff_last_year:+.2f}%", delta=f"{diff_last_year:+.2f}%")

st.markdown("---")

# Verbrauchsübersicht Balken
st.markdown("### Kundencenter Verbrauchsübersicht")
live_usages = sorted([(cc["name"], cc["sum_usage"], cc["live_usage"]) for cc in ccs], key=lambda x: -x[1])
for name, sum_usage, live_usage in live_usages:
    st.progress(min(sum_usage / max_cc["sum_usage"], 1.0), text=f"{name}: {sum_usage:.1f} KWH  |  Live: {live_usage:.1f} kW")

st.markdown("---")

# Detailbericht für einzelnes Kundencenter
st.markdown(f"### {single_cc['name']} Detailbericht")
col4, col5 = st.columns([1, 1])
with col4:
    st.metric(label="Gesamtverbrauch über gewählten Zeitraum", value=f"{single_cc['sum_usage']:.0f} kWh")
    st.metric(label="Täglicher Durchschnitt", value=f"{single_cc['avg_usage']:.2f} kWh")
    st.metric(label="Maximalverbrauch", value=f"{single_cc['max_usage']['date']}", delta=f"{single_cc['max_usage']['consumption']:.2f} kWh")
    st.metric(label="Minimalverbrauch", value=f"{single_cc['min_usage']['date']}", delta=f"{single_cc['min_usage']['consumption']:.2f} kWh")
with col5:
    # Simulate pie chart data
    st.markdown("#### Verbrauch nach Kategorie (simuliert)")
    import matplotlib.pyplot as plt
    categories = ["Standby", "Licht & Geräte", "Andere Geräte", "Küche", "Klimaanlage"]
    values = np.random.dirichlet(np.ones(len(categories)), size=1)[0] * single_cc['sum_usage']
    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(values, labels=categories, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)