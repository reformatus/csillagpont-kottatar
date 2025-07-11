# Csillagpont Kották 2025

Ez a 2025-ös csillagpont fesztivál kottatárja.

Véletlen tévedtél ide? A tárat a [Sófár Hangoló appban](https://app.sofarkotta.hu/) tudod használni.

## Automated Data Updates

This repository includes an automated system for fetching and updating song data from an external API. The system consists of:

### Files and Structure

- `updater/` - Contains Python scripts for data fetching and processing
- `docs/` - GitHub Pages compatible output directory
- `.github/workflows/update-songs.yml` - GitHub Actions workflow for automation

### Setup Instructions

1. **Configure GitHub Repository Settings**:
   - Go to your repository Settings → Secrets and variables → Actions
   - Add the following **Secret**:
     - `API_ROOT`: Your API endpoint URL
   - Add the following **Variable**:
     - `SITE_PATH`: Path where the site is hosted

2. **Install Dependencies** (for local testing):
   ```bash
   cd updater
   pip install -r requirements.txt
   ```

3. **Manual Execution** (for testing):
   ```bash
   cd updater
   # Set environment variables for local testing
   $env:API_ROOT="..."
   $env:SITE_PATH="..."
   python run_updater.py
   ```

4. **GitHub Actions Setup**:
   - The workflow is configured to run manually via GitHub Actions UI
   - Optional: Uncomment the schedule section in the workflow file for daily automated runs
   - The workflow will automatically commit changes if new data is found

### What It Does

- Fetches song list from the configured API
- Downloads individual song details and associated PDF/SVG files
- Updates file paths to work with GitHub Pages
- Properly handles URL-encoded filenames
- Only downloads files that have changed (using MD5 hash comparison)
- Updates the `lastUpdated` timestamp when changes are detected