import pandas as pd

file_path = 'DelayDelivery79.xlsx'
xl = pd.ExcelFile(file_path)

for sheet_name in xl.sheet_names:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    df.to_csv(f"{sheet_name}.csv", index=False)