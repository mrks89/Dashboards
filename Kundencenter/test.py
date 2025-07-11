import streamlit as st
import plotly.graph_objects as go
import numpy as np
import time
from datetime import datetime, timedelta
from functions import APIClient, get_day_with_max_consumption, get_day_with_min_consumption, get_mean_consumption, get_sum_consumption
import base64

def get_base64_image(image_path):
    """Convert image to base64 string for HTML display"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"DEBUG: Error converting image to base64: {e}")
        return ""

print("DEBUG: Starting application initialization...")

# --- CONFIG ---
print("DEBUG: Setting up Streamlit page config...")
st.set_page_config(layout="wide")
st.markdown("""
    <style>
        .main {background-color: #222228;}
        .block-container {padding-top: 1.5rem;}
        .dashboard-section {
            border: 2px solid #FFCC00;
            border-radius: 24px;
            padding: 18px 24px 24px 24px;
            margin-bottom: 24px;
            background: #18181c;
        }
        .yellow-text {color: #FFCC00;}
        .white-text {color: #fff;}
        .gray-text {color: #bbb;}
        .big {font-size: 2.2rem; font-weight: 700;}
        .medium {font-size: 1.2rem;}
        .small {font-size: 0.9rem;}
        .center {text-align: center;}
        .flex-row {display: flex; flex-direction: row; align-items: center;}
        .flex-col {display: flex; flex-direction: column;}
        .gap-1 {gap: 1rem;}
        .gap-2 {gap: 2rem;}
        .box {background: #222228; border-radius: 12px; padding: 12px 18px; margin-bottom: 10px; border: 1px solid #555555;}
        .box-red {background: #222228; border: 1px solid #871010;}
        .box-green {background: #222228; border: 1px solid #278109 }
        .box-yellow {background: #222228; border: 1px solid #555555;}
        .box-icon {font-size: 1.5rem; margin-right: 10px;}
        .bar-label {font-size: 1.1rem; font-weight: 600;}
    </style>
""", unsafe_allow_html=True)

# --- CUSTOMER CENTER DEFINITIONS ---
print("DEBUG: Defining customer centers...")
customer_centers = [
    {"sensor_id": "21820", "name": "Mattersburg"}, 
    {"sensor_id": "21189", "name": "Eisenstadt"},
    {"sensor_id": "22097", "name": "Jennersdorf"},
    {"sensor_id": "21821", "name": "Oberwart"},
    {"sensor_id": "21822", "name": "Oberpullendorf"},
    {"sensor_id": "22096", "name": "Güssing"},
]
print(f"DEBUG: Defined {len(customer_centers)} customer centers")

# --- API CLIENT SETUP ---
print("DEBUG: Setting up API client...")
CLIENT_ID = st.secrets["client_id"]  # Replace with your client ID
CLIENT_SECRET = st.secrets["client_secret"]  # Replace with your client secret
print(f"DEBUG: API credentials loaded - Client ID: {CLIENT_ID[:8]}...") # Only show first 8 chars for security

api = APIClient(CLIENT_ID, CLIENT_SECRET)
print(f"DEBUG: Checking API authentication status...")
if not hasattr(st.session_state, "api_authenticated"):
    print("DEBUG: API not authenticated yet, attempting authentication...")
    try:
        print("DEBUG: Calling api.authenticate()...")
        api.authenticate()
        print("DEBUG: API authentication successful!")
        st.session_state.api_authenticated = True
    except Exception as e:
        print(f"DEBUG: API authentication failed with error: {e}")
        st.error(f"API Authentifizierung fehlgeschlagen: {e}")
        st.stop()
else:
    print("DEBUG: API already authenticated, skipping authentication step")

# --- DATE RANGE (last 7 days) ---
print("DEBUG: Calculating date range...")
today = datetime.now().date()
start_date_obj = today - timedelta(days=7)
end_date_obj = today - timedelta(days=1)
start_date = start_date_obj.strftime("%Y-%m-%d")
end_date = end_date_obj.strftime("%Y-%m-%d")

# Calculate calendar weeks
start_week = start_date_obj.isocalendar()[1]
end_week = end_date_obj.isocalendar()[1]
start_year = start_date_obj.isocalendar()[0]
end_year = end_date_obj.isocalendar()[0]

print(f"DEBUG: Date range calculated - Start: {start_date}, End: {end_date}")
print(f"DEBUG: Calendar weeks - Start: {start_year}-W{start_week:02d}, End: {end_year}-W{end_week:02d}")

# --- DATA FETCHING & CACHING ---
def fetch_historical_data():
    """Fetch historical data (usage per day, statistics) - called once daily at 1 AM"""
    print("DEBUG: Starting fetch_historical_data() function...")
    db = []
    for cc in customer_centers:
        print(f"DEBUG: Processing customer center: {cc['name']} (ID: {cc['sensor_id']})")
        try:
            print(f"DEBUG: Fetching usage_per_day for {cc['name']}...")
            usage_per_day_raw = api.usage_per_day(cc["sensor_id"], start_date, end_date)
            # Convert watts to kilowatts
            usage_per_day = [{"date": day["date"], "consumption": day["consumption"] / 1000} for day in usage_per_day_raw]
            print(f"DEBUG: Successfully fetched {len(usage_per_day)} days of data for {cc['name']}")
            
            print(f"DEBUG: Calculating statistics for {cc['name']}...")
            sum_usage = get_sum_consumption(usage_per_day)
            avg_usage = get_mean_consumption(usage_per_day)
            min_usage = get_day_with_min_consumption(usage_per_day)
            max_usage = get_day_with_max_consumption(usage_per_day)
            
        except Exception as e:
            print(f"DEBUG: Error processing {cc['name']}: {e}")
            usage_per_day = []
            sum_usage = avg_usage = 0
            min_usage = max_usage = {"date": "-", "consumption": 0}        
        db.append({
            "sensor_id": cc["sensor_id"],
            "name": cc["name"],
            "usage_per_day": usage_per_day,
            "min_usage": min_usage,
            "max_usage": max_usage,
            "sum_usage": sum_usage,
            "avg_usage": avg_usage,
            "live_usage": 0,  # Will be updated by fetch_live_data
        })
        print(f"DEBUG: Added {cc['name']} to database with sum_usage: {sum_usage}")
    
    # Gesamt (total)
    print("DEBUG: Calculating total consumption for all customer centers...")
    usage_per_day_total = []
    if db and db[0]["usage_per_day"]:
        print(f"DEBUG: Database has {len(db)} entries, first entry has {len(db[0]['usage_per_day'])} days of data")
        for i in range(len(db[0]["usage_per_day"])):
            date = db[0]["usage_per_day"][i]["date"]
            consumption = sum(cc["usage_per_day"][i]["consumption"] for cc in db if len(cc["usage_per_day"]) > i)
            usage_per_day_total.append({"date": date, "consumption": consumption})
            print(f"DEBUG: Day {date}: Total consumption = {consumption}")
    else:
        print("DEBUG: No data available for calculating totals - database is empty or has no usage_per_day data")
    
    print("DEBUG: Calculating total statistics...")
    sum_usage = get_sum_consumption(usage_per_day_total)
    avg_usage = get_mean_consumption(usage_per_day_total)
    min_usage = get_day_with_min_consumption(usage_per_day_total)
    max_usage = get_day_with_max_consumption(usage_per_day_total)
    print(f"DEBUG: Total statistics - Sum: {sum_usage}, Avg: {avg_usage}")
    
    db.append({
        "sensor_id": "00000",
        "name": "Gesamt",
        "usage_per_day": usage_per_day_total,
        "min_usage": min_usage,
        "max_usage": max_usage,
        "sum_usage": sum_usage,
        "avg_usage": avg_usage,
        "live_usage": 0,  # Will be updated by fetch_live_data
    })
    
    # Also fetch previous week data
    print("DEBUG: Fetching previous week data...")
    prev_week_data = fetch_previous_week_data()
    
    print(f"DEBUG: fetch_historical_data() completed with {len(db)} total entries")
    return db, prev_week_data

def fetch_previous_week_data():
    """Fetch previous week data for comparison"""
    print("DEBUG: Starting fetch_previous_week_data() function...")
    
    # Calculate previous week date range
    today = datetime.now().date()
    current_week_start = today - timedelta(days=7)  # Start of current period
    prev_week_end = current_week_start - timedelta(days=1)  # End of previous week
    prev_week_start = prev_week_end - timedelta(days=6)  # Start of previous week (7 days)
    
    prev_start_date = prev_week_start.strftime("%Y-%m-%d")
    prev_end_date = prev_week_end.strftime("%Y-%m-%d")
    
    print(f"DEBUG: Previous week range - Start: {prev_start_date}, End: {prev_end_date}")
    
    db_prev = []
    for cc in customer_centers:
        print(f"DEBUG: Processing previous week data for {cc['name']}...")
        try:
            usage_per_day_raw = api.usage_per_day(cc["sensor_id"], prev_start_date, prev_end_date)
            # Convert watts to kilowatts
            usage_per_day = [{"date": day["date"], "consumption": day["consumption"] / 1000} for day in usage_per_day_raw]
            sum_usage = get_sum_consumption(usage_per_day)
        except Exception as e:
            print(f"DEBUG: Error processing previous week data for {cc['name']}: {e}")
            sum_usage = 0
        
        db_prev.append({
            "sensor_id": cc["sensor_id"],
            "name": cc["name"],
            "sum_usage": sum_usage,
        })
    
    # Calculate total for previous week
    total_prev_usage = sum(cc["sum_usage"] for cc in db_prev)
    db_prev.append({
        "sensor_id": "00000",
        "name": "Gesamt",
        "sum_usage": total_prev_usage,
    })
    
    print(f"DEBUG: Previous week total usage: {total_prev_usage}")
    return db_prev

def fetch_live_data(db):
    """Fetch only live power data for all customer centers"""
    print("DEBUG: Starting fetch_live_data() function...")
    total_live_usage = 0
    
    for i, cc in enumerate(db[:-1]):  # Exclude the 'Gesamt' entry
        try:
            print(f"DEBUG: Fetching live power for {cc['name']}...")
            live_usage = api.get_live_power(cc["sensor_id"]) / 1000  # Convert watts to kilowatts
            db[i]["live_usage"] = live_usage
            total_live_usage += live_usage
            print(f"DEBUG: Live usage for {cc['name']}: {live_usage} kW")
        except Exception as e:
            print(f"DEBUG: Error fetching live data for {cc['name']}: {e}")
            db[i]["live_usage"] = 0
    
    # Update total live usage for 'Gesamt'
    db[-1]["live_usage"] = total_live_usage
    print(f"DEBUG: Total live usage: {total_live_usage} kW")
    return db

def should_fetch_historical_data():
    """Check if it's time to fetch historical data (daily at 1 AM)"""
    now = datetime.now()
    # Check if it's 1 AM (between 1:00 and 1:05 to give some window)
    if now.hour == 1 and now.minute < 5:
        return True
    
    # Also fetch on first run if no historical data exists
    if "historical_data_last_fetch" not in st.session_state:
        return True
    
    # Check if it's been more than 23 hours since last fetch (fallback)
    last_fetch = st.session_state.get("historical_data_last_fetch", 0)
    return (time.time() - last_fetch) > 24 * 3600

def fetch_dashboard_data():
    """Main function that coordinates historical and live data fetching"""
    print("DEBUG: Starting fetch_dashboard_data() function...")
    
    # Check if we need to fetch historical data
    if should_fetch_historical_data():
        print("DEBUG: Fetching historical data...")
        db, prev_week_data = fetch_historical_data()
        st.session_state.historical_data_last_fetch = time.time()
        st.session_state.dashboard_db_historical = db
        st.session_state.previous_week_data = prev_week_data
    else:
        print("DEBUG: Using cached historical data...")
        db = st.session_state.get("dashboard_db_historical", [])
        if not db:  # Fallback if no historical data exists
            print("DEBUG: No cached historical data found, fetching...")
            db, prev_week_data = fetch_historical_data()
            st.session_state.historical_data_last_fetch = time.time()
            st.session_state.dashboard_db_historical = db
            st.session_state.previous_week_data = prev_week_data
    
    # Always fetch live data
    db = fetch_live_data(db.copy())  # Use copy to avoid modifying cached data
    
    return db

# --- DATA FETCHING ---

print("DEBUG: Checking session state for dashboard_db and last_update...")
if "dashboard_db" not in st.session_state or "last_update" not in st.session_state:
    print("DEBUG: dashboard_db or last_update not in session state, initializing...")
    st.session_state.dashboard_db = fetch_dashboard_data()
    st.session_state.last_update = time.time()
    st.session_state.last_live_update = time.time()
else:
    print("DEBUG: dashboard_db and last_update already in session state")

print("DEBUG: Checking session state for single_cc_idx...")
if "single_cc_idx" not in st.session_state:
    print("DEBUG: single_cc_idx not in session state, initializing to 0")
    st.session_state.single_cc_idx = 0
else:
    print(f"DEBUG: single_cc_idx already in session state: {st.session_state.single_cc_idx}")

# Initialize live update tracking if not exists
if "last_live_update" not in st.session_state:
    st.session_state.last_live_update = time.time()

# Refresh live data every 10 seconds, full data check for historical updates
current_time = time.time()
if current_time - st.session_state.last_live_update > 10:  # Live data every 10 seconds
    print("DEBUG: Live data is older than 10 seconds, updating...")
    # Only fetch live data if we have historical data cached
    if "dashboard_db_historical" in st.session_state and st.session_state.dashboard_db_historical:
        print("DEBUG: Updating only live data...")
        db = st.session_state.dashboard_db_historical.copy()
        st.session_state.dashboard_db = fetch_live_data(db)
    else:
        print("DEBUG: No historical data cached, fetching full data...")
        st.session_state.dashboard_db = fetch_dashboard_data()
    
    st.session_state.last_live_update = current_time
    st.session_state.last_update = current_time
    # Cycle through customer centers for detail view every 30 seconds
    if current_time - st.session_state.get("last_cc_cycle", 0) > 30:
        st.session_state.single_cc_idx = (st.session_state.single_cc_idx + 1) % len(customer_centers)
        st.session_state.last_cc_cycle = current_time
        print(f"DEBUG: Cycled to single_cc_idx: {st.session_state.single_cc_idx}")

# Check for historical data updates (daily at 1 AM or on first run)
if should_fetch_historical_data():
    print("DEBUG: Time for historical data update...")
    st.session_state.dashboard_db = fetch_dashboard_data()
    st.session_state.last_update = current_time

# Use current data from session state
db = st.session_state.dashboard_db
print(f"DEBUG: Retrieved dashboard data with {len(db)} entries")

# Get fresh data for display
gesamt = db[-1]
print(f"DEBUG: Gesamt data - Sum: {gesamt['sum_usage']}, Live: {gesamt['live_usage']}")
ccs = db[:-1]
print(f"DEBUG: Individual customer centers: {len(ccs)} entries")
single_idx = st.session_state.single_cc_idx
single_cc = ccs[single_idx]
print(f"DEBUG: Selected single CC for detail view: {single_cc['name']} (index {single_idx})")

# --- DASHBOARD HEADER ---
# Format week display
if start_week == end_week and start_year == end_year:
    week_display = f"KW {start_week:02d}/{start_year}"
else:
    week_display = f"KW {start_week:02d}/{start_year} - KW {end_week:02d}/{end_year}"

# Create header with logo and title
header_col1, header_col2 = st.columns([1, 4])

with header_col1:
    # Display logo
    try:
        logo_base64 = get_base64_image("img/logo.png")
        st.markdown(
            f'<div style="display: flex; align-items: center; height: 100%;">'
            f'<img src="data:image/png;base64,{logo_base64}" '
            f'style="height: 4.4rem; width: auto; object-fit: contain;" />'
            f'</div>',
            unsafe_allow_html=True
        )
        print("DEBUG: Successfully loaded img/logo.png")
    except Exception as e:
        print(f"DEBUG: Could not load img/logo.png: {e}")
        # Fallback: show a placeholder
        st.markdown(
            f'<div style="height: 4.4rem; display: flex; align-items: center; justify-content: center; border: 2px dashed #FFCC00; border-radius: 8px;">'
            f'<span class="yellow-text" style="font-size: 1rem;">LOGO</span>'
            f'</div>',
            unsafe_allow_html=True
        )

with header_col2:
    st.markdown(
        f'<span class="yellow-text big">Gesamtübersicht Kundencenter Burgenland Energie</span> '
        f'<span class="gray-text" style="font-size:1.2rem;">(letzten 7 Tage)</span>',
        unsafe_allow_html=True
    )

st.markdown('<br>', unsafe_allow_html=True)

# Create placeholders for real-time updates
status_placeholder = st.empty()
main_placeholder = st.empty()

# Real-time dashboard loop
for seconds in range(3600):  # Run for 1 hour (3600 seconds)
    # Check if we need to refresh live data (every 10 seconds)
    current_time = time.time()
    if current_time - st.session_state.last_live_update > 10:
        print("DEBUG: Refreshing live data in real-time loop...")
        # Only fetch live data if we have historical data cached
        if "dashboard_db_historical" in st.session_state and st.session_state.dashboard_db_historical:
            print("DEBUG: Updating only live data in loop...")
            db = st.session_state.dashboard_db_historical.copy()
            st.session_state.dashboard_db = fetch_live_data(db)
        else:
            print("DEBUG: No historical data cached in loop, fetching full data...")
            st.session_state.dashboard_db = fetch_dashboard_data()
        
        st.session_state.last_live_update = current_time
        st.session_state.last_update = current_time
        
        # Cycle through customer centers for detail view every 30 seconds
        if current_time - st.session_state.get("last_cc_cycle", 0) > 30:
            st.session_state.single_cc_idx = (st.session_state.single_cc_idx + 1) % len(customer_centers)
            st.session_state.last_cc_cycle = current_time
        
        # Update data references
        db = st.session_state.dashboard_db
        gesamt = db[-1]
        ccs = db[:-1]
        single_idx = st.session_state.single_cc_idx
        single_cc = ccs[single_idx]
    
    # Check for historical data updates (daily at 1 AM)
    if should_fetch_historical_data():
        print("DEBUG: Time for historical data update in loop...")
        st.session_state.dashboard_db = fetch_dashboard_data()
        st.session_state.last_update = current_time
        
        # Update data references
        db = st.session_state.dashboard_db
        gesamt = db[-1]
        ccs = db[:-1]
        single_idx = st.session_state.single_cc_idx
        single_cc = ccs[single_idx]
    
    # Update status indicator
    time_since_update = time.time() - st.session_state.last_live_update
    status_color = "🟢" if time_since_update < 5 else "🟡" if time_since_update < 10 else "🔴"    
    with status_placeholder.container():
        # Get historical data timing info
        historical_last_fetch = st.session_state.get("historical_data_last_fetch", 0)
        historical_time_str = datetime.fromtimestamp(historical_last_fetch).strftime("%d.%m %H:%M") if historical_last_fetch > 0 else "Not yet"
        next_historical_update = "01:00" if datetime.now().hour < 1 else "Tomorrow 01:00"
        
        st.markdown(
            f'<div style="position: fixed; top: 10px; left: 10px; z-index: 999; background: rgba(0,0,0,0.8); padding: 5px 10px; border-radius: 15px;">'
            f'<span style="color: white; font-size: 0.8rem;">'
            f'{status_color} Live: {datetime.fromtimestamp(st.session_state.last_live_update).strftime("%H:%M:%S")} | '
            f'📊 Historical: {historical_time_str} (Next: {next_historical_update})'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    # Update main dashboard content
    with main_placeholder.container():
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            # Gesamtverbrauch über gewählten Zeitraum and Vorwoche
            print(f"DEBUG: Rendering column 1 with gesamt data - sum: {gesamt['sum_usage']}, avg: {gesamt['avg_usage']}")
            st.markdown(
                f'<div class="box flex-row gap-1" style="height: 15vh; margin-bottom: 10px; display: flex; align-items: center;">'
                f'<span class="box-icon yellow-text">⚡</span>'
                f'<div><b style="font-size: 1rem;">Gesamtverbrauch </b><br>'
                f'<span class="yellow-text" style="font-size: 1.5rem; font-weight: bold;">{gesamt["sum_usage"]:.0f}</span> '
                f'<span class="gray-text" style="font-size: 1rem;">kWh</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )
            
            # Dummy diff for now, you can calculate real difference if you fetch last week's data
            # Get previous week data
            prev_week_data = st.session_state.get("previous_week_data", [])
            if prev_week_data:
                # Find the matching previous week data (Gesamt entry)
                prev_gesamt = next((item for item in prev_week_data if item["name"] == "Gesamt"), None)
                if prev_gesamt and prev_gesamt["sum_usage"] > 0:
                    absolute_kwh = gesamt["sum_usage"] - prev_gesamt["sum_usage"]
                    diff_kw = (absolute_kwh / prev_gesamt["sum_usage"]) * 100 if prev_gesamt["sum_usage"] > 0 else 0
                    prev_week_total = prev_gesamt["sum_usage"]
                else:
                    # Fallback to dummy data if no previous week data
                    diff_kw = np.random.uniform(-30, 30)
                    absolute_kwh = diff_kw * gesamt["sum_usage"] / 100
                    prev_week_total = gesamt["sum_usage"] + absolute_kwh
            else:
                # Fallback to dummy data if no previous week data
                diff_kw = np.random.uniform(-30, 30)
                absolute_kwh = diff_kw * gesamt["sum_usage"] / 100
                prev_week_total = gesamt["sum_usage"] + absolute_kwh
            
            st.markdown(
                f'<div class="box flex-row gap-1" style="height: 15vh; display: flex; align-items: center;">'
                f'<span class="box-icon yellow-text">📊</span>'
                f'<div><b style="font-size: 1rem;">Gesamtverbrauch Vorperiode</b><br>'
                f'<span class="yellow-text" style="font-size: 1.5rem; font-weight: bold;">{absolute_kwh:+.2f}</span> '
                f'<span class="gray-text" style="font-size: 1rem;">kWh</span> '
                f'<span class="gray-text" style="font-size: 1rem;">({diff_kw:+.2f}%)</span><br>'
                f'<span class="gray-text" style="font-size: 1rem;">{prev_week_total:.2f} kWh</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col2:
            # Täglicher Durchschnitt, Höchster Verbrauch, Niedrigster Verbrauch
            st.markdown(f'<div class="box flex-row gap-1" style="height: 10vh; margin-bottom: 10px; display: flex; align-items: center;"><span class="box-icon yellow-text">📅</span><div><b style="font-size: 1rem;">Täglicher Durchschnitt</b><br><span class="yellow-text" style="font-size: 1.5rem; font-weight: bold;">{gesamt["avg_usage"]:.2f}</span> <span class="gray-text" style="font-size: 1rem;">kWh</span></div></div>', unsafe_allow_html=True)
            
            max_cc = max(ccs, key=lambda x: x["sum_usage"])
            min_cc = min(ccs, key=lambda x: x["sum_usage"])
            print(f"DEBUG: Max CC: {max_cc['name']} ({max_cc['sum_usage']}), Min CC: {min_cc['name']} ({min_cc['sum_usage']})")
            
            st.markdown(f'<div class="box box-red flex-row gap-1" style="height: 10vh; margin-bottom: 10px; display: flex; align-items: center;"><span class="box-icon yellow-text">📈</span><div><b style="font-size: 1rem;">Höchster Verbrauch</b><br><span class="white-text" style="font-size: 1rem;">{max_cc["name"]}</span><br><span class="yellow-text" style="font-size: 1.5rem; font-weight: bold;">{max_cc["sum_usage"]:.1f}</span> <span class="gray-text" style="font-size: 1rem;">kWh</span></div></div>', unsafe_allow_html=True)
            
            st.markdown(f'<div class="box box-green flex-row gap-1" style="height: 10vh; display: flex; align-items: center;"><span class="box-icon yellow-text">📉</span><div><b style="font-size: 1rem;">Niedrigster Verbrauch</b><br><span class="white-text" style="font-size: 1rem;">{min_cc["name"]}</span><br><span class="yellow-text" style="font-size: 1.5rem; font-weight: bold;">{min_cc["sum_usage"]:.1f}</span> <span class="gray-text" style="font-size: 1rem;">kWh</span></div></div>', unsafe_allow_html=True)

        with col3:
            # Live indicator and gauge
            print(f"DEBUG: Rendering column 3 with live usage gauge: {gesamt['live_usage']} kW")
            st.markdown(
                '<div class="center">'
                '<span class="yellow-text medium" style="margin-right:20px;">● Live</span>'
                '<span class="white-text medium" style="font-size:1.2rem;">Gesamtverbrauch</span>'
                '</div>',
                unsafe_allow_html=True
            )
            
            # Calculate gauge max value
            gauge_max = max(100, gesamt["live_usage"] * 1.3)
            print(f"DEBUG: Gauge max value calculated: {gauge_max}")
            
            fig = go.Figure()
            
            # Create fine-grained color steps for gradual transition
            num_steps = 20  # Number of color steps for smooth transition
            steps = []
            
            for i in range(num_steps):
                start_range = (gauge_max / num_steps) * i
                end_range = (gauge_max / num_steps) * (i + 1)
                
                # Calculate progress from 0 to 1
                progress = i / (num_steps - 1)
                
                if progress <= 0.5:
                    # Green to Yellow transition (first half)
                    # Green: #0EB313, Yellow: #FFFF00
                    red = int(14 + (255 - 14) * (progress * 2))
                    green = int(179 + (255 - 179) * (progress * 2))
                    blue = int(19 * (1 - progress * 2))
                else:
                    # Yellow to Red transition (second half)
                    # Yellow: #FFFF00, Red: #F44336
                    red = int(255 + (244 - 255) * ((progress - 0.5) * 2))
                    green = int(255 + (67 - 255) * ((progress - 0.5) * 2))
                    blue = int(0 + (54 - 0) * ((progress - 0.5) * 2))
                
                # Ensure values are within valid range
                red = max(0, min(255, red))
                green = max(0, min(255, green))
                blue = max(0, min(255, blue))
                
                color = f"rgb({red},{green},{blue})"
                
                steps.append({
                    'range': [start_range, end_range], 
                    'color': color, 
                    'thickness': 0.2
                })
            
            # Add gauge indicator with needle
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=gesamt["live_usage"],
                number={'suffix': ' kW', 'font': {'size': 20, 'color': 'white'}},
                gauge={
                    'axis': {
                        'range': [0, gauge_max], 
                        'tickcolor': 'white', 
                        'tickwidth': 2, 
                        'ticklen': 10,
                        'tickfont': {'color': 'white', 'size': 12, 'family': 'Arial'},
                        'showticklabels': True,
                        'tickmode': 'linear',
                        'tick0': 0,
                        'dtick': gauge_max / 4
                    },
                    'bar': {'color': "rgba(0,0,0,0)", 'line': {'color':"rgba(0,0,0,0)" }},  # Hide the bar
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 0,
                    'steps': steps,
                    'threshold': {
                        'line': {'color': 'white', 'width': 6},
                        'thickness': 1.0,
                        'value': gesamt["live_usage"]
                    }
                },
                domain={'x': [0, 1], 'y': [0, 0.8]}  # Changed from [0, 1] to [0, 0.8] to move gauge down
            ))
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),  # Increased top margin from 20 to 40
                height=220,  # Changed from 300 to 150
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={'color': 'white', 'size': 12, 'family': 'Arial'},
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True, key=f"gauge_chart_{seconds}")

        st.markdown('<div style="height: 48px;"></div>', unsafe_allow_html=True)

        # Title above the entire row of 5 squares
        st.markdown(
            f'<span class="white-text medium"><span class="box-icon yellow-text">🔄</span>{single_cc["name"]} Detailbericht</span>',
            unsafe_allow_html=True
        )

        # Create 5 equal columns: image + 4 data boxes
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

        with col1:
            # Display image for the current customer center
            print(f"DEBUG: Displaying image for {single_cc['name']}")
            image_path = f"./img/{single_cc['name'].lower()}.png"
            try:
                # Use HTML to control image size - height matches the boxes
                st.markdown(
                    f'<div style="height: 280px; display: flex; justify-content: center; align-items: center;">'
                    f'<img src="data:image/png;base64,{get_base64_image(image_path)}" '
                    f'style="height: 280px; width: auto; object-fit: contain; border-radius: 8px;" />'
                    f'</div>',
                    unsafe_allow_html=True
                )
                print(f"DEBUG: Successfully loaded image: {image_path}")
            except Exception as e:
                print(f"DEBUG: Could not load image {image_path}: {e}")
                # Fallback: show a placeholder
                st.markdown(
                    f'<div class="box" style="height:280px; display:flex; flex-direction:column; justify-content:center; align-items:center;">'
                    f'<span class="yellow-text" style="font-size:2rem; text-align:center;">{single_cc["name"]}</span><br>'
                    f'<span class="gray-text" style="text-align:center;">Kundencenter</span>'
                    '</div>',
                    unsafe_allow_html=True
                )

        with col2:
            # Gesamtverbrauch
            st.markdown(
                f'<div class="box flex-col" style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; height: 280px;">'
                f'<span class="box-icon yellow-text" style="font-size: 2rem; margin-bottom: 8px;">⚡</span>'
                f'<div style="font-weight: bold; font-size: 1rem; margin-bottom: 12px;">Gesamtverbrauch</div>'
                f'<div><span class="yellow-text" style="font-size: 1.5rem; font-weight: bold;">{single_cc["sum_usage"]:.0f}</span></div>'
                f'<div><span class="gray-text" style="font-size: 1rem;">kWh</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col3:
            # Täglicher Durchschnitt
            st.markdown(
                f'<div class="box flex-col" style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; height: 280px;">'
                f'<span class="box-icon yellow-text" style="font-size: 2rem; margin-bottom: 8px;">📅</span>'
                f'<div style="font-weight: bold; font-size: 1rem; margin-bottom: 12px;">Täglicher Durchschnitt</div>'
                f'<div><span class="yellow-text" style="font-size: 1.5rem; font-weight: bold;">{single_cc["avg_usage"]:.2f}</span></div>'
                f'<div><span class="gray-text" style="font-size: 1rem;">kWh</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col4:
            # Maximalverbrauch
            st.markdown(
                f'<div class="box box-red flex-col" style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; height: 280px;">'
                f'<span class="box-icon yellow-text" style="font-size: 2rem; margin-bottom: 8px;">📈</span>'
                f'<div style="font-weight: bold; font-size: 1rem; margin-bottom: 8px;">Maximalverbrauch</div>'
                f'<div style="font-size: 1rem; color: white; margin-bottom: 8px;">{single_cc["max_usage"]["date"]}</div>'
                f'<div><span class="yellow-text" style="font-size: 1.5rem; font-weight: bold;">{single_cc["max_usage"]["consumption"]:.2f}</span></div>'
                f'<div><span class="gray-text" style="font-size: 1rem;">kWh</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col5:
            # Minimalverbrauch
            st.markdown(
                f'<div class="box box-green flex-col" style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; height: 280px;">'
                f'<span class="box-icon yellow-text" style="font-size: 2rem; margin-bottom: 8px;">📉</span>'
                f'<div style="font-weight: bold; font-size: 1rem; margin-bottom: 8px;">Minimalverbrauch</div>'
                f'<div style="font-size: 1rem; color: white; margin-bottom: 8px;">{single_cc["min_usage"]["date"]}</div>'
                f'<div><span class="yellow-text" style="font-size: 1.5rem; font-weight: bold;">{single_cc["min_usage"]["consumption"]:.2f}</span></div>'
                f'<div><span class="gray-text" style="font-size: 1rem;">kWh</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )

        print(f"DEBUG: Rendering detail view for {single_cc['name']} - Sum: {single_cc['sum_usage']}, Avg: {single_cc['avg_usage']}")
        print(f"DEBUG: Detail view Min/Max - Min: {single_cc['min_usage']}, Max: {single_cc['max_usage']}")
    # Sleep for 3 seconds before next update (faster refresh for live data)
    time.sleep(3)