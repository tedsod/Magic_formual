import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

class IndexChangePlotter:
    def __init__(self):
        self.years = [
            2004, 2005, 2006, 2007, 2008, 2009,
            2010, 2011, 2012, 2013, 2014, 2015,
            2016, 2017, 2018, 2019, 2020, 2021, 2022
        ]
        
        self.change_in_index = [
            16.59, 29.40, 19.51, -5.74, -38.75, 43.69,
            21.42, -14.51, 11.83, 20.66, 9.87, -1.21,
            4.86, 3.94, -10.67, 25.78, 5.80, 29.07, -15.55
        ]

        sns.set(style='darkgrid')

    def plot(self, years, annual_returns):
        plt.figure(figsize=(10, 6))
        
        # Plot Change in Index
        plt.plot(self.years, self.change_in_index, marker='o', linestyle='-', color='b', label='Change in Index')
        
        # Plot Annual Returns from DataFrame
        plt.plot(years, annual_returns ,marker='o', linestyle='-', color='r', label='Annual Returns')

        plt.xlabel('Year')
        plt.ylabel('Value')
        plt.title('Change in Index and Annual Returns Over Years')
        plt.legend()

        plt.grid(True)
        plt.ylim(min(min(self.change_in_index), min(annual_returns)) - 10,
                 max(max(self.change_in_index), max(annual_returns)) + 10)

        plt.tight_layout()
        plt.show()
'''
# Example DataFrame with Annual Returns
data = {
    'Year': [2004, 2005, 2006],
    'Annual Returns': [10.2, 12.5, 8.7]
}

df = pd.DataFrame(data)

# Create an instance of the class and plot
plotter = IndexChangePlotter()
plotter.plot(df)
'''