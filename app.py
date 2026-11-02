import streamlit as st
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder
import edge_tts
import asyncio
import os
from groq import Groq
from dotenv import load_dotenv

# Load local .env file (for testing on your laptop)
load_dotenv()

# --- API KEY SETUP ---
# This tries to get the key from Streamlit Cloud Secrets first. 
# If it fails (because you are running locally), it looks in the .env file.
try:
    GROQ_API_KEY = st.secrets["GROQ_API"]
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API")

## --- UI SETUP ---
st.set_page_config(page_title="UAE 55 Robot", page_icon="🤖", layout="centered")

# --- HIDE THE STREAMLIT TOP BAR ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Custom CSS for a friendly, UAE-themed UI
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    h1 { color: #006400; text-align: center; font-family: 'Arial', sans-serif; }
    .robot-text { text-align: center; font-size: 20px; color: #333; margin-top: 20px;}
    .qr-text { text-align: center; font-size: 14px; color: #555; margin-bottom: 30px;}
    </style>
""", unsafe_allow_html=True)



# Header
st.markdown("<h1>🤖 صديق اليوم الوطني 55 | National Day 55 Buddy</h1>", unsafe_allow_html=True)

# --- QR CODE SECTION ---
# Uses columns to center the QR code nicely
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    try:
        # Display the QR code. Ensure 'qr_code.png' is in the same folder!
        st.image("qr_code.png", use_container_width=True)
        st.markdown(
            "<p class='qr-text'>📱 Scan to try on your phone!<br>امسح الرمز للتجربة على هاتفك!</p>", 
            unsafe_allow_html=True
        )
    except Exception:
        st.warning("QR Code image not found. Please ensure 'qr_code.png' is in the folder.")

# --- INSTRUCTIONS ---
st.markdown("<p class='robot-text'>مرحباً بك! اضغط على المايك وتحدث بالعربية أو الإنجليزية.<br>Welcome! Press the mic and speak in Arabic or English.</p>", unsafe_allow_html=True)

# --- INITIALIZE GROQ ---
if not GROQ_API_KEY:
    st.error("API Key not found. Please check your Streamlit Secrets or .env file.")
    st.stop()
    
client = Groq(api_key=GROQ_API_KEY)

# --- ROBOT'S PERSONALITY (SYSTEM PROMPT) ---
SYSTEM_PROMPT = """
You are a friendly, intelligent robot at a school exhibition for the UAE 55th National Day.
Your job is to answer parents' questions.
You MUST follow these rules strictly:
1. If the user speaks Arabic, reply in Arabic.
2. If the user speaks English, reply in English.
3. Keep your answers short (1-2 sentences), friendly, and enthusiastic.
4. Remember these facts:
   - The UAE 55th National Day is on December 2nd, 2026.
   - This exhibition showcases student projects in Artificial Intelligence.
   - You are built using Python and AI by a brilliant students.
"""

# --- HELPER FUNCTIONS ---

def transcribe_audio(audio_bytes):
    """Converts speech to text, trying Arabic first, then English."""
    r = sr.Recognizer()
    temp_file = "temp_audio.wav"
    
    with open(temp_file, "wb") as f:
        f.write(audio_bytes)
    
    with sr.AudioFile(temp_file) as source:
        audio_data = r.record(source)
        
    try:
        # Try Arabic first
        text = r.recognize_google(audio_data, language="ar-AE")
        lang = "ar"
    except sr.UnknownValueError:
        try:
            # Fallback to English
            text = r.recognize_google(audio_data, language="en-US")
            lang = "en"
        except:
            text = None
            lang = "en"
            
    if os.path.exists(temp_file):
        os.remove(temp_file)
    return text, lang

def get_ai_response(user_text):
    """Sends text to Groq and gets a response."""
    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        model="openai/gpt-oss-20b", # The updated Groq model
        temperature=0.6,
        max_tokens=150,
    )
    return completion.choices[0].message.content

async def generate_tts(text, lang):
    """Generates an MP3 file using Microsoft Edge TTS."""
    if lang == "ar":
        voice = "ar-AE-FatimaNeural" # Emirati Arabic voice
    else:
        voice = "en-US-AriaNeural"   # Friendly English voice
        
    output_file = "response_audio.mp3"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    return output_file

# --- MAIN APP LOGIC ---

# The Audio Recorder Widget
audio_bytes = audio_recorder(
    text="Press to speak / اضغط للتحدث",
    recording_color="#FF0000",
    neutral_color="#006400",
    icon_name="microphone",
    icon_size="3x",
)

if audio_bytes:
    st.info("Processing... / جاري المعالجة...")
    
    # Step 1: Listen
    user_text, detected_lang = transcribe_audio(audio_bytes)
    
    if user_text:
        st.success(f"**You said / قلت:** {user_text}")
        
        # Step 2: Think
        with st.spinner("Thinking... / جاري التفكير..."):
            ai_response = get_ai_response(user_text)
            st.info(f"**Robot:** {ai_response}")
            
        # Step 3: Speak
        with st.spinner("Speaking... / جاري التحدث..."):
            audio_file = asyncio.run(generate_tts(ai_response, detected_lang))
            
            # Play the audio automatically
            with open(audio_file, "rb") as f:
                audio_data = f.read()
                st.audio(audio_data, format="audio/mp3", autoplay=True)
            
            # Clean up the file
            if os.path.exists(audio_file):
                os.remove(audio_file)
    else:
        st.error("Sorry, I couldn't understand. Please try again. / عذراً، لم أفهم. حاول مرة أخرى.")