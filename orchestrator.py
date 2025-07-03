# orchestrator.py (simplified)
import asyncio, websockets, sounddevice as sd

async def voice_session():
    # 1) STT client captures audio + speech-to-text...
    transcript = await stt_client.recognize_once()

    # 2) Chat streaming (WebSocket)
    async with websockets.connect("ws://chat-agent:8001/stream") as ws:
        await ws.send(transcript)
        # 3) As tokens arrive, pipe to TTS streaming
        async for msg in ws:
            token = msg["token"]
            audio_chunk = await tts_client.speak_stream(token)
            sd.play(audio_chunk, samplerate=24000)  # immediate playback

asyncio.run(voice_session())
