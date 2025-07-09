#!/usr/bin/env python3
"""
Song Data Updater

This script fetches song data from an API and saves it to the docs directory
for GitHub Pages compatibility.

Usage:
1. Update the API_ROOT in credentials.py with your actual API endpoint
2. Install dependencies: pip install -r requirements.txt
3. Run: python run_updater.py
"""

from updater import update_songs_data

if __name__ == "__main__":
    update_songs_data()
