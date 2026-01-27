"""
Export Energy Data to Google Sheets (for Tableau)
=================================================
This script fetches energy consumption data from Our World in Data and
uploads it to a Google Sheets spreadsheet that can be connected to Tableau.

Setup Instructions:
-------------------
1. Go to https://console.cloud.google.com/
2. Create a new project (or select an existing one)
3. Enable the "Google Sheets API" and "Google Drive API":
   - APIs & Services > Library > search "Google Sheets API" > Enable
   - APIs & Services > Library > search "Google Drive API" > Enable
4. Create a Service Account:
   - APIs & Services > Credentials > Create Credentials > Service Account
   - Give it a name (e.g., "energy-data-export")
   - Click "Done"
5. Create a JSON key for the service account:
   - Click on the service account > Keys > Add Key > Create New Key > JSON
   - Save the downloaded JSON file as "credentials.json" in this directory
6. Share your Google Sheet with the service account email:
   - Open the JSON file and copy the "client_email" value
   - In Google Sheets, click "Share" and add that email with Editor access

Requirements:
    pip install pandas gspread google-auth

Connecting to Tableau:
    - In Tableau, go to Data > New Data Source > Google Sheets
    - Select the spreadsheet created by this script
    - Tableau will auto-refresh from the sheet
"""

import sys
import os

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

from energy_consumption_data import load_owid_energy_data


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CREDENTIALS_FILE = os.environ.get(
    "GOOGLE_CREDENTIALS_FILE",
    os.path.join(os.path.dirname(__file__), "credentials.json"),
)

SPREADSHEET_NAME = "Energy Consumption Data"

# Columns to export (subset keeps the sheet manageable for Tableau)
EXPORT_COLUMNS = [
    "country",
    "iso_code",
    "year",
    "population",
    "gdp",
    "primary_energy_consumption",
    "energy_per_capita",
    "energy_per_gdp",
    "electricity_generation",
    "electricity_demand",
    "fossil_fuel_consumption",
    "fossil_share_energy",
    "renewables_consumption",
    "renewables_share_energy",
    "nuclear_consumption",
    "nuclear_share_energy",
    "coal_consumption",
    "oil_consumption",
    "gas_consumption",
    "hydro_consumption",
    "solar_consumption",
    "wind_consumption",
    "carbon_intensity_elec",
    "greenhouse_gas_emissions",
]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ---------------------------------------------------------------------------
# Google Sheets helpers
# ---------------------------------------------------------------------------

def authenticate(credentials_file: str) -> gspread.Client:
    """Authenticate with Google using a service account JSON key file."""
    if not os.path.exists(credentials_file):
        print(f"ERROR: Credentials file not found: {credentials_file}")
        print("See the setup instructions at the top of this script.")
        sys.exit(1)

    creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    client = gspread.authorize(creds)
    print("Authenticated with Google successfully.")
    return client


def get_or_create_spreadsheet(client: gspread.Client,
                              name: str) -> gspread.Spreadsheet:
    """Open an existing spreadsheet by name, or create a new one."""
    try:
        spreadsheet = client.open(name)
        print(f"Opened existing spreadsheet: '{name}'")
    except gspread.SpreadsheetNotFound:
        spreadsheet = client.create(name)
        print(f"Created new spreadsheet: '{name}'")
        # Make it accessible via link so Tableau can reach it
        spreadsheet.share("", perm_type="anyone", role="reader")
        print("Spreadsheet shared as view-only via link.")
    return spreadsheet


def upload_dataframe(spreadsheet: gspread.Spreadsheet,
                     df: pd.DataFrame,
                     worksheet_name: str = "Sheet1") -> None:
    """
    Upload a DataFrame to a worksheet, replacing all existing content.

    Google Sheets has a 10 million cell limit. For large datasets this
    function filters to country-level rows only (valid 3-letter ISO codes).
    """
    # Filter to actual countries only
    df = df[df["iso_code"].notna() & (df["iso_code"].str.len() == 3)].copy()

    # Replace NaN with empty string for Sheets compatibility
    df = df.fillna("")

    print(f"Preparing {len(df)} rows x {len(df.columns)} columns for upload...")

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
        worksheet.clear()
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name, rows=len(df) + 1, cols=len(df.columns)
        )

    # Convert to list-of-lists (header + rows)
    header = df.columns.tolist()
    rows = df.values.tolist()
    data = [header] + rows

    worksheet.update(data, value_input_option="USER_ENTERED")
    print(f"Uploaded {len(rows)} rows to worksheet '{worksheet_name}'.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Export Energy Data to Google Sheets")
    print("=" * 60)

    # 1. Load data
    print("\n[1/3] Loading energy data from Our World in Data...")
    df = load_owid_energy_data()

    # Keep only the columns we care about
    available = [c for c in EXPORT_COLUMNS if c in df.columns]
    df = df[available]
    print(f"Selected {len(available)} columns for export.")

    # 2. Authenticate
    print("\n[2/3] Authenticating with Google...")
    client = authenticate(CREDENTIALS_FILE)

    # 3. Upload
    print("\n[3/3] Uploading to Google Sheets...")
    spreadsheet = get_or_create_spreadsheet(client, SPREADSHEET_NAME)
    upload_dataframe(spreadsheet, df)

    url = spreadsheet.url
    print(f"\nDone! Spreadsheet URL:\n  {url}")
    print("\nTo connect in Tableau:")
    print("  1. Data > New Data Source > Google Sheets")
    print(f"  2. Select '{SPREADSHEET_NAME}'")
    print("  3. Drag the sheet onto the canvas and start building!")


if __name__ == "__main__":
    main()
