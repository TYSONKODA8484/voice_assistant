import os
import json
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
import google.generativeai as genai
from datetime import datetime

AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\ffmpeg\bin\ffprobe.exe"

# --- Setup ---
load_dotenv()
app = Flask(__name__)
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")
SESSIONS_FILE = "sessions.json"

COMPANY_CONTEXT = """

Company Overview:
- Name: Crystal Group (The Cold Chain Solutions Company)
- Industry: Transportation, Logistics, Supply Chain, and Storage
- Headquarters: Mumbai, Maharashtra, India
- Followers: 43,000+
- Employees: 201–500
- Founded: 1962
- Website: crystalgroup.in

Mission: Safeguard the quality of temperature-sensitive goods with care and dedication, enabling clients to succeed at every stage.
Vision: To be the most trusted leader in cold chain logistics, empowering businesses with seamless, reliable services and peace of mind.

Core Services:
- Cold Storage Warehousing: Advanced warehouses with temperature control (-25°C to +25°C), real-time monitoring, and hygiene protocols.
- Portable Cold Storage: Flexible, pay-per-day portable cold storage containers for rent or sale.
- Refrigerated Transportation: Fleet of over 200 reefer trucks for pan-India delivery of temperature-sensitive goods.
- Supply Chain Solutions: End-to-end logistics, including last-mile delivery, distribution hubs, and project cargo.
- Value-Added Services: Inventory management, real-time tracking, repackaging, sorting, and labeling.
- Dry Containers: Secure, weather-resistant storage for non-temperature-sensitive goods.
- Specialized Storage: Solutions for pharmaceuticals, food, floriculture, chemicals, and more.

Key Features:
- Temperature Range: -25°C to +25°C (some containers up to -30°C to +30°C)
- Container Sizes: 10ft, 20ft, 40ft (with high-cube and multi-temperature options)
- Advanced Technology: Mobile pallet racking, WMS software, remote monitoring, humidity control, and multi-zone temperature settings
- Certifications: ISO 9001-2008 certified
- Locations: Mumbai (HQ), Kolkata, Bhubaneswar, Howrah
- Clientele: Food & beverage, pharmaceuticals, agriculture, floriculture, chemicals, and more.

Frequently Asked Questions (FAQs) and Topics:
- Storage Capabilities: What products can you store? Do you handle both fresh and frozen goods?
- Temperature Control: What temperature ranges do you offer? Can you customize storage temperatures?
- Container Sizes & Capacity: What sizes of containers are available? How much can each container hold?
- Rental & Purchase Options: Can I rent or buy a portable cold storage container? What are the terms?
- Transportation Services: Do you provide refrigerated transport? What is your delivery coverage?
- Inventory Management: How do you track and monitor inventory? Is real-time tracking available?
- Security & Safety: What security measures are in place? Are you compliant with food/pharma safety standards?
- Pricing & Contracts: What are your rates? Do you offer long-term or short-term contracts?
- Value-Added Services: Do you offer labeling, kitting, or other value-added services?
- Power Backup & Reliability: Do you have backup power systems to prevent spoilage?
- Regulatory Compliance: Are you certified for food safety (HACCP, FSMA, GMP, etc.)?
- Site Visits: Can I schedule a visit to your facility?
- Support & Response Time: How quickly can I get a response or support?

Customer Segments:
- Food & Beverage (producers, distributors, retailers)
- Pharmaceuticals & Healthcare (vaccines, medicines, blood)
- Agriculture & Horticulture (farmers, exporters, floriculture)
- Hospitality & Catering (hotels, restaurants)
- E-commerce & Retail (grocery, meal delivery)
- Chemical & Industrial (temperature-sensitive chemicals)

Always greet the customer, clarify their needs, and provide clear, concise, and helpful answers. If you do not know the answer, offer to connect the customer with a human expert.
"""

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_sessions(sessions):
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/message", methods=["POST"])
def api_message():
    session_id = request.form.get("session_id")
    sessions = load_sessions()
    if session_id not in sessions:
        sessions[session_id] = []
    if "audio" in request.files:
        audio_file = request.files["audio"]
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as fp:
            audio_file.save(fp)
            webm_path = fp.name
        # Convert to WAV
        wav_path = webm_path.replace('.webm', '.wav')
        audio = AudioSegment.from_file(webm_path)
        audio.export(wav_path, format="wav")
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        try:
            user_text = recognizer.recognize_google(audio_data)
        except Exception as e:
            user_text = f"[Could not recognize speech: {e}]"
        os.remove(webm_path)
        os.remove(wav_path)
    else:
        user_text = request.form.get("user_text", "")
    # LLM logic
    history = sessions[session_id]
    prompt = (
        f"{COMPANY_CONTEXT}\n"
        f"Conversation so far:\n" +
        "\n".join([f"User: {m['user']}\nFreddy: {m['bot']}" for m in history]) +
        f"\nCustomer question: {user_text}\n"
        "As Freddy, always provide a direct, friendly, and concise answer using the company information above. "
        "Keep your answer under 200 characters."
    )
    response = model.generate_content(prompt)
    bot_answer = response.text.strip()
    history.append({"user": user_text, "bot": bot_answer, "timestamp": datetime.utcnow().isoformat()})
    save_sessions(sessions)
    return jsonify({"user_text": user_text, "bot": bot_answer})

@app.route("/api/speak", methods=["POST"])
def api_speak():
    text = request.form.get("text")
    tts = gTTS(text=text, lang='en', slow=False)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
        filename = fp.name
    tts.save(filename)
    return send_file(filename, mimetype="audio/mp3", as_attachment=False)

@app.route("/api/sessions", methods=["GET"])
def api_sessions():
    sessions = load_sessions()
    return jsonify({"sessions": list(sessions.keys())})

@app.route("/api/session/<session_id>", methods=["GET"])
def api_session(session_id):
    sessions = load_sessions()
    return jsonify({"history": sessions.get(session_id, [])})

if __name__ == "__main__":
    # Ensure sessions.json exists and is valid
    if not os.path.exists(SESSIONS_FILE) or os.stat(SESSIONS_FILE).st_size == 0:
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            f.write("{}")
    app.run(debug=True)
