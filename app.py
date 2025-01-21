from flask import Flask, render_template, redirect, url_for, request, jsonify
import math
from functools import wraps
from models.conn import db
from models.models import APIKey
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')

db.init_app(app)

# Database initialization
with app.app_context():
    db.create_all()

def get_api_keys():
    return [key.api_key for key in APIKey.query.all()]

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')  # Read key from header
        if api_key not in get_api_keys():
            return jsonify({"error": "Unauthorized, invalid API key"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Rotta per la home page
@app.route('/')
def home():
    return render_template('index.html')

# route to add api key
@app.route('/add-api-key', methods=['POST'])
def add_api_key():
    data = request.get_json()
    if not data or 'user' not in data or 'api_key' not in data:
        return jsonify({"error": "Please provide both user and api_key."}), 400

    user = data['user']
    api_key = data['api_key']

    try:
        new_key = APIKey(user=user, api_key=api_key)
        db.session.add(new_key)
        db.session.commit()
        return jsonify({"message": "API key added successfully."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# calcolo scala
@app.route('/calculate-stairs', methods=['POST'])
@require_api_key
def calculate_stairs():
    data = request.get_json()
    if not data or 'height' not in data or 'depth' not in data:
        return jsonify({"error": "Please provide both height and depth in the request."}), 400

    try:
        # valori obbligatori (cm)
        altezzaTotale = float(data['height'])
        larghezzaTotale = float(data['depth'])
        
        # valori facoltativi (cm)
        piastrella = float(data.get('margin', 0))
        minAltezza = float(data.get('minStepHeight', 10))
        maxAltezza = float(data.get('maxStepHeight', 20))
        minProfondita = float(data.get('minStepDepth', 25))
        maxProfondita = float(data.get('maxStepDepth', 35))
    except ValueError:
        return jsonify({"error": "Height, depth, margin, and limit values must be valid numbers."}), 400
    
    # Verifica che maxAltezza sia maggiore di minAltezza
    if maxAltezza <= minAltezza:
        return jsonify({"error": "Maximum step height must be greater than minimum step height."}), 400

    # Verifica che maxLarghezza sia maggiore di minLarghezza
    if maxProfondita <= minProfondita:
        return jsonify({"error": "Maximum step width must be greater than minimum step width."}), 400
    
    
    
    prefAltezza = (minAltezza + maxAltezza) / 2 # altezza preferita
    prefProfondita = (minProfondita + maxProfondita) / 2 # larghezza preferita
    
    # Calcolo del numero di gradini per altezza e larghezza
    numGradini = math.ceil(altezzaTotale / (prefAltezza + piastrella))
    numGradini2 = math.ceil(larghezzaTotale / prefProfondita)
    
    # calocla altezza di ogni gradino
    altezzaGradino = altezzaTotale / numGradini
    profonditaGradino = larghezzaTotale / numGradini2
    
    # Controllo se le dimensioni sono valide
    if altezzaGradino < minAltezza or altezzaGradino > maxAltezza:
        return jsonify({"error": "Calculated step height is out of acceptable range."}), 400

    if profonditaGradino < minProfondita or profonditaGradino > maxProfondita:
        return jsonify({"error": "Calculated step depth is out of acceptable range."}), 400
    
    # Calcolare l'errore rispetto ai valori preferiti
    erroreAltezza = abs(altezzaGradino - prefAltezza)
    erroreProfondita = abs(profonditaGradino - prefProfondita)
    
    # Decidere quale parametro dare priorità in base alla 
    if erroreAltezza <= erroreProfondita:
        altezzaGradino = altezzaTotale / numGradini
        profonditaGradino = larghezzaTotale / numGradini
    else:
        altezzaGradino = altezzaTotale / numGradini2
        profonditaGradino = larghezzaTotale / numGradini2
    
    # rimuovi la piastrella
    altezzaGradino -= piastrella
    
    # Restituisci i risultati
    return jsonify({
        "stepNum": numGradini,
        "stepHeight": altezzaGradino,
        "stepDepth": profonditaGradino
    })

if __name__ == '__main__':
    app.run(debug=True)