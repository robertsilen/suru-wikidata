import logging
import pandas as pd
import json
import uuid
import os
from dotenv import load_dotenv

import LexData
from LexData.language import en
from LexData.claim import Claim
fi = LexData.Language("fi", "Q1412")
import requests

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)

# Get credentials from environment variables
wiki_username = os.getenv("WIKI_USERNAME")
wiki_password = os.getenv("WIKI_PASSWORD")
wiki_email = os.getenv("WIKI_EMAIL")
quickstatement_token = os.getenv("QUICKSTATEMENT_TOKEN")

if not wiki_username or not wiki_password:
    raise ValueError("WIKI_USERNAME and WIKI_PASSWORD must be set in .env file")

repo = LexData.WikidataSession(wiki_username, wiki_password)
categories = {
    "noun": "Q1084",
    "adjective": "Q34698",
}

def add(lang, lemma, category, suru_id, sv_gloss, betydelse_objekt):
    category_id = categories.get(category, None)
    if category_id is None:
        raise ValueError(f"Unknown category for {lang} {lemma}: {category}")

    # Find or create lexeme
    L2 = LexData.get_or_create_lexeme(repo, lemma, fi, category_id)
    lexeme_id = L2['id']
    print(f"Created lexeme for {lang}:{lemma}, {category}, URL: https://www.wikidata.org/wiki/Lexeme:{lexeme_id}")

    # Add P12682 claim to the lexeme with suru_id
    if suru_id is not None:
        suru_property = "P12682"
        suru_value = suru_id.replace("SURU_", "")    
        
        # Use Wikidata API directly with proper authentication
        api_url = "https://www.wikidata.org/w/api.php"
        
        # Create session and authenticate
        session = requests.Session()
        session.headers.update({
            'User-Agent': f'SuruWikidataBot/1.0 (https://github.com/robertsilen/suru-wikidata; {wiki_email})'
        })
        
        # Step 1: Get login token
        login_token_params = {
            'action': 'query',
            'meta': 'tokens',
            'type': 'login',
            'format': 'json'
        }
        
        login_token_response = session.get(api_url, params=login_token_params)
        if login_token_response.status_code != 200:
            print(f"Failed to get login token. Status: {login_token_response.status_code}")
            return None
            
        login_token_data = login_token_response.json()
        login_token = login_token_data['query']['tokens']['logintoken']
        print(f"Got login token: {login_token}")
        
        # Step 2: Perform login
        login_data = {
            'action': 'login',
            'lgname': wiki_username,
            'lgpassword': wiki_password,
            'lgtoken': login_token,
            'format': 'json'
        }
        
        login_response = session.post(api_url, data=login_data)
        if login_response.status_code != 200:
            print(f"Failed to login. Status: {login_response.status_code}")
            return None
            
        login_result = login_response.json()
        if login_result.get('login', {}).get('result') != 'Success':
            print(f"Login failed: {login_result}")
            return None
            
        print("Successfully logged in to Wikidata")
        
        # Step 3: Get CSRF token for editing
        csrf_token_params = {
            'action': 'query',
            'meta': 'tokens',
            'type': 'csrf',
            'format': 'json'
        }
        
        csrf_response = session.get(api_url, params=csrf_token_params)
        if csrf_response.status_code == 200:
            csrf_data = csrf_response.json()
            csrf_token = csrf_data['query']['tokens']['csrftoken']
            print(f"Got CSRF token: {csrf_token}")
            
            # Step 4: Add the claim
            claim_data = {
                'action': 'wbcreateclaim',
                'entity': lexeme_id,
                'snaktype': 'value',
                'property': suru_property,
                'value': json.dumps(suru_value),
                'token': csrf_token,
                'format': 'json'
            }
            
            print(f"Adding claim with data: {claim_data}")
            
            claim_response = session.post(api_url, data=claim_data)
            if claim_response.status_code == 200:
                result = claim_response.json()
                if 'success' in result:
                    print(f"Successfully added Suru_ID (P12682) claim with value '{suru_value}' to lexeme {lexeme_id}")
                else:
                    print(f"Failed to add claim. Response: {result}")
            else:
                print(f"Failed to add claim. Status: {claim_response.status_code}, Response: {claim_response.text}")
        else:
            print(f"Failed to get CSRF token. Status: {csrf_response.status_code}, Response: {csrf_response.text}")
    

    # Add sense to lexeme
    if len(L2.senses) == 0 and sv_gloss is not None and betydelse_objekt is not None:
        L2.createSense(
            {"sv": sv_gloss},
            claims={"P5137": [betydelse_objekt]},
        )
        print(f"Added sense for {lang}:{lemma}, {category}, URL: https://www.wikidata.org/wiki/Lexeme:{lexeme_id}")
    else:
        print(f"Did not add sense for {lang}:{lemma}, {category}, URL: https://www.wikidata.org/wiki/Lexeme:{lexeme_id}")
    
    # Return the lexeme ID and URL
    return {
        'lexeme_id': lexeme_id,
        'lexeme_url': f"https://www.wikidata.org/wiki/Lexeme:{lexeme_id}"
    }

# Exempel
# exempel add("fi", "haaste", "noun", "SURU_7107788c441b76dfdb12e2eb7ab5a1a2", "utmaning", "Q16511806")


