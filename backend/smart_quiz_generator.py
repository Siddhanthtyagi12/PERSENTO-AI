import os
import json
import re
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from google import genai
from dotenv import load_dotenv
from functools import wraps

# Robust .env loading
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

quiz_bp = Blueprint('quiz', __name__)

# Configure Gemini with the new library
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def get_gemini_client():
    if not os.getenv("GEMINI_API_KEY"):
        return None
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'org_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@quiz_bp.route('/quiz')
@login_required
def quiz_page():
    return render_template('quiz_generator.html', active_page='quiz')

@quiz_bp.route('/api/generate_quiz', methods=['POST'])
@login_required
def generate_quiz():
    data = request.json
    notes = data.get('notes')
    
    if not notes:
        return jsonify({"error": "No notes provided"}), 400
        
    client = get_gemini_client()
    if not client:
        return jsonify({"error": "Gemini API Key missing in .env"}), 500
        
    try:
        # Try multiple models seen in the user's available models list (using full names)
        models_to_try = ['models/gemini-2.0-flash', 'models/gemini-flash-latest', 'models/gemini-pro-latest', 'models/gemini-1.5-flash']
        content = None
        error_msg = ""
        
        for model_name in models_to_try:
            try:
                print(f"[DEBUG] Trying Gemini model (New Lib): {model_name}")
                response = client.models.generate_content(
                    model=model_name,
                    contents=f"Generate 5 MCQs from these notes: {notes}. Format as RAW JSON list of objects with 'question', 'options' (4), and 'answer'. No markdown."
                )
                content = response.text
                if content:
                    print(f"[DEBUG] Success with {model_name}")
                    break
            except Exception as model_err:
                print(f"[DEBUG] Model {model_name} failed:")
                print(f"Error Type: {type(model_err)}")
                print(f"Error Message: {str(model_err)}")
                error_msg += f"{model_name}: {str(model_err)}\n"
                continue
        
        if not content:
            msg = "All AI models failed. "
            if "NOT_FOUND" in error_msg:
                msg += "This API key might not have access to these models. Please check Google AI Studio."
            elif "PERMISSION_DENIED" in error_msg:
                msg += "Permission denied. Check if the API key is valid and Generative AI API is enabled."
            else:
                msg += f"Error: {error_msg[:100]}"
            return jsonify({"error": msg}), 500
        
        # Find JSON block
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            questions = json.loads(json_match.group())
            return jsonify({"status": "success", "questions": questions})
        else:
            try:
                questions = json.loads(content)
                return jsonify({"status": "success", "questions": questions})
            except:
                return jsonify({"error": "Failed to parse questions as JSON"}), 500
            
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return jsonify({"error": str(e)}), 500
