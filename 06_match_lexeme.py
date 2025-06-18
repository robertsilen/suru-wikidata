import requests
import pandas as pd
import ast  # Add this import for literal_eval

def save_df_to_xlsx(df, path):
    # Output the modified dataframe to a new Excel file
    output_path = path.replace('.xlsx', '_wikidata.xlsx')
    output_path = path.replace('05', '06')
    df.to_excel(output_path, index=False)
    print(f"Output saved to {output_path}")

def get_lexeme_entity(lexeme_id):
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbgetentities",
        "ids": lexeme_id,
        "format": "json"
    }
    response = requests.get(url, params=params)
    return response.json()

def search_wikidata_objects(query, search_lang, query_lang):
    base_url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": query,
        "format": "json",
        "language": search_lang, # language of the search results
        "uselang": query_lang, # language of the query
        "type": "item",
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    
    # Check if 'search' key exists in response and has results
    if 'search' in data and len(data['search']) > 0:
        first_result = data['search'][0]
        return {
            'q_code': first_result['id'],
            'title': first_result['display']['label']['value']
        }
    return {'q_code': '', 'title': ''}

def search_wikidata_lexemes(query, search_category, search_lang, query_lang):
    base_url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": query,
        "format": "json",
        "language": search_lang, # language of the search results
        "uselang": query_lang, # language of the query
        "type": "lexeme",
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    
    # Check if 'search' key exists in response
    if 'search' not in data:
        print(f"Warning: No 'search' key in response for query: {query}")
        return {}
 
    if len(data['search']) > 0:
        for item in data['search']:
            #print(item)
            id = item['id']
            entity = get_lexeme_entity(id)
            entities = entity.get('entities')
            if entities is not None:
                senses = entities[id].get('senses', [])
                if len(senses) > 0:
                    objects = senses[0].get('claims').get('P5137')
                    if objects is not None and len(objects) > 0:    
                        object = objects[0].get('mainsnak').get('datavalue').get('value').get('id')
                    else:
                        object = ''
                else:
                    object = ''
            else:
                object = ''
            word = item['display']['label']['value']
            lang = item['display']['label']['language']
            category = item['display']['description']['value'].split(", ")[1]
            url = item['concepturi']
            if lang == search_lang and word == query and category == search_category:
                item = {'word': word, 'lang': lang, 'category': category, 'url': url, 'p5137': object}
                return item
    return {}

def add_wikidata_to_suru(df):
    # Initialize new columns with empty strings
    df['Lfi_value'] = ''
    df['Lfi_url'] = ''
    df['Lsv'] = ''
    df['p5137'] = ''
    # Iterate through each row in the dataframe
    i = 0
    # start from row 2309
    for index, row in df.iterrows():
        i = i + 1
        headword = row['headword']
        sanaluokka = row['Sanaluokka']
        print(f"{i} / {len(df)} Fetching L code for headword: {headword}")
        item = search_wikidata_lexemes(headword, sanaluokka, "fi", "fi")
        object = search_wikidata_objects(headword, "fi", "fi")
        print(f"{i} / {len(df)} {index} {headword} {sanaluokka} {item} {object}")
        df.at[index, 'Lfi_value'] = item.get('word', '')
        df.at[index, 'Lfi_url'] = item.get('url', '')
        df.at[index, 'p5137'] = item.get('p5137', '')

        translation_list_sv = row['translations']
        # Skip if translation_list_sv is NaN or None
        if pd.isna(translation_list_sv):
            df.at[index, 'Lsv'] = str([])
            continue
            
        # Handle case where translation_list_sv is a string
        if isinstance(translation_list_sv, str):
            # Split by semicolon and strip whitespace
            translations = [t.strip() for t in translation_list_sv.split(';')]
        else:
            translations = translation_list_sv
        Lsv_list = []
        sv_objects = []
        for translation in translations:
            print(f"{index} sv söker: {translation} {sanaluokka}")
            item = search_wikidata_objects(translation, "sv", "fi")
            object = search_wikidata_objects(translation, "sv", "fi")
            if item.get('word', '') != '':
                Lsv_list.append([item.get('word', ''), item.get('url', ''), item.get('p5137', '')])
            if object.get('q_code', '') != '':
                sv_objects.append([object.get('q_code', ''), object.get('title', '')])
        print(f"{index} Lsv hittade: {str(Lsv_list)}")
        print(f"{index} sv_objects: {str(sv_objects)}")
        df.at[index, 'Lsv'] = str(Lsv_list)

        df.at[index, 'object'] = object.get('q_code', '')+';'+object.get('title', '')
        df.at[index, 'sv_objects'] = str(sv_objects)
        # every 50 rows, save the dataframe to a xlsx
        if index % 50 == 0:
            save_df_to_xlsx(df, "suru_temp.xlsx")
    return df

#input_file_path = '04_cat.xlsx'
# input_file_path = '05_suom_lista.xlsx'
input_file_path = '05_vanligaste.xlsx'

suru_df = pd.read_excel(input_file_path)
print(suru_df.shape)
suru_df = add_wikidata_to_suru(suru_df)
save_df_to_xlsx(suru_df, input_file_path)