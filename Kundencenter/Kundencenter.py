import requests
import time
import streamlit as st
import plotly.express as px
import random
import datetime

from collections import Counter, defaultdict

def get_most_important_keys(disagg_dicts, top_n=5):
    """
    Returns the most common keys, the keys with the highest summed values, and all unique categories.
    
    Args:
        disagg_dicts (list): List of disaggregation dictionaries.
        top_n (int): Number of top keys to return.
        
    Returns:
        (list, list, list): (most_common_keys, highest_sum_keys, all_categories)
    """
    key_counter = Counter()
    value_sums = defaultdict(float)
    all_categories = set()
    
    for d in disagg_dicts:
        key_counter.update(d.keys())
        for k, v in d.items():
            value_sums[k] += v
            all_categories.add(k)
    
    most_common_keys = [k for k, _ in key_counter.most_common(top_n)]
    highest_sum_keys = sorted(value_sums, key=value_sums.get, reverse=True)[:top_n]
    all_categories = sorted(all_categories)
    
    return most_common_keys, highest_sum_keys, all_categories

class APIClient:
    BASE_URL = "https://smart-meter-reseller-api.voltaware.com"
    TOKEN_ENDPOINT = "/auth/token"
    REFRESH_ENDPOINT = "/auth/token/refresh"

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = 0

    def authenticate(self):
        """Authenticate and retrieve the initial access token."""
        url = f"{self.BASE_URL}{self.TOKEN_ENDPOINT}"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        self._update_tokens(data)

    def refresh_access_token(self):
        """Refresh the access token using the refresh token."""
        url = f"{self.BASE_URL}{self.REFRESH_ENDPOINT}"
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": self.refresh_token
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        self._update_tokens(data)

    def _update_tokens(self, data):
        """Update the tokens and expiry time."""
        self.access_token = data["access_token"]
        self.token_expiry = time.time() + data["expires_in_secs"]
        self.refresh_token = data.get("refresh_token")  # Only present in initial auth

    def get_access_token(self):
        """Get a valid access token, refreshing it if necessary."""
        if time.time() >= self.token_expiry:
            self.refresh_access_token()
        return self.access_token

    def get_disaggregation_results(self, sensor_id, date):
        """Retrieve disaggregation results for a sensor on a specific date."""
        url = f"https://reseller-api.voltaware.com/sensors/{sensor_id}/disag/day?date={date}"
        
        headers = {"Authorization": f"Bearer {self.get_access_token()}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_live_power(self, sensor_id):
        """Retrieve live power data for a sensor."""
        url = f"https://reseller-api.voltaware.com/sensors/{sensor_id}/stats/live"
        
        headers = {"Authorization": f"Bearer {self.get_access_token()}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

def make_grid(cols,rows):
    grid = [0]*cols
    for i in range(cols):
        with st.container():
            grid[i] = st.columns(rows)
    return grid

def get_all_disaggregation_keys_sorted_by_sum(sensors):
    """
    Returns a list of all unique keys found in the 'disaggregation' dicts of the sensors variable,
    sorted by their summed values (highest first).
    """
    value_sums = defaultdict(float)
    for sensor in sensors.values():
        for k, v in sensor.get("disaggregation", {}).items():
            value_sums[k] += v
    return [k for k, _ in sorted(value_sums.items(), key=lambda item: item[1], reverse=True)]

# Streamlit Web App
def run_streamlit_app(api_client):

    import plotly.colors

    # Todo: kW statt W
    # Legende vereinheitlichen
    # Größe checken

    st.set_page_config(layout="wide")
    st.title("BE-Kundencenter Dashboard")

    update_time = datetime.datetime.strptime("8:00", "%H:%M").time()

    sensors = {
        "21820":{"disaggregation":{}, "name":"Mattersburg"},
        "21189":{"disaggregation":{}, "name":"Eisenstadt"},
        "22097":{"disaggregation":{}, "name":"Jennersdorf"},
        "21821":{"disaggregation":{}, "name":"Oberwart"},
        "21822":{"disaggregation":{}, "name":"Oberpullendorf"},
        "22096":{"disaggregation":{}, "name":"Güssing"},
    }

    dis = []

    placeholder = st.empty()
    # Create two columns for the layout
    grid = make_grid(3,3)

    while True:
        current_time = datetime.datetime.now().time()

        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        for i, sensor_id in enumerate(sensors):
            try:
                # Fetch disaggregation results for the sensor
                data = api_client.get_disaggregation_results(sensor_id, yesterday)
                sensors[sensor_id]["disaggregation"] = data.get("consumption", {})
                dis.append(sensors[sensor_id]["disaggregation"])
            except requests.exceptions.RequestException as e:
                    st.error(f"Error fetching data for sensor {sensors[sensor_id]["name"]}: {e}")

        all_keys = get_all_disaggregation_keys_sorted_by_sum(sensors)

        # Assign a color to each key using Plotly's qualitative palette
        palette = [
            "#636EFA", "#00CC96", "#AB63FA", "#FFA15A",
            "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52",
            "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD",
            "#8C564B", "#E377C2", "#7F7F7F", "#BCBD22", "#17BECF"
        ]
        color_map = {key: palette[i % len(palette)] for i, key in enumerate(all_keys)}

        # Ensure all disaggregation dicts have all keys, fill missing with 0
        for sensor in sensors.values():
            for key in all_keys:
                if key not in sensor["disaggregation"]:
                    sensor["disaggregation"][key] = 0

        with placeholder.container():
                    # Draw custom legend in a single row using all_keys and color_map
            legend_html = ""
            for key in all_keys:
                color = color_map[key]
                legend_html += (
                    f'<span style="display:inline-block;width:16px;height:16px;background-color:{color};'
                    f'margin-right:8px;border-radius:3px;vertical-align:middle;"></span>'
                    f'<span style="margin-right:18px;vertical-align:middle;">{key}</span>'
                )
            st.markdown(legend_html, unsafe_allow_html=True)

            # create three columns
            col1, col2, col3 = st.columns(3)

            # Fetch and display results for each sensor
            for i, sensor_id in enumerate(sensors):
                consumption = sensors[sensor_id]["disaggregation"]
                consumption_labels = list(consumption.keys())
                consumption_values = list(consumption.values())

                data_live = api_client.get_live_power(sensor_id)
                live_power = data_live.get("consumption", {}).get("actualRaw", 0)/1000 # Convert from W to kW

                # Create the pie chart using Plotly with color mapping and no legend
                fig = px.pie(
                    values=consumption_values,
                    names=consumption_labels,
                    color=consumption_labels,
                    color_discrete_map=color_map,
                    hole=0.4
                )
                fig.update_layout(showlegend=False)
                # Set smaller margins and chart size
                fig.update_layout(
                    margin=dict(l=0, r=0, t=0, b=0),  # left, right, top, bottom
                    height=220,  # adjust as needed
                )

                col_index = i % 3
                if col_index == 0:
                    with col1:
                        st.metric(
                            label=f"{sensors[sensor_id]['name']}",
                            value=f"{live_power:.2f} kW",
                        )
                        st.plotly_chart(fig, key=f"{time.time()+random.randint(0, 100)}")
                elif col_index == 1:
                    with col2:
                        st.metric(
                            label=f"{sensors[sensor_id]['name']}",
                            value=f"{live_power:.2f} kW",
                        )
                        st.plotly_chart(fig, key=f"{time.time()+random.randint(0, 100)}")
                elif col_index == 2:
                    with col3:
                        st.metric(
                            label=f"{sensors[sensor_id]['name']}",
                            value=f"{live_power:.2f} kW",
                        )
                        st.plotly_chart(fig, key=f"{time.time()+random.randint(0, 100)}")
                   

        #if (current_time > update_time):
        #    st.rerun()
        time.sleep(10)

# Example usage:
if __name__ == "__main__":
    client_id = st.secrets["client_id"]  # Replace with your client ID
    client_secret = st.secrets["client_secret"]  # Replace with your client secret

    api_client = APIClient(client_id, client_secret)
    api_client.authenticate()

    # Run the Streamlit app
    run_streamlit_app(api_client)