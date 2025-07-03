import os, time
from flask            import Flask, request, send_from_directory, Response
from flask_cors       import CORS
from dotenv           import load_dotenv
from google            import genai

load_dotenv()  # loads GEMINI_API from .env
API_KEY = os.getenv("GEMINI_API")
if not API_KEY:
    raise RuntimeError("GEMINI_API not set in .env")

# Initialize Gemini client
client     = genai.Client(api_key=API_KEY)
MODEL_CHAT = "gemini-2.5-flash"

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

@app.route('/')
@app.route('/voice_agent.html')
def ui():
    return send_from_directory('.', 'voice_agent.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data       = request.get_json(force=True)
    transcript = data.get("transcript")
    if not transcript:
        return {"error": "Missing transcript"}, 400

    # Create a single chat session per client IP (or use cookies/session)
    chat = client.chats.create(model=MODEL_CHAT)

    # Stream tokens as SSE
    def event_stream():
        # Send user turn
        stream = chat.stream_send_message(transcript)
        for token in stream:
            yield f"data: {token.text}\n\n"
        # Signal end
        yield "event: end\n"
        yield "data: \n\n"

    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(port=8001)
