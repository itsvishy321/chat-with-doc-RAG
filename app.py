from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
import uuid
from vector_store import VectorStore
from document_processor import DocumentProcessor
from chat_service import ChatService
from database import DatabaseService

load_dotenv()

app = Flask(__name__)

# Initialize services
vector_store = VectorStore()
doc_processor = DocumentProcessor()
chat_service = ChatService()
db_service = DatabaseService() 

# Store for session management
sessions = {}

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/api/process_url', methods=['POST'])
def process_url():
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Process document
        print(f"Processing URL: {url}") 
        content = doc_processor.fetch_content(url)
        chunks = doc_processor.chunk_content(content)
        
        # Store in vector database
        collection_name = f"doc_{session_id}"
        vector_store.create_collection(collection_name)
        vector_store.add_documents(collection_name, chunks, url)
        
        # Store session info
        sessions[session_id] = {
            'url': url,
            'collection_name': collection_name,
            'chat_history': []
        }
        
        # Save session to database
        db_service.create_session(session_id, url, len(chunks))

        return jsonify({
            'session_id': session_id,
            'message': 'Document processed successfully',
            'chunks_count': len(chunks)
        })
        
    except Exception as e:
        print(f"Error processing URL: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        session_id = data.get('session_id')
        question = data.get('question')
        
        if not session_id or not question:
            return jsonify({'error': 'Session ID and question are required'}), 400
        
        if session_id not in sessions:
            return jsonify({'error': 'Invalid session ID'}), 400
        
        session_info = sessions[session_id]
        collection_name = session_info['collection_name']
        
        # Search for relevant chunks
        relevant_chunks = vector_store.search(collection_name, question, limit=5)
        
        # Generate answer using Groq 
        context = "\n\n".join([chunk['content'] for chunk in relevant_chunks])
        answer = chat_service.generate_answer(question, context, session_info['url'])
        
        # Store in chat history
        chat_entry = {
            'question': question,
            'answer': answer,
            'relevant_chunks': len(relevant_chunks)
        }
        session_info['chat_history'].append(chat_entry)
        
         # Save to database
        db_service.save_chat_message(session_id, question, answer, len(relevant_chunks))

        return jsonify({
            'answer': answer,
            'relevant_chunks_count': len(relevant_chunks)
        })
        
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/sessions')
def get_sessions():
    """Get all document sessions"""
    try:
        sessions_data = db_service.get_all_sessions()
        return jsonify({'sessions': sessions_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<session_id>')
def get_session_detail(session_id):
    """Get detailed session info with chat history"""
    try:
        session_data = db_service.get_session_history(session_id)
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404
        return jsonify(session_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500





@app.route('/api/sessions/<session_id>/restore', methods=['POST'])
def restore_session(session_id):
    """Restore a session from database to memory"""
    try:
        session_data = db_service.get_session_history(session_id)
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = session_data['session_info']
        chat_history = session_data['chat_history']
        
        # Restore to in-memory sessions
        collection_name = f"doc_{session_id}"
        sessions[session_id] = {
            'url': session_info['document_url'],
            'collection_name': collection_name,
            'chat_history': [
                {
                    'question': msg['question'],
                    'answer': msg['answer'],
                    'relevant_chunks': msg['relevant_chunks_count']
                }
                for msg in chat_history
            ]
        }
        
        return jsonify({
            'message': 'Session restored successfully',
            'session_info': session_info,
            'chat_history': chat_history
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)