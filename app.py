import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import av
import assemblyai as aai
import google.generativeai as gen_ai
import requests
import tempfile
import os

# API Keys
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
gen_ai.configure(api_key=os.getenv("GEMINI_API_KEY"))

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID_MALE = "pNInz6obpgDQGcFmaJgB"
ELEVENLABS_VOICE_ID_FEMALE = "21m00Tcm4TlvDq8ikWAM"

# Streamlit Page Setup
st.set_page_config(page_title="AI Voice Companion", page_icon="🤖", layout="wide")
st.title("🤖 Ask Pookie - Your AI Companion")

# Sidebar
st.sidebar.header("Settings")
voice_selection = st.sidebar.radio("Select Voice", ["Male", "Female"], index=0)
language_selection = st.sidebar.radio("Choose Language", ["English", "Tamil", "Malayalam", "Telugu", "Hindi"], index=0)

ELEVENLABS_VOICE_ID = ELEVENLABS_VOICE_ID_FEMALE if voice_selection == "Female" else ELEVENLABS_VOICE_ID_MALE

# Recorder setup
st.subheader("🎙️ Record your voice")

ctx = webrtc_streamer(
    key="audio",
    mode=WebRtcMode.SENDONLY,
    client_settings=ClientSettings(
        media_stream_constraints={
            "audio": True,
            "video": False,
        },
    ),
)

if ctx.audio_receiver:
    audio_frames = ctx.audio_receiver.get_frames(timeout=5)

    # Save audio to temporary WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        with av.open(f.name, mode='w', format='wav') as container:
            stream = container.add_stream('pcm_s16le')
            for frame in audio_frames:
                container.mux(frame)
        audio_path = f.name

    st.audio(audio_path)

    # Transcribe audio
    with st.spinner("🔎 Transcribing..."):
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_path)
        recognized_text = transcript.text

    if recognized_text:
        st.success(f"✅ You said: {recognized_text}")

        # Gemini Response
        with st.spinner("🤖 AI Thinking..."):
            model = gen_ai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Respond in {language_selection} for: '{recognized_text}'"
            response = model.generate_content(prompt)
            ai_text = response.text

        st.subheader("💬 AI Response")
        st.write(ai_text)

        # ElevenLabs TTS
        with st.spinner("🔊 Speaking back..."):
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": ELEVENLABS_API_KEY,
            }
            data = {
                "text": ai_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8
                }
            }
            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                st.audio(response.content, format="audio/mp3")
            else:
                st.error(f"ElevenLabs Error: {response.text}")

    else:
        st.error("❌ Couldn't recognize speech. Try again.")

