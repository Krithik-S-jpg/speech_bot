import streamlit as st
import assemblyai as aai
import google.generativeai as gen_ai
import requests
import os
import base64
import io
from pydub import AudioSegment

# Streamlit page setup
st.set_page_config(page_title="AI Voice Companion", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

# Background CSS
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

# Title
st.title("🤖 Ask Pookie - Your AI Companion")

# Sidebar
st.sidebar.header("Settings")
voice_selection = st.sidebar.radio("Select Voice", ["Male", "Female"])
language_selection = st.sidebar.radio("Choose Language", ["English", "Tamil", "Malayalam", "Telugu", "Hindi"], index=0)
volume_percent = st.sidebar.slider("Volume", 0, 100, 100)

# Set Voice ID
ELEVENLABS_VOICE_ID = ELEVENLABS_VOICE_ID_FEMALE if voice_selection == "Female" else ELEVENLABS_VOICE_ID_MALE
ELEVENLABS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"

# Recorder frontend using HTML + JS
st.markdown("""
    <h3>🎙️ Record your voice</h3>
    <audio id="audio" controls></audio><br>
    <button id="start">Start Recording</button>
    <button id="stop">Stop Recording</button>

    <script>
        let mediaRecorder;
        let audioChunks;

        document.getElementById('start').onclick = async function() {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = function(event) {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = function() {
                const audioBlob = new Blob(audioChunks);
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = document.getElementById('audio');
                audio.src = audioUrl;

                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = function() {
                    const base64AudioMessage = reader.result.split(',')[1];
                    const xhr = new XMLHttpRequest();
                    xhr.open('POST', '/recorded_audio');
                    xhr.setRequestHeader('Content-Type', 'application/json');
                    xhr.send(JSON.stringify({ audio_data: base64AudioMessage }));
                }
            };

            mediaRecorder.start();
        };

        document.getElementById('stop').onclick = function() {
            mediaRecorder.stop();
        };
    </script>
""", unsafe_allow_html=True)

# Receive recorded audio
from streamlit_server_state import server_state, server_state_lock

if "audio_data" not in server_state:
    server_state.audio_data = None

if st.experimental_get_query_params().get("recorded_audio"):
    server_state.audio_data = st.experimental_get_query_params()["recorded_audio"]

# Function to transcribe
def transcribe_audio_bytes(audio_bytes):
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_bytes)

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe("temp_audio.wav")
    return transcript.text if transcript else ""

# Function for Gemini
def gemini_chat(query, lang):
    try:
        prompt = f"Respond in {lang}. For the query '{query}', generate a helpful response in 10-25 words without asking follow-up questions."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# ElevenLabs speech
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

# If audio recorded
if server_state.audio_data:
    audio_bytes = base64.b64decode(server_state.audio_data)
    st.audio(audio_bytes, format="audio/wav")

    recognized_text = transcribe_audio_bytes(audio_bytes)

    if recognized_text.strip():
        st.success(f"✅ Recognized: {recognized_text}")
        response = gemini_chat(recognized_text, language_selection)
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
