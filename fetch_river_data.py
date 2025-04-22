import requests
import pandas as pd
from datetime import datetime
import time

# List of station IDs
stations = ["L1602", "L1708", "F1707", "L1707", "L1707A", "L1705A"]

# API base URL
base_url = "https://environment.data.gov.uk/flood-monitoring/id/stations"

# Function to get data for one station
def get_station_data(station_id):
    try:
        # Fetch station info
        response = requests.get(f"{base_url}/{station_id}")
        if response.status_code != 200:
            print(f"Error: Could not fetch data for station {station_id}")
            return None
        
        # Get the 'items' from response
        data = response.json()
        station_info = data.get("items", {})
        
        # Handle case where items is a list
        if isinstance(station_info, list):
            if not station_info:
                print(f"No station info found for station {station_id}")
                return None
            station_info = station_info[0]  # Take the first item
        
        # Get the measures URL
        measures = station_info.get("measures", {})
        if isinstance(measures, list):
            measures = measures[0] if measures else {}
        measures_url = measures.get("@id")
        if not measures_url:
            print(f"No measures found for station {station_id}")
            return None
        
        # Fetch the last two readings (limit to 2)
        readings_response = requests.get(f"{measures_url}/readings", params={"_limit": 2, "_sorted": "true"})
        if readings_response.status_code != 200:
            print(f"Error: Could not fetch readings for station {station_id}")
            return None
        
        readings = readings_response.json().get("items", [])
        if not readings:
            print(f"No readings found for station {station_id}")
            return None
        
        # Extract the latest reading
        latest_reading = readings[0]
        result = {
            "station_id": station_id,
            "station_name": station_info.get("label", "Unknown"),
            "river": station_info.get("riverName", "Unknown"),
            "value": latest_reading.get("value", None),
            "timestamp": latest_reading.get("dateTime", None),
            "status": "unknown"  # Default status
        }
        
        # Determine rising/dropping/stable if we have two readings
        if len(readings) >= 2:
            previous_reading = readings[1]
            latest_value = latest_reading.get("value")
            previous_value = previous_reading.get("value")
            if latest_value is not None and previous_value is not None:
                # Use a small threshold to account for minor fluctuations
                threshold = 0.001  # meters
                if latest_value > previous_value + threshold:
                    result["status"] = "rising"
                elif latest_value < previous_value - threshold:
                    result["status"] = "dropping"
                else:
                    result["status"] = "stable"
        
        return result
    except Exception as e:
        print(f"Error processing station {station_id}: {e}")
        return None

# Collect data for all stations
data_list = []
for station in stations:
    print(f"Fetching data for station {station}...")
    station_data = get_station_data(station)
    if station_data:
        data_list.append(station_data)
    time.sleep(1)  # Wait 1 second to avoid overwhelming the API

# Create a DataFrame (like a table)
if data_list:
    df = pd.DataFrame(data_list)
    # Save to CSV with timestamp in filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"river_data_{timestamp}.csv"
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")
else:
    print("No data was collected.")