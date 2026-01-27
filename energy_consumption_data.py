"""
Energy Consumption Data Access
==============================
This script demonstrates how to access free energy consumption databases using Python.

Data Sources:
1. Our World in Data (OWID) - Energy dataset (CSV from GitHub)
2. World Bank Open Data API - Energy use indicators
3. U.S. Energy Information Administration (EIA) Open Data API (requires free API key)

Requirements:
    pip install pandas requests matplotlib
"""

import pandas as pd
import requests
import matplotlib.pyplot as plt


# =============================================================================
# SOURCE 1: Our World in Data - Energy Dataset (No API key required)
# =============================================================================

def load_owid_energy_data():
    """
    Load the Our World in Data (OWID) energy dataset directly from GitHub.

    This dataset includes energy consumption, production, and mix data for
    every country in the world, updated regularly. It covers:
    - Primary energy consumption
    - Per capita energy use
    - Energy mix (fossil fuels, nuclear, renewables)
    - Electricity generation by source
    - CO2 emissions from energy

    Returns:
        pd.DataFrame: Full energy dataset with columns for each metric.
    """
    url = (
        "https://raw.githubusercontent.com/owid/energy-data/"
        "master/owid-energy-data.csv"
    )
    print("Downloading OWID energy dataset...")
    df = pd.read_csv(url)
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns.")
    print(f"Countries/regions: {df['country'].nunique()}")
    print(f"Year range: {df['year'].min()} - {df['year'].max()}")
    return df


def explore_owid_data(df):
    """Print summary statistics and available columns for the OWID dataset."""
    print("\n--- OWID Energy Dataset Overview ---")
    print(f"Shape: {df.shape}")
    print(f"\nAvailable columns ({len(df.columns)}):")
    for col in sorted(df.columns):
        print(f"  - {col}")
    print(f"\nSample countries: {df['country'].unique()[:10].tolist()}")
    print(f"\nBasic statistics for primary energy consumption (TWh):")
    print(df["primary_energy_consumption"].describe())


def plot_owid_top_consumers(df, year=2022, top_n=10):
    """
    Plot the top N energy-consuming countries for a given year.

    Args:
        df: OWID energy DataFrame.
        year: Year to filter on.
        top_n: Number of top countries to display.
    """
    # Filter out aggregates (e.g., "World", "Asia", "Europe")
    aggregates = [
        "World", "Asia", "Europe", "North America", "South America",
        "Africa", "Oceania", "European Union (27)", "High-income countries",
        "Low-income countries", "Lower-middle-income countries",
        "Upper-middle-income countries",
    ]
    filtered = df[
        (df["year"] == year) & (~df["country"].isin(aggregates))
    ].dropna(subset=["primary_energy_consumption"])

    top = filtered.nlargest(top_n, "primary_energy_consumption")

    plt.figure(figsize=(12, 6))
    plt.barh(top["country"], top["primary_energy_consumption"], color="steelblue")
    plt.xlabel("Primary Energy Consumption (TWh)")
    plt.title(f"Top {top_n} Energy Consuming Countries ({year})")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig("top_energy_consumers.png", dpi=150)
    plt.show()
    print("Plot saved as 'top_energy_consumers.png'")


# =============================================================================
# SOURCE 2: World Bank Open Data API (No API key required)
# =============================================================================

def load_world_bank_energy_data(indicator="EG.USE.PCAP.KG.OE", start_year=2000,
                                 end_year=2022):
    """
    Fetch energy data from the World Bank Open Data API.

    Common energy indicators:
        - EG.USE.PCAP.KG.OE : Energy use (kg of oil equivalent per capita)
        - EG.USE.ELEC.KH.PC : Electric power consumption (kWh per capita)
        - EG.FEC.RNEW.ZS    : Renewable energy consumption (% of total)
        - EG.ELC.PETR.ZS     : Electricity production from oil sources (%)
        - EG.USE.COMM.FO.ZS  : Fossil fuel energy consumption (% of total)

    Args:
        indicator: World Bank indicator code.
        start_year: Start year for the query.
        end_year: End year for the query.

    Returns:
        pd.DataFrame: DataFrame with columns [country, country_code, year, value].
    """
    base_url = "https://api.worldbank.org/v2/country/all/indicator"
    records = []
    page = 1
    total_pages = 1

    print(f"Fetching World Bank indicator: {indicator}")

    while page <= total_pages:
        params = {
            "date": f"{start_year}:{end_year}",
            "format": "json",
            "per_page": 1000,
            "page": page,
        }
        resp = requests.get(f"{base_url}/{indicator}", params=params)
        resp.raise_for_status()
        data = resp.json()

        # First element is metadata, second is the data
        if len(data) < 2 or data[1] is None:
            print("No data returned for this indicator.")
            return pd.DataFrame()

        meta = data[0]
        total_pages = meta.get("pages", 1)

        for entry in data[1]:
            records.append({
                "country": entry["country"]["value"],
                "country_code": entry["countryiso3code"],
                "year": int(entry["date"]),
                "value": entry["value"],
            })

        page += 1

    df = pd.DataFrame(records)
    df = df.dropna(subset=["value"])
    print(f"Loaded {len(df)} records for {df['country'].nunique()} countries.")
    return df


