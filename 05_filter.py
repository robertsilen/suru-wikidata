import pandas as pd

# Read the category Excel file
df_cat = pd.read_excel('suru-wikidata/04_cat.xlsx')

# Read the Finnish word list
df_suom_lista = pd.read_csv('kotus uppsl-med-suom-lista.txt', 
                           header=None, 
                           names=['word'])

# Read the most common searches Excel file
df_vanligaste = pd.read_excel('kotus Vanligaste sökningarna jan-mars 2025.xlsx',
                             usecols=['Label', 'Searches'])

# Print shapes to verify data was loaded
print("Category dataframe shape:", df_cat.shape)
print("Finnish word list shape:", df_suom_lista.shape)
print("Most common searches shape:", df_vanligaste.shape)

#merge df_cat and df_suom_lista on headword and word
df_merged1 = pd.merge(df_cat, df_suom_lista, left_on='headword', right_on='word', how='inner')
print(f"suom lista merged shape: {df_merged1.shape}")
df_merged1.to_excel('suru-wikidata/05_suom_lista.xlsx', index=False)

#merge df_merged and df_vanligaste on headword and Label
df_merged2 = pd.merge(df_cat, df_vanligaste, left_on='headword', right_on='Label', how='inner')
print(f"vanligaste merged shape: {df_merged2.shape}")
df_merged2.to_excel('suru-wikidata/05_vanligaste.xlsx', index=False)