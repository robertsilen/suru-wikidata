# suru-wikidata


Code related to project to improve on lexemes in Wikidata with data from "Great Finnish-Swedish word list" published by "Institute for the Languages of Finland". More on project at https://sv.wikipedia.org/wiki/Wikipedia:Projekt_Fredrika/Suru. 

## Steps

### 1. Download XML files

Download suru.zip from from https://kotus.fi/kotus/kieliaineistot/aineistot-verkossa/ and unzip it to directory ```suru```. Terminal commands on Mac OS: 

```
curl -O https://kaino.kotus.fi/lataa/suru.zip
unzip suru.zip -d suru
```

### 2. Overview

Run ```02_overview_pretty.py``` to iterate all XML files and
1. count amount of DictionaryEntry tags, 
2. save XML files in prettified format for readibility and easier debugging,
3. compile structure of DictionaryEntry tags to 02_xml_structure.xml

```
Prettified xml files will be saved in: suru_pretty/
SuRu-000-aah.xml, DictionaryEntry tags: 987
SuRu-001-ajatella.xml, DictionaryEntry tags: 1002
SuRu-002-alppikiipeily.xml, DictionaryEntry tags: 1014
...
SuRu-110-ymparistomerkki.xml, DictionaryEntry tags: 996
SuRu-111-oljylammitteinen.xml, DictionaryEntry tags: 111
Total DictionaryEntry items: 110811 in 112 files
```

### 3. Convert XML to xlsx

Run ```03_suru_xlsx.py``` and output ```03_suru.xlsx``` with following columns with extracted XML tag texts - chosen with the help of ```02_xml_structure.xml```.

- For each ```.//DictionaryEntry```
  - suru_id: get id value, e.g. "SURU_a57ab4b712842b937486ecf07adf5df0"
  - within ```.//HeadwordCtn```
    - headword: ```Headword```
    - subcategorisation: ```SubCategorisation```
    - seealso: ```SeeAlso``` ("KS" or none)
  - within ```.//TranslationBlock```
    - translations: ```TranslationCtn/Translation``` (possibly several)
  - for each ```.//SenseGrp``` (possibly several)
    - sense_groups: ```TranslationCtn``` (possibly several)

### 4. Add word category to xlsx

Add Finnish word category (such as verb, noun, etc.) needed to identify correct Wikidata lexeme: 

1. Download the word list: 
```
curl -O https://kaino.kotus.fi/lataa/nykysuomensanalista2024.txt
```
2. Run ```04_word_cat.py```

```Total rows: 111765```

### 5. Filter to subset to work on

Run ```05_filter.py``` to filter to smaller subsets with: 

1. All existing Finnish Wikidata lexemes, https://w.wiki/DfFQ
2. Most searched for words in Suru
3. Finland specific words in Suru

### 6. Fetch Wikidata lexeme details

Run ```06_match_lexeme.py``` to match Finnish headwords and Swedish translations to Wikidata lexemes. Fetch Wikidata object for lexeme sense.

### 7. Create new lexemes (or add suru_id to existing lexemes)

## 7.1 Create indvidiaul lexemes 

Use ```07_create_lex.py``` to create new lexemes with suru_id, sense and object. 

## 7.2 Create lexemes with browser extension

To update and create lexemes while browsing https://kaino.kotus.fi/finsk-svensk/: load folder ```suru-wikidata-extension``` in a Chrome compatible browser at [chrome://extensions](chrome://extensions). 

To use the extension widget's "create lexem with flask" link, run ```python 07_create_lex_flask.py``` . Requires [LexData](https://nudin.github.io/LexData/) and adding a .env file with WIKI_USERNAME, WIKI_PASSWORD and WIKI_EMAIL for authentication. 