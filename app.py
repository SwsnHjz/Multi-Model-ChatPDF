print("[DEBUG] app.py execution has started.", flush=True)
import os
import openai
import fitz  
import docx
import math
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash,session
from flask_cors import CORS
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
import json
import hashlib
import asyncio
import httpx 
import glob
from functools import wraps
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth


# Import model-specific answer functions
from models import (
    get_answer_from_gpt4,
    get_answer_from_mistral,
    get_answer_from_gemini,
    get_answer_from_deepseek
)

print("[DEBUG] All modules imported successfully.", flush=True)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

app = Flask(__name__, template_folder='templates', static_folder='static')

# File size llimit
CORS(app)

#app configs
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
# Set up the SQLite database file
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
# Add Mail Configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com') 
app.config['MAIL_PORT'] = 465          
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True  

app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')

app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

mail = Mail(app)
oauth = OAuth(app)

oauth.register(
    name='google',
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# LoginManager where to redirect users if they try to access a protected page
login_manager.login_view = 'homepage' 
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info' 

#User model for database 
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False) 
    password = db.Column(db.String(60), nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False) 

# This function is required by Flask-Login to load a user from the session
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# handles the error of limit size 
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify(error="File is too large. The limit is 20MB."), 413
    
    
ASSISTANT_KNOWLEDGE_BASE = {
    "chunks": [],
    "embeddings": []
}


SESSIONS_DIR = 'sessions'
USAGE_FILE = 'user_usage.json'
user_usage_store = {}
MESSAGE_LIMIT = 20

if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# Dictionaries for translations and greetings 
backend_translations = {
    'en': {
        'greeting': "Hello! How can I help you with the contents of this document?",
        'not_found': "I couldn't find an answer for that in the document. Is there anything else about its content I can help with?"
    },
    'ar': {
        'greeting': "مرحباً! كيف يمكنني مساعدتك بمحتويات هذا المستند؟",
        'not_found': "لم أتمكن من العثور على إجابة لذلك في المستند. هل هناك أي شيء آخر حول محتواه يمكنني المساعدة به؟"
    }
}
greeting_keywords = {
    'en': ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"],
    'ar': ["مرحبا", "أهلا", "السلام عليكم", "أهلا بك"]
}

# when embedding large PDF documents
async def get_embeddings_async(chunks, client):
    timeout = httpx.Timeout(30.0, connect=60.0)
    
    semaphore = asyncio.Semaphore(5) 
    
    async with httpx.AsyncClient(timeout=timeout) as async_client:
        tasks = []
        for chunk in chunks:
            task = asyncio.ensure_future(
                process_chunk(chunk, client, async_client, semaphore)
            )
            tasks.append(task)
        embeddings = await asyncio.gather(*tasks)
        return [emb for emb in embeddings if emb is not None]


async def process_chunk(chunk, client, async_client, semaphore):
    async with semaphore:
        try:
            response = await async_client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {client.api_key}"},
                json={"input": chunk, "model": "text-embedding-3-small"}
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        except Exception as e:
            print(f"Failed to process a chunk: {e}")
            return None
            
            
def get_embedding(text):
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding   
    
# Extracting the text
def extract_text_from_pdf(file_path):
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    return text

def chunk_text(text, chunk_size=1024, overlap=128):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def find_top_k_similar_chunks(query_vec, doc_vecs, k=5):
    similarities = cosine_similarity([query_vec], doc_vecs)[0]
    top_k_indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)[:k]
    return top_k_indices
    
# Processing the PDF
def estimate_tokens(text):
    return int(len(text) / 4)
    
