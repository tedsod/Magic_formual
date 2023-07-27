from borsdata.borsdata_api import BorsdataAPI
from borsdata import constants as constants
import pandas as pd
import json

from borsdata.borsdata_client import BorsdataClient

ROIC_ID = 37
PRICE_PER_EARNINGS_ID = 2
MARKET_CAP_ID = 49
API_KEY = constants.API_KEY
BorsAPI = BorsdataAPI(API_KEY)
BorsClient = BorsdataClient()

'''
Markets: OMX Stockholm
Sector: Energi osv

'''

def filter_instruments():
    countries = BorsAPI.get_countries()
    countries.rename(columns={"name": "Country"}, inplace=True)
    #branches = BorsAPI.get_branches()

    sectors = BorsAPI.get_sectors()
    sectors.rename(columns={"name": "Sector"}, inplace=True)
    print(sectors)
    markets = BorsAPI.get_markets().drop("countryId", axis=1)
    markets.rename(columns={"name": "Cap"}, inplace=True)

    instruments = BorsAPI.get_instruments()
    instruments = instruments.head(10)

    instruments = instruments.merge(markets, left_on='marketId', right_on='id', how='left')
    instruments = instruments.merge(sectors, left_on='sectorId', right_on='id', how='left')
    #instruments = instruments.merge(branches, left_on='branchId', right_on='id', how='left')
    instruments = instruments.merge(countries, left_on='countryId', right_on='id', how='left')
    #print(instruments)
    #instruments.to_json('output_file.json', orient='records')
    return instruments

def find_kpi_id_by_name(kpi_name):
    json_file_path = 'KPI_table.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r') as json_file:
        json_data = json.load(json_file)
    return json_data[kpi_name]

def rank_by_magic_formula(df):
    ROIC_LIST = []
    EY_LIST = []
    for insId in df.index:
        try:
            ROIC = BorsAPI.get_kpi_data_instrument(ins_id=insId, kpi_id=ROIC_ID, calc_group="1year", calc="mean")
            ROIC_LIST.append(ROIC["valueNum"].iloc[0])
        except Exception as e:
            print(f"Error fetching ROIC data for instrument {insId}: {e}")
            ROIC_LIST.append(None)

        try:
            PE = BorsAPI.get_kpi_data_instrument(ins_id=insId, kpi_id=PRICE_PER_EARNINGS_ID, calc_group="1year", calc="mean")
            EY_LIST.append(1 / PE["valueNum"].iloc[0])
        except Exception as e:
            print(f"Error fetching Price-to-Earnings data for instrument {insId}: {e}")
            EY_LIST.append(None)

    df["ROIC"] = ROIC_LIST
    df["Earnings Yield"] = EY_LIST

    roic_rank = df['ROIC'].rank(ascending=False)
    ey_rank = df['Earnings Yield'].rank(ascending=False)

    # Calculate the Magic Formula Rank
    magic_formula_rank = roic_rank + ey_rank

    # Add the Magic Formula Rank as a new column to the DataFrame
    df['Magic Formula Rank'] = magic_formula_rank

    # Sort the DataFrame based on the Magic Formula Rank
    df_sorted = df.sort_values(by='Magic Formula Rank')
    print(df_sorted)
    #df_sorted.to_json('output_file.json', orient='records')
    return df_sorted 

def main():
    try:
        companies = BorsAPI.get_instruments()
        companies = companies.head()
        #companies_sorted = rank_by_magic_formula(companies)
        BorsClient.breadth_large_cap_sweden()
        #return companies_sorted
        return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    #main()
    #BorsAPI.get_kpi_history(10, 27, "year", "mean")
    #BorsAPI.get_kpi_summary(10, "year")
    instruments = filter_instruments()
    instruments = rank_by_magic_formula(instruments)
    instruments.to_json('output_file.json', orient='records')