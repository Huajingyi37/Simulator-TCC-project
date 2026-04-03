# Aura-IQ Public Reports Directory

This directory (`public/reports/`) contains all publicly accessible CSV simulation results from the Aura-IQ Building Energy Management System.

## Overview

- **Location**: `public/reports/`
- **Access**: HTTP REST API via Flask server running on `http://localhost:5000`
- **Format**: CSV (Comma-Separated Values)
- **Permissions**: Publicly readable

## Available Endpoints

### 1. Home (API Info)
```
GET http://localhost:5000/
```
Returns list of all available endpoints.

### 2. Run New Simulation
```
POST http://localhost:5000/api/simulate?scenarios=20
```
- Optional parameter: `scenarios` (default: 20)
- Returns: JSON with simulation summary and download URL
- Creates and saves a new timestamped CSV file

**Example:**
```bash
curl -X POST "http://localhost:5000/api/simulate?scenarios=50"
```

### 3. List All Reports
```
GET http://localhost:5000/api/reports
```
Returns JSON list of all available CSV files with download URLs.

### 4. Download Report
```
GET http://localhost:5000/api/reports/<filename>
GET http://localhost:5000/static/reports/<filename>
```
Returns the CSV file as a downloadable attachment.

**Example:**
```bash
curl http://localhost:5000/api/reports/aura_iq_simulation_20260402_150342.csv > report.csv
```

### 5. Get Report Summary (JSON)
```
GET http://localhost:5000/api/summary/<filename>
```
Returns JSON summary of a specific report without downloading the full CSV.

## CSV File Format

Each CSV contains:
- **Name**: Scenario identifier
- **Description**: Scenario details
- **Outlook Booked**: Calendar booking status (True/False)
- **WiFi Count**: Number of connected devices
- **Tenant Complaint**: Complaint flag (True/False)
- **Logic Action**: AI decision taken
- **Energy Reduction %**: Percentage of energy saved
- **Hourly Savings SGD**: Cost savings in Singapore Dollars
- **Energy Saved kWh**: Kilowatt-hours saved
- **Carbon Avoided Tonnes**: Carbon emissions avoided

Last row contains TOTAL aggregates.

## Setup & Usage

### Option 1: Using Bash Script
```bash
chmod +x start_server.sh
./start_server.sh
```

### Option 2: Manual Start
```bash
python3 -m pip install -r requirements.txt
python3 extension.py
```

## Python Client Example

```python
import requests
import json

# Run a new simulation
response = requests.post('http://localhost:5000/api/simulate?scenarios=30')
result = response.json()
print(f"Simulation Result: {json.dumps(result, indent=2)}")

# List all reports
reports = requests.get('http://localhost:5000/api/reports').json()
print(f"Available Reports: {reports['reports']}")

# Download a specific report
filename = reports['reports'][0]
csv_response = requests.get(f'http://localhost:5000/api/reports/{filename}')
with open(f'downloaded_{filename}', 'wb') as f:
    f.write(csv_response.content)

# Get report summary
summary = requests.get(f'http://localhost:5000/api/summary/{filename}').json()
print(f"Report Summary: {json.dumps(summary, indent=2)}")
```

## cURL Examples

### Run simulation
```bash
curl -X POST "http://localhost:5000/api/simulate?scenarios=25"
```

### List reports
```bash
curl "http://localhost:5000/api/reports"
```

### Download report
```bash
curl "http://localhost:5000/api/reports/aura_iq_simulation_20260402_150342.csv" -o report.csv
```

### Get report summary
```bash
curl "http://localhost:5000/api/summary/aura_iq_simulation_20260402_150342.csv"
```

## File Naming Convention

Files are automatically named with timestamps:
```
aura_iq_simulation_YYYYMMDD_HHMMSS.csv
```

Example: `aura_iq_simulation_20260402_150342.csv`

## Accessing Files Directly

Once the server is running, you can access CSV files through:

1. **REST API**: `http://localhost:5000/api/reports/<filename>`
2. **Static Directory**: `http://localhost:5000/static/reports/<filename>`
3. **File System**: `./public/reports/<filename>`

## Notes

- All files are stored in UTF-8 encoding
- Files are timestamped to prevent overwrites
- Statistics update automatically as new simulations run
- Server runs on `0.0.0.0:5000` (accessible from any interface)

---
**Aura-IQ**: Turning ESG from a cost into a financial asset.