def process_pdf(file_path, filename, user_id):
    print(f"[UPLOAD] Storing text from '{filename}' for user: {user_id}")
    text = extract_text_from_pdf(file_path)
    
    chunks = chunk_text(text)
    embeddings = asyncio.run(get_embeddings_async(chunks, client))

    data_to_store = {
        "chunks": chunks,
        "embeddings": embeddings
    }

    session_filename = f"{user_id}_{filename}.json"
    session_filepath = os.path.join(SESSIONS_DIR, session_filename)
    with open(session_filepath, 'w') as f:
        json.dump(data_to_store, f)
    print(f"Processing and embedding complete for '{filename}'.")
    
# Assistant- a mini chatbot
# containing site documentation, chunks it, embeds it, and stores it in memory for the chatbot
def load_assistant_knowledge():
    """Loads and processes the assistant's documentation file on startup."""
    print("[ASSISTANT] Loading knowledge base...")
    doc_path = 'documentation.docx' 
    
    if not os.path.exists(doc_path):
        print(f"[ASSISTANT] CRITICAL: Knowledge base file not found at '{doc_path}'")
        ASSISTANT_KNOWLEDGE_BASE['chunks'] = ["The documentation file is missing."]
        return

    try:
        # Read text from .docx file
        doc = docx.Document(doc_path)
        full_text = "\n".join([para.text for para in doc.paragraphs])
        
        # Chunk the text
        chunks = chunk_text(full_text)
        ASSISTANT_KNOWLEDGE_BASE['chunks'] = chunks
        
        # Get embeddings for chunks
        embeddings = asyncio.run(get_embeddings_async(chunks, client))
        ASSISTANT_KNOWLEDGE_BASE['embeddings'] = embeddings
        print(f"[ASSISTANT] Knowledge base loaded successfully. {len(chunks)} chunks processed.")
        
    except Exception as e:
        print(f"[ASSISTANT] FAILED to load knowledge base: {e}")
        ASSISTANT_KNOWLEDGE_BASE['chunks'] = [f"Error loading documentation: {e}"]


load_assistant_knowledge()


# get summary and suggest questions in both languages
# with the properly localized prompt for better summarization accuracy

def get_summary_and_questions(text, model_choice='gpt-4'):
    # detect the language of the document text 
    contains_arabic_chars = any('\u0600' <= char <= '\u06FF' for char in text[:1000])

    #build the correct prompt in the correct language
    
    if contains_arabic_chars:
        # these are the instructions in ARABIC
        prompt = f"""حلل النص التالي من مستند. مهمتك هي:
1.  قدم ملخصًا احترافيًا وموجزًا للغرض الرئيسي من المستند في جملة إلى جملتين.
2.  اقترح ثلاثة أسئلة مثيرة للاهتمام وذات صلة قد يرغب المستخدم في طرحها حول المحتوى.
3.  يجب أن تكون إجابتك بتنسيق JSON صالح يحتوي على مفتاحين: "summary" و "suggested_questions" (والذي يجب أن يكون مصفوفة من السلاسل النصية).

إليك مقتطف من النص:
---
{text[:4000]} 
---
إجابة JSON:"""
    else:
        # these are the instructions in ENGLISH
        prompt = f"""Analyze the following text from a document. Your task is to:
1.  Provide a concise, professional summary of the document's main purpose in 1-2 sentences.
2.  Suggest exactly three interesting and relevant questions a user might want to ask about the content.
3.  You MUST format your response as a valid JSON object with two keys: "summary" and "suggested_questions" (which should be an array of strings).

Here is a snippet of the text:
---
{text[:4000]} 
---
JSON Response:"""

    # call the AI model 
    answer_from_ai = get_answer_from_gpt4(prompt)

    
    try:
        start_index = answer_from_ai.find('{')
        end_index = answer_from_ai.rfind('}') + 1
        
        if start_index != -1 and end_index != -1:
            clean_json_string = answer_from_ai[start_index:end_index]
            data = json.loads(clean_json_string)
            return data
        else:
            raise json.JSONDecodeError("No JSON object found in response", answer_from_ai, 0)

    except (json.JSONDecodeError, TypeError) as e:
        
        print(f"CRITICAL: Failed to decode or find JSON. Error: {e}")
        print(f"Original AI Response was: {answer_from_ai}")
        
        if contains_arabic_chars:
            summary = "تمت معالجة المستند وهو جاهز لأسئلتك."
        else:
            summary = "The document has been processed and is ready for your questions."
        return {
            "summary": summary,
            "suggested_questions": []
        }
