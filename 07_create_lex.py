import logging
import pandas as pd
import json
import uuid

import LexData
from LexData.language import en
from LexData.claim import Claim
fi = LexData.Language("fi", "Q1412")
import requests

logging.basicConfig(level=logging.INFO)
repo = LexData.WikidataSession("Robertsilen", "klem_PHIB.wruh0gang")
categories = {
    "noun": "Q1084",
    "adjective": "Q34698",
}

def add(lang, lemma, category, suru_id, sv_gloss, betydelse_objekt):
    category_id = categories.get(category, None)
    if category_id is None:
        raise ValueError(f"Unknown category for {lang} {lemma}: {category}")

    L2 = LexData.get_or_create_lexeme(repo, lemma, fi, category_id)
    lexeme_id = L2['id']
    print(f"Created lexeme for {lang}:{lemma}, {category}, URL: https://www.wikidata.org/wiki/Lexeme:{lexeme_id}")

    # Add P12682 claim to the lexeme with suru_id
    if suru_id is not None:
        suru_property = "P12682"
        suru_value = suru_id.replace("SURU_", "")    
        
        # Use Wikidata API directly
        api_url = "https://www.wikidata.org/w/api.php"
        username = "Robertsilen"
        # NOTE: For security, use a secure method to store your token in production
        token = "$2y$10$4Xu5WC7e0Yg4GiIdPoluQezWX3ZUlOtA.V.ZHnwGj122ELV9XU/Ay"
        
        # First, get an edit token
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'SuruWikidataBot/1.0 (https://github.com/your-repo; your-email@example.com)'
        })
        
        # Get CSRF token
        token_params = {
            'action': 'query',
            'meta': 'tokens',
            'type': 'csrf',
            'format': 'json'
        }
        
        token_response = session.get(api_url, params=token_params)
        if token_response.status_code == 200:
            token_data = token_response.json()
            csrf_token = token_data['query']['tokens']['csrftoken']
            print(f"Got CSRF token: {csrf_token}")
            
            # Add the claim
            claim_data = {
                'action': 'wbcreateclaim',
                'entity': lexeme_id,
                'snaktype': 'value',
                'property': suru_property,
                'value': json.dumps(suru_value),
                'token': csrf_token,
                'format': 'json'
            }
            
            print(f"Wikidata API URL: {api_url}")
            print(f"Claim data: {claim_data}")
            
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
            print(f"Failed to get CSRF token. Status: {token_response.status_code}, Response: {token_response.text}")
    
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


