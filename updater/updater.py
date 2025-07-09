import os
import json
import requests
from pathlib import Path
from datetime import datetime
from credentials import API_ROOT

def ensure_directory_exists(file_path):
    """Create directory structure if it doesn't exist"""
    directory = os.path.dirname(file_path)
    Path(directory).mkdir(parents=True, exist_ok=True)

def save_json_to_file(data, file_path):
    """Save JSON data to a file"""
    ensure_directory_exists(file_path)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved: {file_path}")

def fetch_json_from_api(url):
    """Fetch JSON data from API endpoint"""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def update_songs_data():
    """Main function to fetch and save songs data"""
    # Get the base directory (one level up from updater)
    base_dir = Path(__file__).parent.parent
    
    # Get current timestamp in ISO format
    current_timestamp = datetime.now().isoformat()
    
    # Update local about file with current timestamp
    print("Updating local about information...")
    about_file_path = base_dir / "docs" / "api" / "about" / "index.json"
    
    try:
        # Read existing about data
        with open(about_file_path, 'r', encoding='utf-8') as f:
            about_data = json.load(f)
        
        # Update the lastUpdated field
        about_data['lastUpdated'] = current_timestamp
        
        # Save updated about data
        save_json_to_file(about_data, str(about_file_path))
        print(f"Updated lastUpdated to: {current_timestamp}")
    except FileNotFoundError:
        print(f"About file not found at: {about_file_path}")
    except json.JSONDecodeError:
        print(f"Invalid JSON in about file: {about_file_path}")
    except Exception as e:
        print(f"Error updating about file: {e}")
    
    # Fetch all songs
    songs_url = f"{API_ROOT}/songs"
    print(f"Fetching songs from: {songs_url}")
    
    songs_data = fetch_json_from_api(songs_url)
    if songs_data is None:
        print("Failed to fetch songs data")
        return
    
    # Save songs list to docs/api/songs/index.json
    songs_file_path = base_dir / "docs" / "api" / "songs" / "index.json"
    save_json_to_file(songs_data, str(songs_file_path))
    
    # Extract song UUIDs and fetch individual song details
    if isinstance(songs_data, list):
        songs_list = songs_data
    elif isinstance(songs_data, dict) and 'songs' in songs_data:
        songs_list = songs_data['songs']
    elif isinstance(songs_data, dict) and 'data' in songs_data:
        songs_list = songs_data['data']
    else:
        # Assume the response is a list or try to extract UUIDs from keys
        songs_list = songs_data if isinstance(songs_data, list) else []
    
    print(f"Found {len(songs_list)} songs to process")
    
    for song in songs_list:
        # Extract UUID from song object
        if isinstance(song, dict):
            uuid = song.get('uuid') or song.get('id') or song.get('_id')
        elif isinstance(song, str):
            uuid = song
        else:
            print(f"Skipping invalid song entry: {song}")
            continue
            
        if not uuid:
            print(f"No UUID found for song: {song}")
            continue
        
        # Fetch individual song details
        song_url = f"{API_ROOT}/song/{uuid}"
        print(f"Fetching song details for UUID {uuid}")
        
        song_details = fetch_json_from_api(song_url)
        if song_details is None:
            print(f"Failed to fetch details for song {uuid}")
            continue
        
        # Save individual song details to docs/api/song/UUID/index.json
        song_file_path = base_dir / "docs" / "api" / "song" / str(uuid) / "index.json"
        save_json_to_file(song_details, str(song_file_path))

if __name__ == "__main__":
    print("Starting data update...")
    print(f"Current timestamp: {datetime.now().isoformat()}")
    update_songs_data()
    print("Data update completed!")