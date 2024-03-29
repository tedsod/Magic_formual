import os
import matplotlib.pylab as plt
from borsdata.borsdata_api import BorsdataAPI
from borsdata import constants as constants
import pandas as pd
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
years = list(range(2024, 2003, -1))  # Goes from 2024 to 2004

'''
Markets: OMX Stockholm
Sector: Energi osv

'''



def filter_instruments():
    allowed_caps = ["Large Cap", "Mid Cap"]
    not_allowed_sectors = ["Finans & Fastighet",
                           "Dagligvaror", "Energi", "Kraftförsörjning"]

    countries = BorsAPI.get_countries()
    countries.rename(columns={"name": "Country"}, inplace=True)

    sectors = BorsAPI.get_sectors()
    sectors.rename(columns={"name": "Sector"}, inplace=True)

    markets = BorsAPI.get_markets().drop("countryId", axis=1)
    markets.rename(columns={"name": "Cap"}, inplace=True)

    instruments = BorsAPI.get_instruments()

    instruments = instruments.merge(
        markets, left_on='marketId', right_on='id', how='left')
    instruments = instruments.merge(
        sectors, left_on='sectorId', right_on='id', how='left')
    instruments = instruments.merge(
        countries, left_on='countryId', right_on='id', how='left')

    # Only include Large and Mid Cap
    filtered_instruments = instruments["Cap"].isin(allowed_caps)
    instruments = instruments[filtered_instruments]

    # only include allowed sectors
    filtered_instruments = ~instruments['Sector'].isin(not_allowed_sectors)
    instruments = instruments[filtered_instruments]

    filtered_instruments = instruments["Country"] == "Sverige"
    instruments = instruments[filtered_instruments]

    instruments = instruments.head(10)

    logging.info(f"Number of Companies: {len(instruments)}")

    return instruments

def get_kpi_data(df):
    ROC_dictionary = {}
    EY_dictionary = {}

    for index, insId in df.iterrows():
        logging.info(f"Index: {index}, Name: {insId['name']}")
        try:
            roc_history = BorsAPI.get_kpi_history(
                ins_id=index, kpi_id=ROIC_ID, report_type="year", price_type="mean")
            roc_history = roc_history.rename(columns={"kpiValue": "ROC"})
            pe_history = BorsAPI.get_kpi_history(
                ins_id=index, kpi_id=PRICE_PER_EARNINGS_ID, report_type="year", price_type="mean")
            pe_history = pe_history.rename(columns={"kpiValue": "PE"})

            kpi_data = pd.concat([roc_history, pe_history], axis=1)
                    
            if kpi_data.empty:
                logging.error(f"No KPI data for {insId['name']}")
            for year in years:
                try:
                    roc = kpi_data.loc[int(year), "ROC"] # assuming the year in index is of type int
                    ey =  1/kpi_data.loc[int(year), "PE"] 
                except KeyError:
                    roc = None
                    ey = None

                if year in ROC_dictionary:
                    ROC_dictionary[year].append(roc)
                else:
                    ROC_dictionary[year] = [roc]

                if year in EY_dictionary:
                    EY_dictionary[year].append(ey)
                else:
                    EY_dictionary[year] = [ey]

        except Exception as e:
            logging.error(
                f"Error fetching ROIC data for instrument {index}: {e}")
    return EY_dictionary, ROC_dictionary

def rank_by_magic_formula(df, year=None):
    EY_dictionary, ROC_dictionary = get_kpi_data(df)
    best_ranked_by_year = calculate_ranks(df, EY_dictionary, ROC_dictionary)
    return best_ranked_by_year

def calculate_ranks(df, ROC_dictionary, EY_dictionary, year=None):
    best_ranked_by_year = {}
    for year in years:
        ROC = ROC_dictionary[year]
        EY = EY_dictionary[year]
        df["ROIC"] = ROC
        df["Earnings Yield"] = EY

        roic_rank = df['ROIC'].rank(ascending=False)
        ey_rank = df['Earnings Yield'].rank(ascending=False)

        # Calculate the Magic Formula Rank
        magic_formula_rank = roic_rank + ey_rank

        # Add the Magic Formula Rank as a new column to the DataFrame
        df['Magic Formula Rank'] = magic_formula_rank

        # Sort the DataFrame based on the Magic Formula Rank
        df = df.sort_values(by='Magic Formula Rank')
        best_ranked_by_year[year] = df.head(10).index.to_list()
        save_rankings_to_file(df)
    logging.error(best_ranked_by_year)
    return best_ranked_by_year

def save_rankings_to_file(df):
    folder_name = "companies_rank"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    for year in years:
        df.reset_index().to_json(f'{folder_name}/magic_rank_{int(year)}.json', orient='records')
    
    return None

