import streamlit as st
import assemblyai as aai
import google.generativeai as gen_ai
import requests
import os
import tempfile

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

# Recorder using audio_recorder
audio_bytes = st.audio_recorder(
    text="🎙️ Click to Record",
    recording_color="#e60073",
    neutral_color="#6c757d",
    icon_size="2x",
)

if audio_bytes:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_file_path = tmp_file.name

    # Transcription
    with st.spinner("🔎 Transcribing your speech..."):
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(tmp_file_path)
        recognized_text = transcript.text if transcript else ""

    if recognized_text:
        st.success(f"✅ You said: {recognized_text}")

        # Gemini Response
        with st.spinner("🤖 AI is thinking..."):
            model = gen_ai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Respond in {language_selection}. For the query '{recognized_text}', generate a short friendly helpful response."
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
        st.error("❌ Couldn't detect any speech. Try again.")

