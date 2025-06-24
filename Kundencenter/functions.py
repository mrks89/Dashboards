import requests
from typing import Dict, List, Tuple

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
    
    def usage_per_day(self, sensor_id, start_date, end_date):
        """Retrieve consumption data for a specific period.
        Returns a list of dicts with 'date' and 'consumption' entries from dailyMetrics.
        """
        url = f"https://reseller-api.voltaware.com/sensors/{sensor_id}/stats/consumption?start={start_date}&end={end_date}"
        headers = {"Authorization": f"Bearer {self.get_access_token()}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        # Use 'dailyMetrics' from the response
        result = []
        for entry in data.get("dailyMetrics", []):
            result.append({
                "date": entry.get("date"),
                "consumption": entry.get("consumption")
            })

def get_day_with_max_consumption(daily_data):
    """Returns the entry (dict) with the maximum consumption."""
    if not daily_data:
        return None
    return max(daily_data, key=lambda x: x.get("consumption", 0))

def get_day_with_min_consumption(daily_data):
    """Returns the entry (dict) with the minimum consumption."""
    if not daily_data:
        return None
    return min(daily_data, key=lambda x: x.get("consumption", float("inf")))

def get_mean_consumption(daily_data):
    """Returns the mean consumption over all days."""
    if not daily_data:
        return 0
    total = sum(x.get("consumption", 0) for x in daily_data)
    return total / len(daily_data)

def get_sum_consumption(daily_data):
    """Returns the sum of consumption over all days."""
    if not daily_data:
        return 0
    return sum(x.get("consumption", 0) for x in in daily_data)
    

    

    