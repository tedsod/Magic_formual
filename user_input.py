import json

class UserInput:
    def __init__(self, kpi_file_path="source/KPI_table.json"):
        self.kpi_file_path = kpi_file_path

    def get_year_range(self):
        while True:
            try:
                start_year = int(input("Enter the starting year (2004-2024): "))
                if not 2004 <= start_year <= 2024:
                    print("Starting year should be between 2004 and 2024. Please try again.")
                    continue
                
                while True:
                    end_year = int(input("Enter the ending year (2004-2024): "))
                    if not 2004 <= end_year <= 2024:
                        print("Ending year should be between 2004 and 2024. Please try again.")
                        continue
                    
                    if start_year < end_year:
                        return (start_year, end_year)
                    else:
                        print("Starting year should be strictly less than the ending year. Please try again.")
            except ValueError:
                print("Please enter valid year values. Try again.")


    def get_company_count(self):
        while True:
            choice = input("How many companies do you want to consider? Enter a number (1-600) or 'all': ").strip().lower()
            if choice == "all":
                return "all"
            try:
                count = int(choice)
                if 1 <= count <= 600:
                    return count
                else:
                    print("Please enter a number between 1 and 600 or 'all'. Try again.")
            except ValueError:
                print("Invalid input. Please enter a number between 1 and 600 or 'all'. Try again.")

    def select_kpis(self):
        with open(self.kpi_file_path, 'r') as file:
            kpi_table = json.load(file)
        
        print("Available KPIs:")
        kpi_keys = list(kpi_table.keys())
        for idx, kpi in enumerate(kpi_keys, 1):
            print(f"{idx}. {kpi}")

        pre_selected_indices = [24, 11]  # Indices 24 and 11 are pre-selected

        selected_indices_input = input("Select KPIs by entering their numbers separated by commas (e.g., 1,3,5) (NOTE EBIT/EV & ROC is preselected): ").strip()

        if not selected_indices_input:  # If input is empty, use pre-selected indices
            selected_indices = pre_selected_indices
        else:
            try:
                selected_indices = [int(idx.strip()) for idx in selected_indices_input.split(',')]
                selected_indices.extend(pre_selected_indices)  # Add pre-selected indices
                selected_indices = list(set(selected_indices))  # Remove duplicates

                if any(idx <= 0 or idx > len(kpi_keys) for idx in selected_indices):
                    print("Invalid input. Please enter valid numbers within the range.")
                    return None

            except ValueError:
                print("Invalid input. Please enter valid numbers separated by commas.")
                return None

        selected_kpis = {kpi_keys[idx - 1]: kpi_table[kpi_keys[idx - 1]] for idx in selected_indices}
        return selected_kpis




'''
# To use the class:
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
'''