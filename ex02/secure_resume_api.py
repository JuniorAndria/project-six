from flask import Flask, request, jsonify, json
import base64
import pdfplumber
import re
import chromadb
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
import binascii

app = Flask(__name__)
secret_key = '61c407a3046b0aab26fa54ed2c7b082b55ed8ab0839f1645e7bfbd958a00c3ed'

json.provider.DefaultJSONProvider.ensure_ascii = False

embedding_function = embedding_functions.DefaultEmbeddingFunction()
client = chromadb.PersistentClient(path="./chromadb")
collection = client.get_or_create_collection(name="curriculo", embedding_function=embedding_function)

limiter = Limiter(get_remote_address, app=app, default_limits=["100 per hour"])

users = [
    {'id': 1, 'username': 'admin', 'password': 'admin', 'role': 'admin'},
    {'id': 2, 'username': 'user', 'password': 'user', 'role': 'candidato'},
    {'id': 3, 'username': 'rh', 'password': 'rh', 'role': 'recrutador'},
    {'id': 4, 'username': 'user2', 'password': 'user2', 'role': 'candidato'},
    {'id': 5, 'username': 'user3', 'password': 'user3', 'role': 'candidato'},
    {'id': 6, 'username': 'rh1', 'password': 'rh1', 'role': 'recrutador'},
]

MAX_PDF_SIZE = 10 * 1024 * 1024

def search_curriculos(query, user_id, role, limit=3):
    if role == 'candidato':
        return collection.query(query_texts=[query], n_results=limit, where={"user_id": user_id})
    return collection.query(query_texts=[query], n_results=limit)

def check_if_file_exists(file_id):
    results = collection.get(where={"file_id": file_id})
    return len(results['ids']) > 0

def add_curriculo_to_collection(chunks, file_id, user_id):
    for i, chunk in enumerate(chunks):
        chunk_id = f"{file_id}_chunk_{i}"
        metadata = {"file_id": file_id, "chunk_id": i, "user_id": user_id}
        collection.add(documents=[chunk], metadatas=[metadata], ids=[chunk_id])

def process_pdf_file_to_text(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = "".join(
            clean_text(page.extract_text()) for page in pdf.pages if page.extract_text()
        )
    return text

def clean_text(text):
    page_number_pattern = r"Página\s+\d+\s+de\s+\d+\n"
    return re.sub(page_number_pattern, '', text)

def chunk_text_recursive(text, chunk_size, chunk_overlap, separators):
    text_splitter = RecursiveCharacterTextSplitter(
        separators=separators,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return text_splitter.split_text(text)

def basic_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Basic '):
            return jsonify({'error': 'Autenticação necessária.'}), 401
        token = auth_header.split(" ")[1]
        try:
            decoded_bytes = base64.b64decode(token)
            decoded_str = decoded_bytes.decode('utf-8')
            credentials = decoded_str.split(":")
            
            if len(credentials) != 2:
                return jsonify({'error': 'Formato de credenciais inválido.'}), 401

            username, password = credentials
            
            for user in users:
                if user['username'] == username and user['password'] == password:
                    kwargs['user_id'] = user['id']
                    kwargs['role'] = user['role']
                    return f(*args, **kwargs)

            return jsonify({'error': 'Credenciais inválidas.'}), 401

        except binascii.Error:
            return jsonify({'error': 'Erro ao decodificar as credenciais. Base64 inválido.'}), 401
        except UnicodeDecodeError:
            return jsonify({'error': 'Erro ao decodificar os caracteres das credenciais.'}), 401
        except ValueError:
            return jsonify({'error': 'Formato de credenciais inválido.'}), 401
    return decorated_function

@app.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    return jsonify({"error": "Limite de taxa excedido. Tente novamente mais tarde."}), 429

app.config['JSON_AS_ASCII'] = False

@app.after_request
def add_charset(response):
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response

@app.route('/search', methods=['GET'])
@basic_auth_required
@limiter.limit("10 per minute")
def search(user_id, role):
    query = request.args.get('query', '')
    limit = int(request.args.get('limit', 3))
    results = search_curriculos(query, user_id, role, limit)
    objects = [
        {
            "document": results['metadatas'][0][index]['file_id'],
            "chunk_id": results['metadatas'][0][index]['chunk_id'],
            "content": results['documents'][0][index]
        }
        for index in range(len(results['ids'][0]))
    ]
    return jsonify(objects), 200

@app.route('/upload_pdf', methods=['POST'])
@basic_auth_required
@limiter.limit("10 per minute")
def upload_pdfs(user_id, role):
    if role == "recrutador":
        return jsonify({'error': 'Apenas candidatos podem enviar currículos.'}), 403
    if not request.files:
        return jsonify({'error': 'Nenhum arquivo foi enviado.'}), 400
    file = next(request.files.values())
    if file.filename == '':
        return jsonify({'error': 'Arquivo sem nome selecionado.'}), 400
    file.seek(0, 2) 
    file_size = file.tell()  
    file.seek(0) 

    if file_size > MAX_PDF_SIZE:
        return jsonify({'error': 'Arquivo excede o tamanho máximo permitido de 10 MB.'}), 413
    
    file_id = file.filename
    if check_if_file_exists(file_id):
        return jsonify({'error': 'Arquivo já existe.'}), 400
    text = process_pdf_file_to_text(file)
    chunks = chunk_text_recursive(text, 1000, 100, ["\n", " ", ""])
    add_curriculo_to_collection(chunks, file_id, user_id)
    return jsonify({'message': 'PDF processado com sucesso', 'chunks_created': len(chunks)}), 200

@app.route('/delete_curriculum/<file_id>', methods=['DELETE'])
@basic_auth_required
@limiter.limit("3 per minute")
def delete_curriculum(file_id, user_id, role):
    if role != 'admin':
        return jsonify({'error': 'Você não tem permissão para deletar currículos.'}), 403
    if check_if_file_exists(file_id):
        collection.delete(where={"file_id": file_id})
        return jsonify({'message': f'Currículo com id {file_id} deletado com sucesso!'}), 200
    else:
        return jsonify({'error': 'Currículo não encontrado.'}), 404
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
