#!/usr/bin/env python3

import pandas as pd
from influxdb import InfluxDBClient
import datetime
import os
import re
import yaml
import requests
from typing import List, Dict, Any, Optional
import time

EG4_BASE_URL = "https://monitor.eg4electronics.com"
EG4_LOGIN_URL = f"{EG4_BASE_URL}/WManage/web/login"
EG4_MONITOR_URL = f"{EG4_BASE_URL}/WManage/web/monitor/inverter"
EG4_PLANT_LIST_URL = f"{EG4_BASE_URL}/WManage/web/config/plant/list/viewer"
EG4_INVERTER_LIST_URL = f"{EG4_BASE_URL}/WManage/web/config/inverter/list"

def read_config() -> Dict[str, Any]:
    """
    Read configuration from config.yaml
    """
    try:
        with open('config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading config file: {e}")
        raise

def _extract_user_id(html: str) -> Optional[str]:
    match = re.search(r"userId\s*=\s*'(\d+)'", html)
    return match.group(1) if match else None


def authenticate_eg4(username: str, password: str) -> Optional[requests.Session]:
    """Authenticate with EG4 Monitor Center and return a session with cookies."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    print("\n=== Starting Authentication ===")

    print(f"Requesting login page: {EG4_LOGIN_URL}")
    login_page = session.get(EG4_LOGIN_URL)
    login_page.raise_for_status()
    if 'JSESSIONID' not in session.cookies:
        print("Login failed: no JSESSIONID cookie received from login page")
        return None

    print(f"Attempting login for account: {username}")
    response = session.post(
        EG4_LOGIN_URL,
        data={'account': username, 'password': password},
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': EG4_BASE_URL,
            'Referer': EG4_LOGIN_URL,
        },
        allow_redirects=True,
    )
    response.raise_for_status()

    if 'loginDismatch' in response.text:
        print("Login failed: invalid username or password")
        return None

    user_id = _extract_user_id(response.text)
    if not user_id:
        print("Login failed: authenticated page did not include userId")
        return None

    print(f"Login successful (userId={user_id}, url={response.url})")
    return session


def _api_headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": EG4_BASE_URL,
        "Referer": EG4_MONITOR_URL,
        "X-Requested-With": "XMLHttpRequest",
    }


def get_plant_list(session: requests.Session) -> List[Dict[str, Any]]:
    """Fetch all sites/plants visible to the authenticated user."""
    response = session.post(
        EG4_PLANT_LIST_URL,
        headers=_api_headers(),
        data={
            "page": 1,
            "rows": 100,
            "searchText": "",
            "sort": "createDate",
            "order": "desc",
        },
    )
    response.raise_for_status()
    return response.json().get("rows", [])


def get_inverters_for_plant(session: requests.Session, plant_id: int) -> List[Dict[str, Any]]:
    """Fetch inverters belonging to a single plant/site."""
    response = session.post(
        EG4_INVERTER_LIST_URL,
        headers=_api_headers(),
        data={
            "page": 1,
            "rows": 100,
            "plantId": plant_id,
            "searchText": "",
            "targetSerialNum": "",
        },
    )
    response.raise_for_status()
    return response.json().get("rows", [])


def get_inverter_list(
    session: requests.Session,
    config: Dict[str, Any],
    *,
    all_sites: bool = False,
) -> List[Dict[str, Any]]:
    """Fetch plants, then resolve inverters and their site membership."""
    configured_ids = (
        set()
        if all_sites
        else {inv["id"] for inv in config["eg4_monitor"].get("inverters", [])}
    )

    plants = get_plant_list(session)
    inverters: List[Dict[str, Any]] = []

    print(f"Found {len(plants)} site(s):")
    for plant in plants:
        plant_id = plant["plantId"]
        plant_name = plant["name"]
        plant_inverters = get_inverters_for_plant(session, plant_id)

        print(f"  - {plant_name} (plantId={plant_id}, {len(plant_inverters)} inverter(s))")
        for row in plant_inverters:
            serial = row["serialNum"]
            print(f"      {serial} ({row.get('deviceTypeText', 'unknown')})")
            if configured_ids and serial not in configured_ids:
                continue
            inverters.append({
                "id": serial,
                "plant_id": plant_id,
                "plant_name": plant_name,
                "name": row.get("plantName", plant_name),
                "model": row.get("deviceTypeText", "unknown"),
            })

    if configured_ids:
        found_ids = {inv["id"] for inv in inverters}
        for serial in sorted(configured_ids - found_ids):
            print(f"  Warning: configured inverter {serial} not found on any site")
            inverters.append({
                "id": serial,
                "plant_id": None,
                "plant_name": "unknown",
                "name": serial,
                "model": "unknown",
            })

    return inverters

def download_eg4_data(session: requests.Session, config: Dict[str, Any], 
                     inverter_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Download data from EG4 Monitor Center for the specified inverter and date range
    """
    base_url = config['eg4_monitor']['base_url']
    
    # Construct the export URL
    export_url = f"{base_url}/export/{inverter_id}/{start_date}"
    params = {
        'endDateText': end_date
    }
    
    # Make the request to download data
    response = session.get(export_url, params=params)
    response.raise_for_status()
    
    # Save the XLS file temporarily
    temp_file = f"temp_data_{inverter_id}_{int(time.time())}.xls"
    with open(temp_file, 'wb') as f:
        f.write(response.content)
    
    try:
        # Read the XLS file
        df = pd.read_excel(temp_file)
        # Add inverter_id as a column
        df['inverter_id'] = inverter_id
        return df
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)

