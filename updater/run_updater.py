#!/usr/bin/env python3
"""
Song Data Updater

This script fetches song data from an API and saves it to the docs directory
for GitHub Pages compatibility.

Usage:
1. Set environment variables:
   - API_ROOT: Your API endpoint URL
   - SITE_PATH: Path where the site is hosted (optional)
2. Install dependencies: pip install -r requirements.txt
3. Run: python run_updater.py

Environment Variables:
- API_ROOT (required): The base URL of your API
- SITE_PATH (optional): The path prefix for your site
"""

import os
from updater import update_songs_data

if __name__ == "__main__":
    # Check if required environment variables are set
    if not os.getenv('API_ROOT'):
        print("ERROR: API_ROOT environment variable is required")
        print("Please set API_ROOT to your API endpoint URL")
        exit(1)
    
    update_songs_data()
