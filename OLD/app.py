# app.py
import os, base64, wave, io
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ─── Configuration ─────────────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("GEMINI_API")
if not API_KEY:
    st.error("GEMINI_API not set in .env")
    st.stop()

client = genai.Client(api_key=API_KEY)
MODEL_TTS = "gemini-2.5-flash-preview-tts"

st.title("🎙️ Instant Voice Q&A with Gemini TTS")
st.write("Type your question and press **Enter**; Gemini will answer via speech (≤400 chars).")

# ─── Text Input with auto-trigger ──────────────────────────────────────────
if "last_q" not in st.session_state:
    st.session_state.last_q = ""

question = st.text_input("Your question:", key="question")

# Only re-run TTS when the question changes
if question and question != st.session_state.last_q:
    st.session_state.last_q = question
    prompt = f"Answer concisely in ≤400 characters: {question}"

    with st.spinner("Generating answer…"):
        try:
            response = client.models.generate_content(
                model=MODEL_TTS,
                contents=prompt,
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
            pcm = response.candidates[0].content.parts[0].inline_data.data

            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(pcm)
            wav_bytes = buf.getvalue()

        except Exception as e:
            st.error(f"TTS generation failed: {e}")
            st.stop()

    # ─── Auto-play audio ────────────────────────────────────────────────
    st.audio(wav_bytes, format="audio/wav")
