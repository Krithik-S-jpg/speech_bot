import streamlit as st
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

# Streamlit Page
st.set_page_config(page_title="AI Voice Companion", page_icon="🤖", layout="wide")
st.title("🤖 Ask Pookie - Your AI Companion")

# Background
st.markdown("""
<style>
.stApp {
    background-image: url('https://i.pinimg.com/originals/6d/46/f9/6d46f977733e6f9a9fa8f356e2b3e0fa.gif');
    background-size: cover;
}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("Settings")
voice_selection = st.sidebar.radio("Select Voice", ["Male", "Female"], index=0)
language_selection = st.sidebar.radio("Choose Language", ["English", "Tamil", "Malayalam", "Telugu", "Hindi"], index=0)

ELEVENLABS_VOICE_ID = ELEVENLABS_VOICE_ID_FEMALE if voice_selection == "Female" else ELEVENLABS_VOICE_ID_MALE

# Recorder
st.subheader("🎙️ Record Your Voice")

audio_file = st.file_uploader("Upload your audio (WAV/MP3)", type=["wav", "mp3"])

# Process audio
if audio_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(audio_file.read())
        tmp_file_path = tmp_file.name

    # Transcribe
    with st.spinner("🔎 Transcribing..."):
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(tmp_file_path)
        recognized_text = transcript.text if transcript else ""

    if recognized_text:
        st.success(f"✅ Recognized: {recognized_text}")

        # Gemini Response
        with st.spinner("🤖 Generating AI response..."):
            model = gen_ai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Respond in {language_selection}. For the query '{recognized_text}', generate a friendly helpful response in 10-25 words without asking follow-up questions."
            response = model.generate_content(prompt)
            ai_text = response.text

        st.subheader("💬 AI Response")
        st.write(ai_text)

        # ElevenLabs Text-to-Speech
        with st.spinner("🔊 Generating voice..."):
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
        st.error("❌ Could not detect any speech. Try again.")
