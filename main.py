from cmath import log
from re import I
from borsdata.borsdata_api import BorsdataAPI
from borsdata import constants as constants
import pandas as pd
import json
import numpy as np
import logging
from logging_setup import logger

# Call the setup_logger function to get the configured logger



from borsdata.borsdata_client import BorsdataClient

ROIC_ID = 36
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
    allowed_caps = ["Large Cap", "Mid Cap"]
    not_allowed_sectors = ["Finans & Fastighet", "Dagligvaror", "Energi", "Kraftförsörjning"]

    countries = BorsAPI.get_countries()
    countries.rename(columns={"name": "Country"}, inplace=True)

    sectors = BorsAPI.get_sectors()
    sectors.rename(columns={"name": "Sector"}, inplace=True)

    markets = BorsAPI.get_markets().drop("countryId", axis=1)
    markets.rename(columns={"name": "Cap"}, inplace=True)

    instruments = BorsAPI.get_instruments()

    instruments = instruments.merge(markets, left_on='marketId', right_on='id', how='left')
    instruments = instruments.merge(sectors, left_on='sectorId', right_on='id', how='left')
    instruments = instruments.merge(countries, left_on='countryId', right_on='id', how='left')

    #Only include Large and Mid Cap
    filtered_instruments = instruments["Cap"].isin(allowed_caps)
    instruments = instruments[filtered_instruments]

    #only include allowed sectors
    filtered_instruments = ~instruments['Sector'].isin(not_allowed_sectors)
    instruments = instruments[filtered_instruments]


    filtered_instruments = instruments["Country"] == "Sverige"
    instruments = instruments[filtered_instruments]

    instruments = instruments.head(5)

    logging.info(f"Number of Companies: {len(instruments)}")

        
        
    return instruments

def find_kpi_id_by_name(kpi_name):
    json_file_path = 'KPI_table.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r') as json_file:
        json_data = json.load(json_file)
    return json_data[kpi_name]

def rank_by_magic_formula(df, year):
    ROIC_LIST = []
    EY_LIST = []

    for index, insId in df.iterrows():
        logging.info(f"Index: {index}, Name: {insId['name']}")
        try:
            roc_history = BorsAPI.get_kpi_history(ins_id=index, kpi_id=ROIC_ID, report_type="year", price_type="mean")
            ROIC = roc_history.loc[year].iloc[1]
            ROIC_LIST.append(ROIC)
        except Exception as e:
            logging.error(f"Error fetching ROIC data for instrument {index}: {e}")
            ROIC_LIST.append(None)

        try:
            pe_history  = BorsAPI.get_kpi_history(ins_id=index, kpi_id=PRICE_PER_EARNINGS_ID, report_type="year", price_type="mean")
            PE = pe_history.loc[year].iloc[1]
            EY_LIST.append(1 / PE)
        except Exception as e:
            logging.error(f"Error fetching Price-to-Earnings data for instrument: {index}, company: {insId['name']}, {e}")
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
    df = df.sort_values(by='Magic Formula Rank')
    #df_sorted.to_json('output_file.json', orient='records')
    return df 

def get_price_data_for_all_instruments(df):
    prices_df = pd.DataFrame()
    insId_list = [ins_id for ins_id in df.index]
    try:
        price_data = BorsAPI.get_instrument_stock_prices_list([insId_list])
        prices_df = pd.concat([prices_df, price_data])
    except Exception as e:
        logging.error(f"Error fetching price data for instrument {insId_list}: {e}")

    return prices_df

#companies = filter_instruments()  # replace this with your list of IDs

#prices_df = get_price_data_for_all_instruments(companies)
#prices_df.to_json('output/output_file_price.json')

def main():
    try:
        companies = BorsAPI.get_instruments()
        companies = companies.head()
        #companies_sorted = rank_by_magic_formula(companies)
        BorsClient.breadth_large_cap_sweden()
        #return companies_sorted
        return None

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    df = filter_instruments

    #main()
    instruments = filter_instruments()
    instruments = rank_by_magic_formula(instruments, 2019)
    
    instruments.to_json('output/output_file.json', orient='records')