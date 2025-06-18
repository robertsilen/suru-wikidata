from flask import Flask, request, jsonify
import importlib.util
import sys

# Import the module with a number prefix
spec = importlib.util.spec_from_file_location("create_lex", "07_create_lex.py")
create_lex = importlib.util.module_from_spec(spec)
sys.modules["create_lex"] = create_lex
spec.loader.exec_module(create_lex)

app = Flask(__name__)

@app.route('/add', methods=['GET'])
def add_lexeme():
    """
    Add a lexeme with parameters from URL query string.
    
    Parameters:
    - lang: language code (e.g., 'fi')
    - lemma: the word/lemma
    - category: part of speech (e.g., 'noun', 'adjective')
    - suru_id: Suru ID (optional)
    - sv_gloss: Swedish gloss (optional)
    - betydelse_objekt: meaning object (optional)
    
    Example URL:
    http://localhost:5000/add?lang=fi&lemma=haaste&category=noun&suru_id=SURU_7107788c441b76dfdb12e2eb7ab5a1a2&sv_gloss=utmaning&betydelse_objekt=Q16511806
    """
    try:
        # Get parameters from URL query string
        lang = request.args.get('lang')
        lemma = request.args.get('lemma')
        category = request.args.get('category')
        suru_id = request.args.get('suru_id')
        sv_gloss = request.args.get('sv_gloss')
        betydelse_objekt = request.args.get('betydelse_objekt')
        
        # Validate required parameters
        if not lang or not lemma or not category:
            return jsonify({
                'error': 'Missing required parameters. Required: lang, lemma, category. Optional: suru_id, sv_gloss, betydelse_objekt'
            }), 400
        
        # Call the add function
        result = create_lex.add(lang, lemma, category, suru_id, sv_gloss, betydelse_objekt)
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed lexeme: {lang}:{lemma} ({category})',
            'lexeme_id': result['lexeme_id'],
            'lexeme_url': result['lexeme_url'],
            'parameters': {
                'lang': lang,
                'lemma': lemma,
                'category': category,
                'suru_id': suru_id,
                'sv_gloss': sv_gloss,
                'betydelse_objekt': betydelse_objekt
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'An error occurred while processing the request'
        }), 500

@app.route('/', methods=['GET'])
def home():
    """
    Home page with usage instructions
    """
    return jsonify({
        'message': 'Suru Wikidata Lexeme Creator API',
        'usage': {
            'endpoint': '/add',
            'method': 'GET',
            'required_parameters': ['lang', 'lemma', 'category'],
            'optional_parameters': ['suru_id', 'sv_gloss', 'betydelse_objekt'],
            'example': 'http://localhost:5001/add?lang=fi&lemma=haaste&category=noun&suru_id=SURU_7107788c441b76dfdb12e2eb7ab5a1a2&sv_gloss=utmaning&betydelse_objekt=Q16511806'
        }
    })

if __name__ == '__main__':
    print("Starting Suru Wikidata Lexeme Creator Flask server...")
    print("Server will be available at: http://localhost:5001")
    print("Use /add endpoint with GET parameters to create lexemes")
    print("Example: http://localhost:5001/add?lang=fi&lemma=haaste&category=noun")
    app.run(debug=True, host='0.0.0.0', port=5001) 