def prepare_influxdb_points(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convert DataFrame rows to InfluxDB points
    """
    points = []
    
    # Assuming the first column is timestamp and other columns are measurements
    timestamp_col = df.columns[0]
    
    for _, row in df.iterrows():
        timestamp = row[timestamp_col]
        if isinstance(timestamp, datetime.datetime):
            timestamp = timestamp.isoformat()
        
        for col in df.columns[1:]:  # Skip timestamp column
            if col == 'inverter_id':  # Skip the inverter_id column as it's a tag
                continue
            point = {
                "measurement": col,
                "time": timestamp,
                "tags": {
                    "inverter_id": row['inverter_id']
                },
                "fields": {
                    "value": float(row[col])
                }
            }
            points.append(point)
    
    return points

def write_to_influxdb(points: List[Dict[str, Any]], 
                     host: str = "localhost",
                     port: int = 8086,
                     database: str = "eg4_data",
                     username: str = None,
                     password: str = None) -> None:
    """
    Write points to InfluxDB
    """
    try:
        client = InfluxDBClient(
            host=host,
            port=port,
            username=username,
            password=password
        )
        
        # Create database if it doesn't exist
        client.create_database(database)
        client.switch_database(database)
        
        # Write points
        client.write_points(points)
        print(f"Successfully wrote {len(points)} points to InfluxDB")
        
    except Exception as e:
        print(f"Error writing to InfluxDB: {e}")
        raise
    finally:
        client.close()

def main():
    # Read configuration
    config = read_config()
    influxdb_config = config.get('influxdb', {})
    
    # Use today's date for both start and end date
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    try:
        session = authenticate_eg4(config['eg4_monitor']['username'], config['eg4_monitor']['password'])
        if session:
            print("=== Authentication Complete ===\n")

            print("Fetching sites and inverters...\n")
            inverters = get_inverter_list(session, config)

            if not inverters:
                raise Exception("No inverters matched the current configuration")

            print(f"\nProcessing {len(inverters)} configured inverter(s):")
            for inv in inverters:
                print(
                    f"  - {inv['plant_name']} / {inv['id']} "
                    f"(Model: {inv['model']})"
                )
            
            all_points = []
            
            # Process each inverter
            for inverter in inverters:
                inverter_id = inverter['id']
                print(
                    f"Downloading data for {inverter['plant_name']} / "
                    f"{inverter_id} for {today}..."
                )
                df = download_eg4_data(session, config, inverter_id, today, today)
                
                # Prepare points for InfluxDB
                print(f"Preparing data for InfluxDB for inverter {inverter_id}...")
                points = prepare_influxdb_points(df)
                all_points.extend(points)
            
            # Write to InfluxDB
            print("Writing to InfluxDB...")
            write_to_influxdb(
                points=all_points,
                host=influxdb_config.get('host', 'localhost'),
                port=influxdb_config.get('port', 8086),
                database=influxdb_config.get('database', 'eg4_data'),
                username=influxdb_config.get('username'),
                password=influxdb_config.get('password')
            )
            
        else:
            raise Exception("Authentication failed")
        
    except Exception as e:
        print(f"\nError: {e}")
        raise

if __name__ == "__main__":
    main() 