import requests
import time
import streamlit as st
from threading import Thread
import matplotlib.pyplot as plt
import plotly.express as px
import random
import datetime

# TODO add variable date

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
        url = f"https://reseller-api.voltaware.com/sensors/{sensor_id}/disag/day?date=2025-05-04"
        
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

# Streamlit Web App
def run_streamlit_app(api_client):

    flag_updated = False
    do_update = False

    st.set_page_config(layout="wide")
    st.title("Kundencenter Dashboard")

    sensor_ids = ["21820", "21189", "22097","21821","21822"]

    update_time = datetime.datetime.strptime("8:00", "%H:%M").time()

    sensor_name = {
        "21820": "Mattersburg",
        "21189": "Eisenstadt",
        "22097": "Jennersdorf",
        "21821": "Oberwart",
        "21822": "Oberpullendorf"
    }

    placeholder = st.empty()
    # Create two columns for the layout
    grid = make_grid(3,2)

    while True:
        current_time = datetime.datetime.now().time()
        with placeholder.container():
            # create three columns
            col1, col2, col3 = st.columns(3)

            # Fetch and display results for each sensor
            for i, sensor_id in enumerate(sensor_ids):
                try:
                    # Fetch disaggregation results for the sensor
                    data = api_client.get_disaggregation_results(sensor_id, "2025-05-04")
                    consumption = data.get("consumption", {})
                    consumption_labels = list(consumption.keys())
                    consumption_values = list(consumption.values())

                    data_live = api_client.get_live_power(sensor_id)
                    live_power = data_live.get("consumption", {}).get("actualRaw", 0)

                    # Create the pie chart using Plotly
                    fig = px.pie(
                        values=consumption_values,
                        names=consumption_labels,
                        #title=f"{sensor_name[sensor_id]} - Live Power: {live_power} W",
                        hole=0.4  # Optional: Makes it a donut chart
                    )

                    # Determine the column and row index
                    col_index = i % 3  # Column index (0, 1, or 2)
                    #row_index = i // 3  # Row index (0 or 1)
                    if col_index == 0:                        
                        with col1:
                            st.metric(
                                label=f"{sensor_name[sensor_id]}",
                                value=f"{live_power} W",
                            )
                            
                            st.plotly_chart(fig)#, key=f"{sensor_name[sensor_id]+random.randint(0, 100)}")
                            
                    elif col_index == 1:
                        with col2:
                            st.metric(
                                label=f"{sensor_name[sensor_id]}",
                                value=f"{live_power} W",
                            )
                            st.plotly_chart(fig)#, key=f"{sensor_name[sensor_id]+random.randint(0, 100)}")
                    elif col_index == 2:
                        with col3:
                            st.metric(
                                label=f"{sensor_name[sensor_id]}",
                                value=f"{live_power} W",
                            )
                            st.plotly_chart(fig)#, key=f"{sensor_name[sensor_id]+random.randint(0, 100)}")
                   

                except requests.exceptions.RequestException as e:
                    st.error(f"Error fetching data for sensor {sensor_id}: {e}")

        #if (current_time > update_time):
        #    st.rerun()

        time.sleep(1)

# Example usage:
if __name__ == "__main__":
    client_id = st.secrets["client_id"]  # Replace with your client ID
    client_secret = st.secrets["client_secret"]  # Replace with your client secret

    api_client = APIClient(client_id, client_secret)
    api_client.authenticate()

    # Run the Streamlit app
    run_streamlit_app(api_client)