#Generate answers for the questions the user asks  
# Converts user queries to embeddings, retrieves top-K similar document chunks
# and injects them as context into the selected LLM provider

def generate_answer(question, filename, model_choice, user_id, lang='en', k=5):
    
    contains_arabic_chars = any('\u0600' <= char <= '\u06FF' for char in question)
    response_lang_code = 'ar' if contains_arabic_chars else 'en'
    response_messages = backend_translations.get(response_lang_code)

    # this is to handle greetings
    if question.lower().strip() in greeting_keywords.get(response_lang_code, []):
        return response_messages['greeting']

    # retrieve data from the correct user's session file
    session_filename = f"{user_id}_{filename}.json"
    session_filepath = os.path.join(SESSIONS_DIR, session_filename)
    if not os.path.exists(session_filepath):
        print(f"[ERROR] Session file not found for user {user_id}: {session_filename}")
        return "Error: No file has been processed. Please upload a document."

    with open(session_filepath, 'r') as f:
         session_data = json.load(f)
    
    chunks = session_data.get("chunks", [])
    
    embeddings = session_data.get("embeddings", [])
    
    if not chunks or not embeddings:
        return "Error: The document data seems to be corrupted or empty."


    query_embedding = get_embedding(question)
    top_k_indices = find_top_k_similar_chunks(query_embedding, embeddings, k)
    context = "\n\n".join([chunks[i] for i in top_k_indices])

    prompt = f"""Use only the context below to answer the question in no more than 3 sentences. If unsure, say "{response_messages['not_found']}"
Question: {question}
Context: {context}
Answer:"""
    input_tokens = estimate_tokens(prompt)
    print(f"[CHAT] Estimated input tokens for model '{model_choice}': {input_tokens}")

    # calling the selected model
    if model_choice == 'gpt-4':
        return get_answer_from_gpt4(prompt)
    elif model_choice == 'mistral':
        return get_answer_from_mistral(prompt)
    elif model_choice == 'gemini':
        return get_answer_from_gemini(prompt)
    elif model_choice == 'deepseek':
        return get_answer_from_deepseek(prompt)
    else:
        return "Error: Invalid model selected."
    
    output_tokens = estimate_tokens(answer)
    print(f"[CHAT] Estimated output tokens: {output_tokens}")
    print(f"[CHAT] Total estimated tokens used: {input_tokens + output_tokens}")

    return answer

#Allows users to test the platform as guests,
# then securely transfers their uploaded documents and chat context to a permanent account upon signup

def transfer_guest_session_if_exists(new_user_id):
    """Checks for a pending guest session and renames the file to the new user's ID."""
    if 'pending_guest_session' in session:
        guest_info = session.pop('pending_guest_session') 
        guest_id = guest_info['guest_id']
        filename = guest_info['filename']
        model_name = guest_info['model_name'] 

        guest_filepath = os.path.join(SESSIONS_DIR, f"{guest_id}_{filename}.json")
        user_filepath = os.path.join(SESSIONS_DIR, f"{new_user_id}_{filename}.json")

        if os.path.exists(guest_filepath):
            try:
                # If the user already has a file with this name, remove it
                if os.path.exists(user_filepath):
                    os.remove(user_filepath)
                
                os.rename(guest_filepath, user_filepath)
                print(f"[SESSION_TRANSFER] Transferred '{filename}' from guest {guest_id} to user {new_user_id}")
                
                # Store info needed for a smart redirect back to the chat page
                session['redirect_after_login'] = {
                    "endpoint": "chat_page",
                    "model_name": model_name,
                    "filename": filename
                }
            except OSError as e:
                print(f"[ERROR] Could not rename session file during transfer: {e}")
                
