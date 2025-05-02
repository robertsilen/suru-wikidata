import pandas as pd

# Read the Excel file
suru_df = pd.read_excel('suru-wikidata/03_suru.xlsx')

# Read the TSV file (which has .txt extension)
# Since it's a TSV file, we'll use tab as the separator
nykysuomi_df = pd.read_csv('suru-wikidata/nykysuomensanalista2024.txt', sep='\t')

# Display basic information about the dataframes
print("\nSURU DataFrame Info:")
print(suru_df.info())
print("\nFirst few rows of SURU data:")
print(suru_df.head())

print("\nNykysuomen sanalista DataFrame Info:")
print(nykysuomi_df.info())
print("\nFirst few rows of Nykysuomen sanalista data:")
print(nykysuomi_df.head())

# Merge the dataframe on column headword in suku_df and "Hakusana" in nykysuomi_df
merged_df = pd.merge(suru_df, nykysuomi_df, left_on='headword', right_on='Hakusana', how='left')

# Display the merged dataframe
print("\nMerged DataFrame:")
print(merged_df.head())

# Save the merged dataframe to a new Excel file
merged_df.to_excel('04_cat.xlsx', index=False)

print("\nMerged dataframe saved to '04_cat.xlsx'")
print(f"Total rows: {len(merged_df)}")