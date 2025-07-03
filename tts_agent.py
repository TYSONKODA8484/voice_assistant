import os, base64, wave, io
from flask            import Flask, request, jsonify
from flask_cors       import CORS
from dotenv           import load_dotenv
from google            import genai
from google.genai      import types

load_dotenv()
API_KEY   = os.getenv("GEMINI_API")
if not API_KEY:
    raise RuntimeError("GEMINI_API not set in .env")

client    = genai.Client(api_key=API_KEY)
MODEL_TTS = "gemini-2.5-flash-preview-tts"

app = Flask(__name__)
CORS(app)

@app.route('/api/tts', methods=['POST'])
def tts():
    data = request.get_json(force=True)
    text = data.get("text")
    if not text:
        return {"error": "Missing text"}, 400

    resp = client.models.generate_content(
        model=MODEL_TTS,
        contents=text,
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

    pcm    = resp.candidates[0].content.parts[0].inline_data.data
    buf    = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm)
    audio_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return jsonify(audio=audio_b64)

if __name__ == '__main__':
    app.run(port=8002)
