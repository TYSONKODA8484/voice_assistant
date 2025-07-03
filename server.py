import os, base64, wave, io
from flask      import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv     import load_dotenv
from google     import genai
from google.genai import types

# ─── Configuration ───────────────────────────────────────────────────────────
load_dotenv()  # Loads GEMINI_API from .env
API_KEY    = os.getenv("GEMINI_API")
if not API_KEY:
    raise RuntimeError("GEMINI_API not set in .env")

client     = genai.Client(api_key=API_KEY)
MODEL_CHAT = "gemini-2.5-flash"                # Chat model
MODEL_TTS  = "gemini-2.5-flash-preview-tts"    # TTS model

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Serve the UI
@app.route('/')
@app.route('/voice_agent.html')
def ui():
    return send_from_directory('.', 'voice_agent.html')

# Main API: takes { transcript } and returns { reply, audio }
@app.route('/api/voice', methods=['POST'])
def voice():
    data       = request.get_json(force=True)
    transcript = data.get('transcript')
    if not transcript:
        return jsonify(error="Missing 'transcript'"), 400

    # 1) Generate text reply via Chat API
    chat = client.chats.create(model=MODEL_CHAT)
    resp = chat.send_message(transcript)
    reply = resp.text

    # 2) Generate audio from the reply
    tts_resp = client.models.generate_content(
        model=MODEL_TTS,
        contents=reply,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Kore"
                    )
                )
            )
        )
    )

    # Extract PCM, wrap in WAV in-memory
    pcm      = tts_resp.candidates[0].content.parts[0].inline_data.data
    buf      = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm)
    wav_bytes = buf.getvalue()

    # Base64-encode WAV for JSON transport
    audio_b64 = base64.b64encode(wav_bytes).decode('utf-8')

    return jsonify(reply=reply, audio=audio_b64)

if __name__ == '__main__':
    app.run(port=8000)
