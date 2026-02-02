import pandas as pd
import glob
import os

# Folder containing the Excel files
folder_path = os.getcwd()   # current folder
output_file = "Merged_Data.xlsx"

# Get all Excel files (exclude output file if re-run)
excel_files = [
    f for f in glob.glob(os.path.join(folder_path, "*.xlsx"))
    if os.path.basename(f) != output_file
]

all_data = []

for file in excel_files:
    df = pd.read_excel(file)
    all_data.append(df)

# Combine all dataframes
merged_df = pd.concat(all_data, ignore_index=True)

# Save to single Excel file
merged_df.to_excel(output_file, index=False)

print(f"✅ Merged {len(excel_files)} files into '{output_file}'")
