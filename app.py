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
try:
    GROQ_API_KEY = st.secrets["GROQ_API"]
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API")

# --- UI SETUP ---
st.set_page_config(page_title="UAE 55 Robot", page_icon="🇦🇪", layout="centered")

# --- CUSTOM CSS FOR EXHIBITION KIOSK ---
st.markdown("""
    <style>
    /* Main background */
    .stApp { 
        background-color: #f8f9fa; 
    }
    
    /* UAE Flag Top Border */
    .uae-border {
        height: 10px;
        background: linear-gradient(to right, #00732f 33%, #ffffff 33%, #ffffff 66%, #000000 66%);
        border-top: 5px solid #ff0000;
        margin-bottom: 30px;
        border-radius: 5px;
    }

    /* Title Styling */
    h1 { 
        color: #00732f; 
        text-align: center; 
        font-family: 'Arial', sans-serif; 
        font-weight: bold;
    }
    
    /* The "Card" for QR Code */
    .qr-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        text-align: center;
        margin: 20px auto;
        max-width: 300px;
    }

    /* Bilingual Text Styling */
    .arabic-text { 
        text-align: center; 
        font-size: 22px; 
        color: #333; 
        direction: rtl; 
        font-family: 'Tahoma', sans-serif;
        margin-bottom: 5px;
    }
    .english-text { 
        text-align: center; 
        font-size: 18px; 
        color: #666; 
        margin-bottom: 20px;
    }
    
    /* Hide standard Streamlit header/footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- RENDER UI ---
# UAE Flag Border
st.markdown("<div class='uae-border'></div>", unsafe_allow_html=True)

# Header
st.markdown("<h1>🤖 صديق اليوم الوطني 55</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #333;'>National Day 55 Buddy</h2>", unsafe_allow_html=True)

# QR Code & Instructions Card
st.markdown("""
    <div class='qr-card'>
        <p style='font-size: 16px; font-weight: bold; color: #00732f;'>📱 Scan to try on your phone</p>
    </div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    try:
        st.image("qr_code.png", use_container_width=True)
    except Exception:
        st.warning("QR Code image not found. Please ensure 'qr_code.png' is in the folder.")

# Instructions (Bilingual)
st.markdown("<p class='arabic-text'>مرحباً بك! اضغط على المايك وتحدث بالعربية أو الإنجليزية.</p>", unsafe_allow_html=True)
st.markdown("<p class='english-text'>Welcome! Press the mic and speak in Arabic or English.</p>", unsafe_allow_html=True)

# --- INITIALIZE GROQ ---
if not GROQ_API_KEY:
    st.error("API Key not found. Please check your Streamlit Secrets or .env file.")
    st.stop()
    
client = Groq(api_key=GROQ_API_KEY)

# --- ROBOT'S PERSONALITY ---
SYSTEM_PROMPT = """
You are a friendly, intelligent robot at a school exhibition for the UAE 55th National Day.
Your job is to answer parents' questions.
You MUST follow these rules strictly:
1. If the user speaks Arabic, reply in Arabic.
2. If the user speaks English, reply in English.
3. Provide a detailed, warm, and engaging answer (about 3 to 4 sentences). Elaborate on the facts to make it interesting for the parents.
4. Remember these facts:
   - The UAE 55th National Day is on December 2nd, 2026.
   - This exhibition showcases student projects in Artificial Intelligence.
   - You are built using Python and AI by a brilliant student.
"""

# --- HELPER FUNCTIONS ---
def transcribe_audio(audio_bytes):
    r = sr.Recognizer()
    temp_file = "temp_audio.wav"
    with open(temp_file, "wb") as f:
        f.write(audio_bytes)
    with sr.AudioFile(temp_file) as source:
        audio_data = r.record(source)
    try:
        text = r.recognize_google(audio_data, language="ar-AE")
        lang = "ar"
    except sr.UnknownValueError:
        try:
            text = r.recognize_google(audio_data, language="en-US")
            lang = "en"
        except:
            text = None
            lang = "en"
    if os.path.exists(temp_file):
        os.remove(temp_file)
    return text, lang

def get_ai_response(user_text):
    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        model="openai/gpt-oss-20b",
        temperature=0.6,
        max_tokens=300,
    )
    return completion.choices[0].message.content

async def generate_tts(text, lang):
    if lang == "ar":
        voice = "ar-AE-FatimaNeural" 
    else:
        voice = "en-US-AriaNeural"   
    output_file = "response_audio.mp3"
    # Increased volume and rate
    communicate = edge_tts.Communicate(text, voice, volume="+100%", rate="+10%")
    await communicate.save(output_file)
    return output_file

# --- MAIN APP LOGIC ---
st.write("---") # Visual separator

# Center the Audio Recorder
col_mic1, col_mic2, col_mic3 = st.columns([1, 1, 1])
with col_mic2:
    audio_bytes = audio_recorder(
        text="Click to Speak | اضغط للتحدث",
        recording_color="#ff0000",
        neutral_color="#00732f",
        icon_name="microphone",
        icon_size="3x",
    )

if audio_bytes:
    st.info("Processing... / جاري المعالجة...")
    user_text, detected_lang = transcribe_audio(audio_bytes)
    
    if user_text:
        # Display what the user said in a nice box
        st.success(f"**You said / قلت:** {user_text}")
        
        with st.spinner("Thinking... / جاري التفكير..."):
            ai_response = get_ai_response(user_text)
            # Display AI response in a chat bubble style
            st.info(f"**🤖 Robot:** {ai_response}")
            
        with st.spinner("Speaking... / جاري التحدث..."):
            audio_file = asyncio.run(generate_tts(ai_response, detected_lang))
            with open(audio_file, "rb") as f:
                audio_data = f.read()
                st.audio(audio_data, format="audio/mp3", autoplay=True)
            if os.path.exists(audio_file):
                os.remove(audio_file)
    else:
        st.error("Sorry, I couldn't understand. Please try again. / عذراً، لم أفهم. حاول مرة أخرى.")