def calculate_annual_return(df, year):
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])  # Ensure 'date' column is in datetime format
    df.set_index('date', inplace=True)  # Set 'date' as the DataFrame's index

    # Ensure the year exists in the data
    min_year = df.index.year.min()
    max_year = df.index.year.max()
    if year < min_year or year > max_year:
        print(f"No data available for the year {year}. Data is available for years {min_year} to {max_year}.")
        return None

    # Filter the DataFrame for the specific year
    df_year = df.loc[str(year)]

    # Group by 'stock_id'
    grouped = df_year.groupby('stock_id')

    # Define a function to calculate the annual return for a group
    def annual_return(group):
        start_price = group['close'].iloc[0]
        end_price = group['close'].iloc[-1]
        return (end_price / start_price) - 1

    # Apply the function to each group
    annual_returns = grouped.apply(annual_return)

    # If you want to print the annual return for each stock:
    for stock_id, return_value in annual_returns.items():
        logging.info(f'The annual return for stock_id {stock_id} in {year} is {return_value * 100:.2f}%')

    # If you want to return the average annual return across all stocks:
    average_annual_return = annual_returns.mean()
    logging.info(f'The average annual return across all stocks in {year} is {average_annual_return * 100:.2f}%')

    return annual_returns

def get_price_data_for_all_instruments(insId_list, year, portfolio):
    try:
        prices_df = BorsAPI.get_instrument_stock_prices_list(insId_list)
        logging.info(f"Top ranked stocks year: {year} - {insId_list}")
        logging.error(f"Found stock prices for companies {prices_df.stock_id.unique().tolist()}")
        calculate_annual_return(prices_df, year)
        portfolio = pd.concat([portfolio, get_year_data(prices_df, year)], axis=0)
    except Exception as e:
        logging.error(
            f"Error fetching price data for instrument {insId_list}: {e}")
        raise e

    return portfolio

def get_year_data(df, year):
    # Convert 'date' column to datetime format if needed
    df['date'] = pd.to_datetime(df['date'])

    # Filter the DataFrame for the desired year (using boolean indexing)
    df_year = df[df['date'].dt.year == year]

    # Call portfolio_return function to calculate the portfolio return for the year
    if df_year.empty:
        return None
    else:
        return portfolio_return(df_year, year)

def portfolio_return(df, year):
    # Assuming you have a DataFrame called 'df' with the stock price data
    # Selecting only the necessary columns for the new DataFrame
    df_prices = df[['date', 'open', 'close', 'stock_id']].copy()
    # Renaming the 'open' and 'close' columns to the respective stock_id
    df_prices.rename(columns={'open': 'stock_open', 'close': 'stock_close'}, inplace=True)

    # Pivot the DataFrame to have stock_id as columns and date as the index
    df_pivot = df_prices.pivot(index='date', columns='stock_id')
    # Calculate the daily returns for each stock
    df_returns = (df_pivot['stock_close'] - df_pivot['stock_open']) / df_pivot['stock_open']
    # Calculate the portfolio's daily return as the mean of individual stock returns
    df_returns['portfolio_return'] = df_returns.mean(axis=1)
    df_returns['portfolio_growth'] = 1 + df_returns['portfolio_return']

    # Group by year and calculate annual growth
    annual_growth = df_returns['portfolio_growth'].resample('Y').prod()

    # Create a new DataFrame with Date as the index and 'portfolio_return' as a new column
    annual_return = annual_growth - 1
    annual_return_year = annual_return[str(year)].values[0]

    # Calculate cumulative return
    df_returns['cumulative_return'] = df_returns['portfolio_growth'].cumprod()

    df_portfolio_return = df_returns[['portfolio_return', 'cumulative_return']].copy()

    logging.info(f"The annual return in {year} is {annual_return_year*100}%")
    return df_portfolio_return


def plot(df):
    plt.figure(figsize=(10, 6))
    plt.plot(df.index.to_list(), df['cumulative_return'], color='blue', linewidth=1.5)
    plt.xlabel('Date')
    plt.ylabel('Daily Portfolio Return')
    plt.title('Daily Portfolio Return Over Time')
    plt.grid(True)
    plt.tight_layout()
    plt.show()



def main():
    portfolio = pd.DataFrame()
    try:
        instruments = filter_instruments()
        magic_rank = rank_by_magic_formula(instruments)
        for year, ranking in magic_rank.items():
            portfolio = get_price_data_for_all_instruments(ranking, year, portfolio)
        portfolio.to_json("test.json", orient="records")
        plot(portfolio)
        return None

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise e


if __name__ == "__main__":

    main()

    