def clean_up_guest_session():
    """Removes guest-specific variables from the session after login."""
    session.pop('is_guest', None)
    session.pop('guest_message_count', None)
    print("[SESSION_CLEANUP] Guest session variables cleared.")           
#generate confirmation token for email
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm-salt')

def confirm_token(token, expiration=3600): # 1 hour expiration
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='email-confirm-salt',
            max_age=expiration
        )
    except:
        return False
    return email



def load_usage():
    """Loads the user usage data from the JSON file into memory."""
    global user_usage_store
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, 'r') as f:
            try:
                user_usage_store = json.load(f)
            except json.JSONDecodeError:
                user_usage_store = {}
    else:
        user_usage_store = {}

def save_usage():
    """Saves the current user usage data from memory to the JSON file."""
    with open(USAGE_FILE, 'w') as f:
        json.dump(user_usage_store, f)


if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)
if not os.path.exists('uploads'):
    os.makedirs('uploads')

load_usage()    
# Flask Routes 
@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/check-email')
def check_email():
    # Get the email from the query parameter to display it
    email = request.args.get('email')
    return render_template('check_email.html', email=email)
    
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    # Get email from form
    email = request.form.get('email') 
    password = request.form.get('password')

    # Check for existing user or email
    if User.query.filter_by(username=username).first() is not None:
        flash('username_exists', 'danger')
        return redirect(url_for('homepage'))
    if User.query.filter_by(email=email).first() is not None:
        flash('email_exists', 'danger') 
        return redirect(url_for('homepage'))

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password=hashed_password, confirmed=False)
    db.session.add(new_user)
    db.session.commit()

    # --- Send Confirmation Email ---
    token = generate_confirmation_token(new_user.email)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = render_template('email/activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email for the platform"
    msg = Message(subject, recipients=[new_user.email], html=html, sender=app.config['MAIL_USERNAME'])
    mail.send(msg)
    
    flash('registration_success_check_email', 'success') 
    return redirect(url_for('check_email', email=new_user.email))

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('confirmation_link_invalid', 'danger')
        return redirect(url_for('homepage'))

    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash('account_already_confirmed', 'info')
    else:
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        flash('account_confirmed_success', 'success')
    login_user(user)
    clean_up_guest_session()
    transfer_guest_session_if_exists(user.id)
    
    if 'redirect_after_login' in session:
        redirect_info = session.pop('redirect_after_login')
        return redirect(url_for(
            redirect_info['endpoint'], 
            model_name=redirect_info['model_name'],
            filename=redirect_info['filename']  
    ))
        
    return redirect(url_for('homepage'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    
    if user and bcrypt.check_password_hash(user.password, password):
        if user.confirmed:
            login_user(user)
            clean_up_guest_session()
            transfer_guest_session_if_exists(user.id)
            if 'redirect_after_login' in session:
                redirect_info = session.pop('redirect_after_login')
                return redirect(url_for(
                    redirect_info['endpoint'], 
                    model_name=redirect_info['model_name'],
                    filename=redirect_info['filename'] 
                    ))
            
            return redirect(url_for('homepage'))
        else:
            flash('account_not_confirmed_check_email', 'info')
            return redirect(url_for('homepage'))
    else:
        flash('login_error', 'danger')
        return redirect(url_for('homepage'))

@app.route('/logout')
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('homepage'))

def is_user_or_guest():
    return current_user.is_authenticated or session.get('is_guest', False)

@app.route('/login/google')
def google_login():
    """Redirects to Google's authentication page."""
    redirect_uri = url_for('google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/login/google/callback')
def google_callback():
    """Handles the response from Google after authentication."""
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    
    # Check if this user already exists in our database
    user = User.query.filter_by(email=user_info['email']).first()

    if not user:
        # If user doesn't exist, create a new one
        new_user = User(
            email=user_info['email'],
            # Create a username from the email, or use their name if available
            username=user_info.get('name', user_info['email'].split('@')[0]),
            # Create a random, unusable password for Google users
            password=bcrypt.generate_password_hash(os.urandom(16)).decode('utf-8'),
            # Mark them as confirmed instantly
            confirmed=True 
        )
        db.session.add(new_user)
        db.session.commit()
        user = new_user

    # Log the user in
    login_user(user)
    clean_up_guest_session()
    transfer_guest_session_if_exists(user.id)
    if 'redirect_after_login' in session:
        redirect_info = session.pop('redirect_after_login')
        return redirect(url_for(
        redirect_info['endpoint'], 
        model_name=redirect_info['model_name'],
        filename=redirect_info['filename']  
    ))
    return redirect(url_for('homepage'))

@app.route('/chat/<model_name>')
def chat_page(model_name):
    is_guest = session.get('is_guest', False)
    
    if not (current_user.is_authenticated or is_guest):
        flash('login_or_guest_required', 'info')
        return redirect(url_for('homepage'))
        
    valid_models = ['gpt-4', 'mistral', 'gemini', 'deepseek']
    if model_name not in valid_models:
        return "Model not found", 404
        
    active_filename = request.args.get('filename', None)    
    
    return render_template('chat.html', model_name=model_name, is_guest=is_guest,active_filename=active_filename)

def user_or_guest_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_user_or_guest():
            return jsonify(error="Authentication required"), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route('/upload', methods=['POST'])
@user_or_guest_required 
def upload_file():
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        real_ip = request.remote_addr
        salted_ip = real_ip + os.getenv("SECRET_SALT", "default_salt_123")
        user_id = hashlib.sha256(salted_ip.encode('utf-8')).hexdigest()
    
    if 'pdf' not in request.files:
        return jsonify({"error": "No PDF file part in the request"}), 400
    file = request.files['pdf']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if file and file.filename.endswith('.pdf'):
        filename = file.filename
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        try:
            process_pdf(filepath, filename, user_id)
            return jsonify({"message": f"Successfully processed '{filename}'", "filename": filename})
        except Exception as e:
            print(f"ERROR during PDF processing: {e}")
            return jsonify({"error": "An error occurred while processing your PDF."}), 500
    return jsonify({"error": "Invalid file type. Please upload a PDF."}), 400


#Tracks guest users securely via IP hashing 
# and limits them to 2 interactions to encourage account registration, preventing API abuse

@app.route('/chat', methods=['POST'])
@user_or_guest_required 
def chat():
    
    # determine the user_id and handle guest logic
    if current_user.is_authenticated:
        user_id = current_user.id
    else: 
        real_ip = request.remote_addr
        salted_ip = real_ip + "a_secret_salt_string_123" 
        user_id = hashlib.sha256(salted_ip.encode('utf-8')).hexdigest()
        
        # Increment and check the message limit for guests
        session['guest_message_count'] = session.get('guest_message_count', 0) + 1
        if session.get('guest_message_count', 0) > 2:
            data = request.json
            session['pending_guest_session'] = {
                'guest_id': user_id,
                'filename': data.get('filename'),
                'model_name': data.get('model')
            }
            return jsonify({
                "error": "You have reached the 2-message limit for guests. Please log in or register to continue.",
                "action": "login_required" 
            }), 429


    
    data = request.json
    question = data.get('question')
    filename = data.get('filename')
    model_choice = data.get('model')
    lang = data.get('lang', 'en') 
    
    if not all([question, filename, model_choice]):
        return jsonify({"error": "Missing data"}), 400

    
    answer = generate_answer(question, filename, model_choice, user_id, lang)
    return jsonify({"answer": answer})

@app.route('/summarize', methods=['POST'])
@user_or_guest_required
def summarize():
    # for guests or logged-in users
    if current_user.is_authenticated:
        user_id = current_user.id
    else: # Guest user
        real_ip = request.remote_addr
        salted_ip = real_ip + "a_secret_salt_string_123" 
        user_id = hashlib.sha256(salted_ip.encode('utf-8')).hexdigest()

    
    data = request.json
    filename = data.get('filename')
    
    
    if not filename:
        return jsonify({"error": "Filename not provided in the request."}), 400

    session_filename = f"{user_id}_{filename}.json"
    session_filepath = os.path.join(SESSIONS_DIR, session_filename)
    
    
    if not os.path.exists(session_filepath):
        print(f"[ERROR] Session file not found at {session_filepath}")
        return jsonify({"error": "Session file could not be found."}), 404
        
    with open(session_filepath, 'r') as f:
        session_data = json.load(f)
    
    chunks = session_data.get("chunks", [])

    
    if not chunks:
        return jsonify({"error": "Document appears to be empty."}), 400

    
    text = " ".join(chunks)
    
    
    summary_data = get_summary_and_questions(text)
    
    return jsonify(summary_data)

#Uses RAG on the site's own documentation 
# to act as a localized customer support bot, answering in both English and Arabic

@app.route('/ask-assistant', methods=['POST'])
@user_or_guest_required
def ask_assistant():
    """Handles questions for the site's help assistant."""
    data = request.json
    question = data.get('question')
    lang = data.get('lang', 'en') #Receive the language from the request

    if not question:
        return jsonify({"error": "No question provided"}), 400

    if not ASSISTANT_KNOWLEDGE_BASE.get('embeddings'):
        return jsonify({"answer": "I'm sorry, my knowledge base is currently unavailable. Please contact support."})

    # Find relevant context from the pre-loaded knowledge base
    query_embedding = get_embedding(question)
    top_k_indices = find_top_k_similar_chunks(
        query_embedding, 
        ASSISTANT_KNOWLEDGE_BASE['embeddings'], 
        k=3
    )
    context = "\n\n".join([ASSISTANT_KNOWLEDGE_BASE['chunks'][i] for i in top_k_indices])

    
    if lang == 'ar':
        # Arabic instructions for the AI
        prompt_instruction = f"""أنت مساعد لموقع اسمه 'AI Chat PDF'. وظيفتك الوحيدة هي الإجابة على الأسئلة حول كيفية استخدام الموقع بناءً على السياق المقدم فقط. كن موجزًا وودودًا.
إذا كان السياق لا يحتوي على الإجابة، يجب أن تقول "أنا لست متأكدًا بشأن ذلك، ولكن يمكنك التواصل مع فريقنا لطرح أسئلة أكثر تحديدًا." ثم في سطر جديد، قدم البريد الإلكتروني "sawsannhijazee@gmail.com". لا تقل أي شيء آخر."""
    else:
        # English instructions for the AI
        prompt_instruction = f"""You are a helpful assistant for a website called 'AI Chat PDF'. Your only job is to answer questions about how to use the site based on the context provided. Be concise and friendly.
If the context doesn't contain the answer, you MUST say "I'm not sure about that, but you can contact our team for more specific questions." and then on a new line, provide the email "sawsannhijazee@gmail.com". Do not say anything else."""

    # Combine instructions, context, and the user's question
    prompt = f"""{prompt_instruction}

Context:
---
{context}
---
User Question: {question}

Answer:"""

    answer = get_answer_from_gpt4(prompt) 
    return jsonify({"answer": answer})


@app.route('/guest-login')
def guest_login():
    """Sets a session variable to mark the user as a guest and returns to homepage."""
    session['is_guest'] = True
    flash('guest_mode_activated', 'success') 
    return redirect(url_for('homepage'))



        
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    
    app.run(host='0.0.0.0', port=5000, debug=True)