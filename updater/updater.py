import os
import json
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import hashlib
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

def download_file(url, local_path):
    """Download a file from URL to local path"""
    try:
        # Create directory if it doesn't exist
        ensure_directory_exists(local_path)
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded: {url} -> {local_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return False

def get_remote_file_hash(url):
    """Get MD5 hash of a remote file without downloading it completely"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        hash_md5 = hashlib.md5()
        for chunk in response.iter_content(chunk_size=8192):
            hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    except requests.exceptions.RequestException as e:
        print(f"Error getting hash for {url}: {e}")
        return None

def get_file_hash(file_path):
    """Get MD5 hash of a file"""
    if not os.path.exists(file_path):
        return None
    
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def process_song_files(song_data, base_dir, api_root):
    """Process PDF and SVG files for a song, download if needed"""
    files_updated = False
    
    print(f"Processing files for song: {song_data.get('title', 'Unknown')}")
    
    for field in ['pdf', 'svg']:
        if field in song_data and song_data[field]:
            original_path = song_data[field]
            print(f"Found {field} field: {original_path}")
            
            # Extract filename from path
            filename = os.path.basename(original_path)
            if not filename:
                print(f"No filename found in path: {original_path}")
                continue
                
            # Create local file path
            local_file_path = base_dir / "docs" / "files" / filename
            relative_path = f"/files/{filename}"
            
            print(f"Local file path: {local_file_path}")
            
            # Construct full URL if it's a relative path
            if original_path.startswith('/'):
                # Path starts with /, append to base host (not API path)
                from urllib.parse import urlparse
                parsed_api = urlparse(api_root)
                base_url = f"{parsed_api.scheme}://{parsed_api.netloc}"
                file_url = f"{base_url}{original_path}"
            elif original_path.startswith('http'):
                file_url = original_path
            else:
                # Already a relative path, construct the full URL from it
                if original_path.startswith('/files/'):
                    from urllib.parse import urlparse
                    parsed_api = urlparse(api_root)
                    base_url = f"{parsed_api.scheme}://{parsed_api.netloc}"
                    file_url = f"{base_url}/system/files/{filename}"
                else:
                    print(f"Skipping unknown path format: {original_path}")
                    continue
            
            print(f"Download URL: {file_url}")
            
            # Check if file needs to be downloaded
            should_download = True
            if local_file_path.exists():
                # Compare file hashes to see if remote file has changed
                print(f"Checking if remote file has changed: {filename}")
                local_hash = get_file_hash(str(local_file_path))
                remote_hash = get_remote_file_hash(file_url)
                
                if remote_hash is None:
                    print(f"Could not get remote hash for {file_url}, skipping download")
                    should_download = False
                elif local_hash == remote_hash:
                    print(f"File unchanged: {filename}")
                    should_download = False
                else:
                    print(f"File changed: {filename} (local: {local_hash[:8]}..., remote: {remote_hash[:8]}...)")
                    should_download = True
            else:
                print(f"File does not exist locally: {filename}")
            
            if should_download:
                print(f"Attempting to download: {file_url}")
                if download_file(file_url, str(local_file_path)):
                    files_updated = True
                    print(f"Successfully downloaded: {filename}")
                else:
                    print(f"Failed to download: {filename}")
            
            # Update the path in song data to relative path
            if song_data[field] != relative_path:
                song_data[field] = relative_path
                files_updated = True
                print(f"Updated {field} path: {original_path} -> {relative_path}")
        else:
            print(f"No {field} field found or empty")
    
    return files_updated

def update_songs_data():
    """Main function to fetch and save songs data"""
    # Get the base directory (one level up from updater)
    base_dir = Path(__file__).parent.parent
    
    # Track if any changes were made
    changes_made = False
    
    # Get current timestamp in ISO format
    current_timestamp = datetime.now().isoformat()
    
    # Fetch all songs
    songs_url = f"{API_ROOT}/songs"
    print(f"Fetching songs from: {songs_url}")
    
    songs_data = fetch_json_from_api(songs_url)
    if songs_data is None:
        print("Failed to fetch songs data")
        return
    
    # Save songs list to docs/api/songs/index.json
    songs_file_path = base_dir / "docs" / "api" / "songs" / "index.json"
    
    # Check if songs data has changed
    old_songs_hash = get_file_hash(str(songs_file_path)) if songs_file_path.exists() else None
    save_json_to_file(songs_data, str(songs_file_path))
    new_songs_hash = get_file_hash(str(songs_file_path))
    
    if old_songs_hash != new_songs_hash:
        changes_made = True
        print("Songs list updated")
    
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
        
        # Handle case where API returns an array with single song object
        if isinstance(song_details, list) and len(song_details) > 0:
            song_data = song_details[0]
        else:
            song_data = song_details
        
        print(f"Processing song: {song_data.get('title', 'Unknown')}")
        
        # Process files (PDF, SVG) and update paths
        files_updated = process_song_files(song_data, base_dir, API_ROOT)
        if files_updated:
            changes_made = True
        
        # Update the song_details with processed data
        if isinstance(song_details, list):
            song_details[0] = song_data
        else:
            song_details = song_data
        
        # Check if song data has changed
        song_file_path = base_dir / "docs" / "api" / "song" / str(uuid) / "index.json"
        old_song_hash = get_file_hash(str(song_file_path)) if song_file_path.exists() else None
        
        # Save individual song details to docs/api/song/UUID/index.json
        save_json_to_file(song_details, str(song_file_path))
        
        new_song_hash = get_file_hash(str(song_file_path))
        if old_song_hash != new_song_hash:
            changes_made = True
            print(f"Song {uuid} updated")
    
    # Update local about file with current timestamp only if changes were made
    if changes_made:
        print("Changes detected, updating about information...")
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
    else:
        print("No changes detected, lastUpdated field not modified")

if __name__ == "__main__":
    print("Starting data update...")
    print(f"Current timestamp: {datetime.now().isoformat()}")
    update_songs_data()
    print("Data update completed!")