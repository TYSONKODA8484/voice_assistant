import streamlit as st
import os
import json
import re
import time
from datetime import datetime
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import tempfile
import speech_recognition as sr
import google.generativeai as genai
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

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

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

def clean_text(text):
    return re.sub(r'[*_`]', '', text)

def get_freddy_answer(question, history):
    # Build the prompt with history for context
    history_prompt = "\n".join(
        [f"User: {item['user']}\nFreddy: {item['bot']}" if item['bot'] else f"User: {item['user']}" for item in history]
    )
    prompt = (
        f"{COMPANY_CONTEXT}\n"
        f"Conversation so far:\n{history_prompt}\n"
        f"Customer question: {question}\n"
        "As Freddy, always provide a direct, friendly, and concise answer using the company information above. "
        "Maintain a professional tone—do not use emojis or informal symbols. Only ask for clarification if the question is unclear. "
        "Keep your answer under 200 characters. If unsure, offer to connect them to a human expert."
    )
    response = model.generate_content(prompt)
    return response.text.strip()

def speak(text):
    tts = gTTS(text=text, lang='en', slow=False)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
        filename = fp.name
    tts.save(filename)
    audio = AudioSegment.from_mp3(filename)
    play(audio)
    os.remove(filename)

def save_session(session_id, history):
    with open(os.path.join(SESSIONS_DIR, f"{session_id}.json"), "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_session(session_id):
    try:
        with open(os.path.join(SESSIONS_DIR, f"{session_id}.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def list_sessions():
    return [f.replace(".json", "") for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")]

# --- Streamlit UI ---
st.set_page_config(page_title="Freddy - Crystal Group Assistant", layout="centered")
st.title("Freddy: Crystal Group Voice Assistant")

# Session selection/creation
session_ids = list_sessions()
selected_session = st.sidebar.selectbox("Select session", session_ids + ["New Session"], index=len(session_ids))
if selected_session == "New Session" or "session_id" not in st.session_state:
    session_id = datetime.now().strftime("%Y%m%d%H%M%S")
    st.session_state["session_id"] = session_id
    st.session_state["history"] = []
    save_session(session_id, [])
else:
    session_id = selected_session
    st.session_state["session_id"] = session_id
    st.session_state["history"] = load_session(session_id)

# Show chat history
for msg in st.session_state["history"]:
    st.markdown(f"**You:** {msg['user']}")
    if msg['bot']:
        st.markdown(f"**Freddy:** {msg['bot']}")

# Voice input (fallback to text)
st.markdown("#### Speak or type your question:")

audio_bytes = None
try:
    import streamlit.components.v1 as components
    audio_bytes = st.file_uploader("Upload a WAV file (or use text input below)", type=["wav"])
except Exception:
    pass

user_input = st.text_input("Or type here:")

if st.button("Send") or audio_bytes:
    if audio_bytes:
        # Save audio and transcribe
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as fp:
            fp.write(audio_bytes.read())
            audio_path = fp.name
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        try:
            user_text = recognizer.recognize_google(audio)
        except Exception as e:
            user_text = f"[Could not recognize speech: {e}]"
        os.remove(audio_path)
    else:
        user_text = user_input

    if user_text.strip():
        st.session_state["history"].append({"user": user_text, "bot": ""})
        answer = get_freddy_answer(user_text, st.session_state["history"])
        answer_clean = clean_text(answer)
        st.session_state["history"][-1]["bot"] = answer_clean
        save_session(session_id, st.session_state["history"])
        st.markdown(f"**Freddy:** {answer_clean}")
        speak(answer_clean)

# Option to stop conversation (end app)
if st.button("Stop Conversation"):
    st.stop()

st.sidebar.markdown("**Session data is saved as JSON and never deleted.**")
