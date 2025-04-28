import streamlit as st
import assemblyai as aai
import google.generativeai as gen_ai
import requests
import os
from streamlit_mic_recorder import mic_recorder  # <<< Changed

# Streamlit page settings
st.set_page_config(page_title="AI Voice Companion", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

# Background style
background_css = """
 <style>
     .stApp {
         background-image: url('https://i.pinimg.com/originals/6d/46/f9/6d46f977733e6f9a9fa8f356e2b3e0fa.gif');
         background-size: cover;
         background-position: center;
         background-attachment: fixed;
     }
     header {
         visibility: hidden;
     }
 </style>
"""
st.markdown(background_css, unsafe_allow_html=True)

# Configure APIs
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
gen_ai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = gen_ai.GenerativeModel('gemini-1.5-flash')

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID_MALE = "pNInz6obpgDQGcFmaJgB"
ELEVENLABS_VOICE_ID_FEMALE = "21m00Tcm4TlvDq8ikWAM"

# App Title
st.title("🤖 Ask Pookie - Your AI Companion")

# Sidebar settings
st.sidebar.header("Settings")
voice_selection = st.sidebar.radio("Select Voice", ["Male", "Female"])
language_selection = st.sidebar.radio("Choose Language", ["English", "Tamil", "Malayalam", "Telugu", "Hindi"], index=0)
volume_percent = st.sidebar.slider("Volume", 0, 100, 100)

# Voice ID selection
ELEVENLABS_VOICE_ID = ELEVENLABS_VOICE_ID_FEMALE if voice_selection == "Female" else ELEVENLABS_VOICE_ID_MALE
ELEVENLABS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"

# Functions
def transcribe_audio(audio_file):
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)
    return transcript.text if transcript else ""

def gemini_chat(query, lang):
    try:
        prompt = f"Respond in {lang}. For the query '{query}', generate a helpful response in 10-25 words without asking follow-up questions."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def text_to_speech_elevenlabs(text):
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY,
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8
        }
    }
    response = requests.post(ELEVENLABS_URL, json=data, headers=headers)

    if response.status_code == 200:
        audio_path = "response_audio.mp3"
        with open(audio_path, "wb") as f:
            f.write(response.content)
        return audio_path
    else:
        st.error(f"⚠ ElevenLabs API Error: {response.text}")
        return None

# --- Main App ---

st.subheader("🎙 Record your voice")

# 🎤 NEW MIC RECORDER
audio_data = mic_recorder(
    start_prompt="🎤 Start recording",
    stop_prompt="⏹ Stop recording",
    key="recorder"
)

if audio_data:
    st.success("✅ Recording complete!")

    audio_bytes = audio_data["bytes"]  # <-- extract the bytes part

    st.audio(audio_bytes, format="audio/wav")  # Play audio

    # Save audio to a file
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_bytes)

    # Transcribe
    user_text = transcribe_audio("temp_audio.wav")

    if user_text.strip():
        st.success(f"✅ Recognized: {user_text}")
        response = gemini_chat(user_text, language_selection)
        st.subheader("💬 AI Response")
        st.write(response)

        audio_path = text_to_speech_elevenlabs(response)
        if audio_path:
            st.audio(audio_path, format="audio/mp3")
            st.info(f"🔊 Set your system volume to {volume_percent}% for best experience.")
        else:
            st.error("⚠ Failed to generate speech.")
    else:
        st.warning("❌ No speech detected, please try again.")
else:
    st.info("⬆ Click the mic button above to record!")