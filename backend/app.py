from flask import Flask, request, jsonify
from flask_cors import CORS
from sales_processor import SalesDataProcessor, SalesChatbot, load_data_from_file
import os
import io
import pandas as pd
from werkzeug.utils import secure_filename
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# CORS: Allow local development and all Netlify deployments
# Note: Replace 'ivalue-chatbot.netlify.app' with your actual Netlify domain
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000",
            "https://ivalue-chatbot.netlify.app"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": False
    }
})

# Google Gemini API Key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if GOOGLE_API_KEY:
    print("Google API key loaded from environment.")
else:
    print("WARNING: GOOGLE_API_KEY not found! Using fallback (remove in production).")
    GOOGLE_API_KEY = 'AIzaSyCrZbuuVJ652PeAZgdGt_Ow7Rh_xK0mXCs'
    os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY

# Global state
current_chatbot = None
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# === AUTO-LOAD DEFAULT FILE ===
DEFAULT_FILE_PATH = os.path.join('uploads', 'sales_data.xlsx')

print("\n" + "="*60)
print("Starting iValue Sales Chatbot Backend...")
print("="*60)

if os.path.exists(DEFAULT_FILE_PATH):
    print(f"Found default file → Auto-loading: {DEFAULT_FILE_PATH}")
    try:
        df = load_data_from_file(DEFAULT_FILE_PATH)
        if df is not None and len(df) > 0:
            processor = SalesDataProcessor(df)
            current_chatbot = SalesChatbot(processor)
            print("DEFAULT DATA LOADED SUCCESSFULLY!")
            print(f"   • Rows: {len(df):,}")
            print(f"   • Columns: {len(df.columns)}")
            print("   • You can now ask questions immediately — no upload needed!")
        else:
            print("File loaded but empty or invalid.")
    except Exception as e:
        print(f"Error loading default file: {e}")
else:
    print("Default file NOT found:")
    print(f"   {DEFAULT_FILE_PATH}")
    print("   → Manual upload required via frontend.")
print("="*60 + "\n")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# === SUPER FAST UPLOAD: Stream directly to pandas (no disk write!) ===
@app.route('/upload', methods=['POST'])
def upload_file():
    global current_chatbot
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if not file.filename:
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        try:
            file_bytes = file.read()
            file_stream = io.BytesIO(file_bytes)
            
            print(f"Processing uploaded file in memory: {filename} ({len(file_bytes)/1e6:.1f} MB)")
            
            df = pd.read_excel(file_stream, engine='openpyxl')
            
            if df is not None and len(df) > 0:
                processor = SalesDataProcessor(df)
                current_chatbot = SalesChatbot(processor)
                
                return jsonify({
                    'message': 'File processed instantly (in memory)!',
                    'filename': filename,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'data_loaded': True,
                    'processed_in_memory': True
                })
            else:
                return jsonify({'error': 'File is empty or invalid'}), 400
                
        except Exception as e:
            print(f"Error processing uploaded file: {e}")
            return jsonify({'error': f'Failed to process file: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type. Only .xlsx and .xls allowed'}), 400

@app.route('/query', methods=['POST'])
def handle_query():
    global current_chatbot
    if not current_chatbot:
        return jsonify({'error': 'No data loaded. Please upload a file first.'}), 400
    
    data = request.get_json()
    user_query = data.get('query', '').strip()
    if not user_query:
        return jsonify({'error': 'No query provided'}), 400
    
    response = current_chatbot.process_query(user_query)
    return jsonify({'response': response})

@app.route('/auto-query', methods=['POST'])
def handle_auto_query():
    global current_chatbot
    if not current_chatbot:
        return jsonify({'error': 'No data loaded. Please upload a file first.'}), 400
    
    data = request.get_json()
    user_query = data.get('query', '').strip()
    if not user_query:
        return jsonify({'error': 'No query provided'}), 400
    
    response = current_chatbot.process_query(user_query)
    return jsonify({
        'original_query': user_query,
        'response': response
    })

@app.route('/suggestions', methods=['GET'])
def get_suggestions():
    suggestions = {
        'basic': ["What's the total revenue?", "Show me top regions", "How many transactions do we have?"],
        'comparisons': ["Compare sales between years", "What's the revenue growth year over year?"],
        'partners': ["Show top partners by revenue", "Show regional performance for a partner"],
        'oems': ["Show top OEMs by margin", "Show regional performance for an OEM"],
        'verticals': ["Show top verticals by revenue", "Show regional performance for a vertical"],
        'customers': ["Show top customers by revenue", "Show regional performance for a customer"]
    }
    return jsonify(suggestions)

@app.route('/status', methods=['GET'])
def status():
    if current_chatbot and hasattr(current_chatbot, 'processor') and current_chatbot.processor.df is not None:
        return jsonify({
            'data_loaded': True,
            'rows': len(current_chatbot.processor.df),
            'columns': len(current_chatbot.processor.df.columns),
            'message': 'Ready for queries!'
        })
    else:
        return jsonify({
            'data_loaded': False,
            'message': 'Waiting for file upload...'
        })

# Proper port binding for Render (and local dev)
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)