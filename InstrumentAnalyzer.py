import os
import matplotlib.pylab as plt
from borsdata.borsdata_api import BorsdataAPI
from borsdata import constants as constants
import pandas as pd
import numpy as np
import logging
from logging_setup import logger
from borsdata.borsdata_client import BorsdataClient
from user_input import UserInput

class InstrumentAnalyzer:
    ROIC_ID = 36
    PRICE_PER_EARNINGS_ID = 2
    API_KEY = constants.API_KEY
    annual_returns = []

    def __init__(self, number_of_companies, year_range, kpi_to_consider):
        self.BorsAPI = BorsdataAPI(self.API_KEY)
        self.BorsClient = BorsdataClient()
        self.portfolio = pd.DataFrame()
        self.number_of_companies = number_of_companies
        self.years = list(range(year_range[1], year_range[0]-1, -1))  # Goes from ex 2024 to 2004
        self.kpi_to_consider = kpi_to_consider


    def get_and_prepare_data(self):
        countries = self.BorsAPI.get_countries()
        countries.rename(columns={"name": "Country"}, inplace=True)

        sectors = self.BorsAPI.get_sectors()
        sectors.rename(columns={"name": "Sector"}, inplace=True)

        markets = self.BorsAPI.get_markets().drop("countryId", axis=1)
        markets.rename(columns={"name": "Cap"}, inplace=True)

        instruments = self.BorsAPI.get_instruments()
        instruments = instruments.merge(markets, left_on='marketId', right_on='id', how='left')
        instruments = instruments.merge(sectors, left_on='sectorId', right_on='id', how='left')
        instruments = instruments.merge(countries, left_on='countryId', right_on='id', how='left')

        return instruments

    def filter_by_cap(self, instruments, allowed_caps):
        filtered_instruments = instruments["Cap"].isin(allowed_caps)
        return instruments[filtered_instruments]

    def filter_by_sector(self, instruments, not_allowed_sectors):
        filtered_instruments = ~instruments['Sector'].isin(not_allowed_sectors)
        return instruments[filtered_instruments]

    def filter_by_country(self, instruments, country="Sverige"):
        filtered_instruments = instruments["Country"] == country
        return instruments[filtered_instruments]

    def filter_instruments(self, allowed_caps=None, not_allowed_sectors=None):
        allowed_caps = ["Large Cap", "Mid Cap"]
        not_allowed_sectors = ["Finans & Fastighet", "Dagligvaror", "Energi", "Kraftförsörjning"]

        instruments = self.get_and_prepare_data()
        instruments = self.filter_by_cap(instruments, allowed_caps)
        instruments = self.filter_by_sector(instruments, not_allowed_sectors)
        instruments = self.filter_by_country(instruments)
        if self.number_of_companies != 'all':
            instruments = instruments.head(self.number_of_companies)
        logging.info(f"Number of Companies: {len(instruments)}")
        return instruments

    def get_kpi_data(self, company_id):
        df_list = []
        for kpi_name, kpi_id in self.kpi_to_consider.items():
            kpi_df = self.BorsAPI.get_kpi_history(ins_id=company_id, kpi_id= kpi_id, report_type="year", price_type="mean") 
            kpi_df = kpi_df.rename(columns={"kpiValue": kpi_name})
            df_list.append(kpi_df)
        
        concatenated_df = pd.concat(df_list, axis=1)
        return concatenated_df

    def process_kpi_data(self, df):
        kpi_dataframe = pd.DataFrame()

        for company_id, insId in df.iterrows():
            try:
                kpi_data = self.get_kpi_data(company_id)

                if kpi_data.empty:
                    logging.error(f"No KPI data for Index: {company_id}, Name: {insId['name']}")
                    continue

                logging.info(f"Index: {company_id}, Name: {insId['name']}")

                kpi_data = kpi_data[kpi_data.index.isin(self.years)]  # filter years

                # Reshape kpi_data for the current company
                reshaped_data = kpi_data.drop(columns="period").stack().unstack(level=-2).T

                # Rename MultiIndex columns if applicable
                if isinstance(reshaped_data.columns, pd.MultiIndex):
                    reshaped_data.columns.set_names('year', level=0, inplace=True)

                reshaped_data['company_id'] = company_id

                # Append to the main dataframe
                kpi_dataframe = pd.concat([kpi_dataframe, reshaped_data.set_index('company_id', append=True).swaplevel(0, 1)])

            except Exception as e:
                logging.error(f"Error fetching ROIC data for Index: {company_id}, Name: {insId['name']}: {e}")
                raise e

        return kpi_dataframe



    def rank_by_magic_formula(self, df):
        kpi_dataframe = self.process_kpi_data(df)
        logging.info(kpi_dataframe.to_string())
        rank = self.calculate_ranks(df, kpi_data=kpi_dataframe)
        return rank
    
    def add_kpi_to_instrument_report(self, year, df, kpi_data):
        year_data = kpi_data.xs(year, level='year')
        #print(pd.concat([df, year_data], axis=1))
        year_data = pd.concat([df, year_data], axis=1)
        return year_data
        

    def calculate_ranks(self, df, kpi_data):
        best_ranked_by_year = {}
        # Iterate over unique years in kpi_data
        for year in kpi_data.index.get_level_values('year').unique():
            df_year = self.add_kpi_to_instrument_report(year, df.copy(), kpi_data)  # Create a copy of the original DataFrame
            magic_formula_rank = 0

            # Rank companies based on ROC and Earnings Yield for this specific year
            for column in kpi_data.columns:
                rank = df_year[str(column)].rank(ascending=False)
                # Handle NaN values by filling them with a large number (adjust as needed)
                rank.fillna(float('inf'), inplace=True)
                # Calculate the Magic Formula Rank
                magic_formula_rank += rank

            # Update the copy of the DataFrame with Magic Formula Rank
            df_year['Magic Formula Rank'] = magic_formula_rank

            # Sort df_year based on Magic Formula Rank
            df_year = df_year.sort_values(by='Magic Formula Rank')

            # Store the best ranked for this year
            best_ranked_by_year[year] = df_year.head(10).index.to_list()

            # Save rankings (you might want to consider saving outside the loop)
            self.save_rankings_to_file(df_year)

        logging.error(best_ranked_by_year)
        return best_ranked_by_year


    def save_rankings_to_file(self, df):
        folder_name = "companies_rank"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        for year in self.years:
            df.reset_index().to_json(f'{folder_name}/magic_rank_{int(year)}.json', orient='records')
        
        return None

    def calculate_annual_return(self, df, year):
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
        self.annual_returns.append(average_annual_return)
        return annual_returns

    def get_price_data_for_all_instruments(self, insId_list, year):
        try:
            prices_df = self.BorsAPI.get_instrument_stock_prices_list(insId_list)
            logging.info(f"Top ranked stocks year: {year} - {insId_list}")
            logging.error(f"Found stock prices for companies {prices_df.stock_id.unique().tolist()}")
            self.calculate_annual_return(prices_df, year)
        except Exception as e:
            logging.error(
                f"Error fetching price data for instrument {insId_list}: {e}")
            raise e

        return None

    def plot(self, df):
        plt.figure(figsize=(10, 6))
        plt.plot(self.years, self.annual_returns, color='blue', linewidth=1.5)
        plt.xlabel('Date')
        plt.ylabel('Annual Portfolio Return')
        plt.title('Annual Portfolio Return Over Time')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def main(self):
        try:
            instruments = self.filter_instruments()
            magic_rank = self.rank_by_magic_formula(instruments)
            for year, ranking in magic_rank.items():
                self.get_price_data_for_all_instruments(ranking, year)
            self.portfolio.to_json("test.json", orient="records")
            self.plot(instruments)
            return None

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            raise e


if __name__ == "__main__":

    user_input = UserInput()
    year_range = user_input.get_year_range()
    print(f"You chose the year range: {year_range[0]}-{year_range[1]}.")

    companies = user_input.get_company_count()
    if companies == "all":
        print("You chose to consider all companies.")
    else:
        print(f"You chose to consider {companies} companies.")

    selected_kpi_dict = user_input.select_kpis()
    print(selected_kpi_dict)

    analyzer = InstrumentAnalyzer(number_of_companies=companies, year_range=year_range, kpi_to_consider=selected_kpi_dict)
    #analyzer = InstrumentAnalyzer(number_of_companies=5, year_range=[2021, 2022], kpi_to_consider={"ROC": 36, "PE": 2, "EBIT/EV": 17})
    analyzer.main()