def plot_world_bank_comparison(df, countries=None, indicator_name="Energy Use"):
    """
    Plot energy indicator over time for selected countries.

    Args:
        df: World Bank DataFrame from load_world_bank_energy_data().
        countries: List of country names to plot. Defaults to top 5 economies.
        indicator_name: Label for the y-axis.
    """
    if countries is None:
        countries = ["United States", "China", "India", "Germany", "Japan"]

    plt.figure(figsize=(12, 6))
    for country in countries:
        subset = df[df["country"] == country].sort_values("year")
        if not subset.empty:
            plt.plot(subset["year"], subset["value"], marker="o",
                     markersize=3, label=country)

    plt.xlabel("Year")
    plt.ylabel(indicator_name)
    plt.title(f"{indicator_name} Over Time")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("world_bank_energy_comparison.png", dpi=150)
    plt.show()
    print("Plot saved as 'world_bank_energy_comparison.png'")


# =============================================================================
# SOURCE 3: U.S. EIA Open Data API (Requires free API key)
# =============================================================================

def load_eia_data(api_key, route="total-energy/data",
                  frequency="annual", data_column="value"):
    """
    Fetch energy data from the U.S. Energy Information Administration (EIA) API v2.

    To get a free API key, register at: https://www.eia.gov/opendata/register.php

    Args:
        api_key: Your free EIA API key.
        route: API route (e.g., "total-energy/data", "electricity/retail-sales/data").
        frequency: Data frequency ("monthly", "quarterly", "annual").
        data_column: The data column to request.

    Returns:
        pd.DataFrame: EIA data as a DataFrame.
    """
    base_url = "https://api.eia.gov/v2"
    url = f"{base_url}/{route}"

    params = {
        "api_key": api_key,
        "frequency": frequency,
        "data[0]": data_column,
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 5000,
    }

    print(f"Fetching EIA data from: {route}")
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    if "response" in data and "data" in data["response"]:
        df = pd.DataFrame(data["response"]["data"])
        print(f"Loaded {len(df)} records from EIA.")
        return df
    else:
        print("No data returned. Check your API key and route.")
        return pd.DataFrame()


# =============================================================================
# MAIN - Run examples
# =============================================================================

def main():
    print("=" * 60)
    print("  Energy Consumption Data Access Demo")
    print("=" * 60)

    # --- Example 1: Our World in Data ---
    print("\n[1/2] Our World in Data - Energy Dataset")
    print("-" * 40)
    owid_df = load_owid_energy_data()
    explore_owid_data(owid_df)
    plot_owid_top_consumers(owid_df)

    # --- Example 2: World Bank ---
    print("\n[2/2] World Bank - Energy Use Per Capita")
    print("-" * 40)
    wb_df = load_world_bank_energy_data(
        indicator="EG.USE.PCAP.KG.OE",
        start_year=2000,
        end_year=2022,
    )
    if not wb_df.empty:
        plot_world_bank_comparison(
            wb_df,
            indicator_name="Energy Use (kg of oil equiv. per capita)",
        )

    # --- Example 3: EIA (uncomment and add your API key) ---
    # print("\n[3/3] U.S. EIA - Total Energy")
    # print("-" * 40)
    # EIA_API_KEY = "YOUR_FREE_API_KEY_HERE"
    # eia_df = load_eia_data(EIA_API_KEY)
    # if not eia_df.empty:
    #     print(eia_df.head(10))

    print("\nDone! Check the generated PNG files for visualizations.")


if __name__ == "__main__":
    main()
