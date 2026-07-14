from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import uuid
import os


from ollama_client import generate_reply
from persistence import (init_chroma, create_page_collection, delete_page_collection,
list_pages, save_message, get_page_messages)


DATA_DIR = os.path.dirname(__file__)
UI_DIR = os.path.join(DATA_DIR, 'ui')


app = Flask(__name__, static_folder=UI_DIR)
CORS(app)


# initialize chroma client
chroma_client = init_chroma()


# simple in-memory index of pages (persisted in chroma as collections)
# we keep a simple list of page metadata in-memory for PoC
pages_index = []


def load_existing_pages():
    """Load existing pages from persistent ChromaDB storage, using persisted titles if available"""
    global pages_index
    try:
        existing_pages = list_pages(chroma_client)
        for page_info in existing_pages:
            title = page_info.get('title')
            if not title:
                # fallback to old style if no title found
                title = f"Page {page_info['id'][:8]}... ({page_info['count']} msgs)" if page_info.get('count') else f"Page {page_info['id'][:8]}..."
            pages_index.append({
                "id": page_info['id'],
                "title": title
            })
        print(f"✅ Loaded {len(pages_index)} existing pages from persistent storage")
    except Exception as e:
        print(f"⚠️ Error loading existing pages: {e}")
        pages_index = []


# helpers
def new_page(title=None):
    page_id = str(uuid.uuid4())
    title = title or f"Page {len(pages_index) + 1}"
    create_page_collection(chroma_client, page_id, title=title)
    pages_index.append({"id": page_id, "title": title})
    return pages_index[-1]


# routes
@app.route('/')
def index():
    return send_from_directory(UI_DIR, 'index.html')


@app.route('/api/pages', methods=['GET', 'POST'])
def pages():
    if request.method == 'GET':
        return jsonify(pages_index)
    data = request.get_json() or {}
    title = data.get('title')
    page = new_page(title)
    return jsonify(page)


@app.route('/api/pages/<page_id>', methods=['DELETE'])
def delete_page(page_id):
    global pages_index
    delete_page_collection(chroma_client, page_id)
    pages_index = [p for p in pages_index if p['id'] != page_id]
    return jsonify({'ok': True})


@app.route('/api/pages/<page_id>/messages', methods=['GET', 'POST'])
def page_messages(page_id):
    if request.method == 'GET':
        # return last 40 messages
        messages = get_page_messages(chroma_client, page_id, limit=40)
        return jsonify(messages)
    
    data = request.get_json() or {}
    role = data.get('role', 'user')
    content = data.get('content', '')
    
    # Save the incoming user message first
    save_message(chroma_client, page_id, role, content)
    
    # fetch context (last 12 messages) to send to model
    context = get_page_messages(chroma_client, page_id, limit=12)
    
    # build messages for Ollama / OpenAI format
    messages = [{'role': m['role'], 'content': m['content']} for m in context if m['role'] in ['user', 'assistant']]
    
    try:
        # call Ollama
        resp_text = generate_reply(messages, model_name='llama3.1')
        
        # save assistant reply
        save_message(chroma_client, page_id, 'assistant', resp_text)
        
        return jsonify({'reply': resp_text})
    except Exception as e:
        print(f"Error generating reply: {e}")
        return jsonify({'error': 'Failed to generate response. Make sure Ollama is running.'}), 500

@app.route('/api/pages/<page_id>/feedback', methods=['POST'])
def feedback(page_id):
    data = request.get_json() or {}
    # store feedback as metadata message
    comment = data.get('comment', '')
    rating = data.get('rating')
    save_message(chroma_client, page_id, 'feedback', f"rating:{rating} comment:{comment}")
    return jsonify({'ok': True})


@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(UI_DIR, path)


if __name__ == '__main__':
    # Load existing pages from persistent storage first
    load_existing_pages()
    
    # Create an initial page only if no pages exist
    if not pages_index:
        default_page = new_page('Welcome Chat')
        print(f"✅ Created default page: {default_page['title']}")
    else:
        print(f"✅ Found {len(pages_index)} existing pages in persistent storage")
    
    print("🚀 Starting Flask server...")
    print("📝 Open http://127.0.0.1:5000 in your browser")
    print("🤖 Make sure Ollama is running with llama3.1 model")
    print(f"💾 Data persisted in: {os.path.join(os.path.dirname(__file__), 'data')}")
    
    app.run(host='127.0.0.1', port=5000, debug=True)