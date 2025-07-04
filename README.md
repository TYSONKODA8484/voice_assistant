# Freddy Voice Assistant

A fully local, free, voice-enabled AI assistant for customer support and general Q&A, powered by Google Gemini (Gemma) and Google Text-to-Speech (gTTS).

---

## Why This Tech Stack?

- **No ChatGPT API**: ChatGPT and similar OpenAI APIs are paid and may have usage restrictions. This project uses **Google Gemini (Gemma)**, which offers a free tier for developers and is suitable for prototyping and small-scale production.
- **Free, Local Voice**: Uses `gTTS` (Google Text-to-Speech) for natural-sounding voice output, which is free and easy to use.
- **No Cloud Speech-to-Text Fees**: Uses the free Google Web Speech API via the `SpeechRecognition` Python library for speech-to-text.
- **All code runs locally**: No data is sent to OpenAI or other paid services.

---

## Features

- **Voice-activated**: Speak your question, get a spoken answer.
- **Text and voice output**: See and hear both your question and the assistant's answer.
- **Session history**: All conversations are saved in a JSON file for future reference.
- **Company-aware**: The assistant ("Freddy") uses your provided company context for accurate, on-brand answers.
- **No manual text input required**: Just speak and listen.
- **Runs on your own machine**: No cloud deployment needed.

---

## How It Works

1. **Startup**: The assistant greets you with a spoken message.
2. **Listening**: The program listens for your voice input via your microphone.
3. **Speech-to-Text**: Your speech is transcribed to text using the Google Web Speech API.
4. **LLM Answer**: The transcribed question, along with conversation history and company context, is sent to the Gemini (Gemma) LLM for a concise, professional answer.
5. **Text-to-Speech**: The answer is spoken aloud using Google Text-to-Speech (gTTS) and also printed to the console.
6. **Session Logging**: Each question and answer is saved in a JSON file (`freddy_history.json`).
7. **Loop**: The assistant is ready for your next question. Press `Ctrl+C` to exit.

---
## Code Overview

- **Speech Recognition**: Uses your microphone to capture audio and transcribes it to text.
- **LLM Integration**: Sends the question and conversation history to Gemini (Gemma) for a context-aware answer.
- **Voice Output**: Uses gTTS to synthesize the answer and plays it back.
- **Session History**: All interactions are saved in `freddy_history.json` for future reference.


## Customization & Improvements

- **LLM API**: You can swap Gemini for any other LLM API (e.g., OpenAI, Anthropic) by changing the `get_freddy_answer` function.
- **Voice API**: For even more natural voices, you can use cloud TTS APIs (e.g., Azure, ElevenLabs) if you wish.
- **UI**: This script is console-based, but you can build a web or desktop UI on top of this logic.

---

## Limitations

- **gTTS requires an internet connection** for voice synthesis.
- **Gemini free tier** may have usage limits.
- **No real-time streaming**: The assistant processes after you finish speaking, not while you speak.
- **Not suitable for production** as-is; for production, use a WSGI server and add error handling, logging, and security.

---

## Why Not ChatGPT?

- **Cost**: ChatGPT and other OpenAI APIs are paid and may incur significant costs for frequent use.
- **Free Tier**: Google Gemini gemma is used here but other model are better but have rate limit issue  offers a generous free tier for developers.
- **Flexibility**: This stack is open, local, and can be easily swapped for other free or paid APIs as needed.

---