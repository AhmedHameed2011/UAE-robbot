import streamlit as st
import edge_tts
import asyncio
import os
import time
import re
from groq import Groq
from dotenv import load_dotenv
from mutagen.mp3 import MP3

# Load local .env file
load_dotenv()

# --- API KEY SETUP ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API"]
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API")

# --- UI SETUP ---
st.set_page_config(page_title="Zayed Robot", page_icon="🇦🇪🤖", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 900px !important; 
    }
    .stApp { background-color: #ffffff; }
    
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.5rem !important; 
        padding-bottom: 0rem !important;
    }

    div[data-testid="stImage"] {
        margin-bottom: -15px !important; 
        padding-bottom: 0px !important;
        line-height: 0 !important;
    }

    h1 { color: #00732f !important; text-align: center; font-family: 'Arial', sans-serif; font-weight: bold; margin-top: 5px !important; margin-bottom: 0px !important; font-size: 24px !important;}
    h2 { text-align: center; color: #333 !important; margin-bottom: 15px !important; margin-top: 0px !important; font-size: 18px !important;}
    
    .arabic-text { text-align: center; font-size: 20px; color: #333; direction: rtl; font-family: 'Tahoma', sans-serif; margin-bottom: 0px; margin-top: 10px; font-weight: bold;}
    .english-text { text-align: center; font-size: 16px; color: #666; margin-bottom: 5px; }

    div[data-testid="stAudioInput"] {
        display: flex;
        justify-content: center;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    
    div[data-testid="stAudioInput"] button {
        background-color: #00732f !important; 
        color: white !important;
        border-radius: 50px !important;
        padding: 10px 20px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0, 115, 47, 0.5) !important;
        font-weight: bold;
    }

    div[data-testid="stAudio"] {
        display: none !important;
    }

    div[data-testid="stMarkdownContainer"], 
    div[data-testid="stAlert"] {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    div[data-testid="stAlert"] p {
        text-align: center !important;
        font-size: 16px !important;
    }

    div[data-testid="stMarkdownContainer"] p {
        text-align: center !important;
        font-size: 18px !important;
        line-height: 1.6 !important;
    }

    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    .thinking-animation {
        text-align: center;
        font-size: 16px;
        color: #00732f;
        animation: pulse 1.5s infinite;
        margin-top: 10px;
    }
    header {visibility: hidden;} footer {visibility: hidden;} #MainMenu {visibility: hidden;}
    hr { display: none; }
    </style>
""", unsafe_allow_html=True)

def file_exists(path):
    return os.path.exists(path)

# --- RENDER UI ---
col_intro1, col_intro2, col_intro3 = st.columns([1, 3, 1])
with col_intro2:
    if file_exists("intro.gif"):
        st.image("intro.gif", use_container_width=True)

st.markdown("<h1>🤖 زايد - صديق اليوم الوطني 55</h1>", unsafe_allow_html=True)
st.markdown("<h2>Zayed - National Day 55 Buddy</h2>", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("<p style='text-align: center; font-size: 16px; font-weight: bold; color: #00732f; margin-bottom: 5px;'>📱 Scan to try on your phone</p>", unsafe_allow_html=True)
    if file_exists("qr_code.png"):
        st.image("qr_code.png", use_container_width=True)
        
    st.markdown("<p class='arabic-text'>👇 تحدث مع زايد</p>", unsafe_allow_html=True)
    st.markdown("<p class='english-text'>👇 Talk to Zayed</p>", unsafe_allow_html=True)
    
    audio_value = st.audio_input(" ", label_visibility="collapsed")

with col_right:
    robot_placeholder = st.empty()
    if file_exists("robot_idle.png"):
        robot_placeholder.image("robot_idle.png", use_container_width=True)
    elif file_exists("robot.png"):
        robot_placeholder.image("robot.png", use_container_width=True)

# --- INITIALIZE GROQ ---
if not GROQ_API_KEY:
    st.error("API Key not found.")
    st.stop()
    
client = Groq(api_key=GROQ_API_KEY)

# --- ROBOT'S PERSONALITY ---
SYSTEM_PROMPT = """
You are "Zayed" (زايد), a friendly robot at a UAE 55th National Day school exhibition. 
Answer parents' questions warmly.
1. If the user speaks Arabic, reply ONLY in Arabic. Do NOT mix English.
2. If the user speaks English, reply ONLY in English.
3. Keep sentences short and clear.
4. If asked about Sheikh Zayed, mention he is the founding father of the UAE, born in 1918, united the Emirates in 1971, and passed away in 2004.
5. The school is "مدرسة الظاهر للشراكات التعليمية".
"""

# --- HELPER FUNCTIONS ---
def transcribe_audio_groq(audio_value):
    if audio_value is None:
        return None, "en"
        
    audio_bytes = audio_value.read()
    
    # تقليل الحد الأدنى للحجم للسماح بالأصوات القصيرة
    if not audio_bytes or len(audio_bytes) < 1000:
        return None, "en"
        
    temp_file = "temp_audio.wav"
    with open(temp_file, "wb") as f:
        f.write(audio_bytes)
    
    try:
        with open(temp_file, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(temp_file, file.read()),
                model="whisper-large-v3-turbo",
                response_format="text",
                language=None
            )
        text = transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
    except Exception as e:
        print(f"--- GROQ TRANSCRIPTION ERROR: {e} ---")
        text = None
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    if text and len(text) > 1:
        lang = "ar" if any('\u0600' <= c <= '\u06FF' for c in text) else "en"
    else:
        text = None
        lang = "en"
    return text, lang

def get_ai_response_stream(user_text):
    stream = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        model="llama-3.1-8b-instant",  # تم التصحيح: استخدام نموذج Groq المدعوم
        temperature=0.7,
        max_tokens=1000, 
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

def clean_text_for_tts(text):
    return re.sub(r'[^\w\s\.\,\!\?\-\:\;]', '', text)

async def generate_tts(text, lang):
    clean_text = clean_text_for_tts(text)
    has_arabic = any('\u0600' <= c <= '\u06FF' for c in clean_text)
    voice = "ar-AE-HamdanNeural" if has_arabic else "en-US-GuyNeural"    
    output_file = "response_audio.mp3"
    communicate = edge_tts.Communicate(clean_text, voice, volume="+100%", rate="+5%")
    await communicate.save(output_file)
    return output_file

# --- RESPONSE LOGIC ---
if audio_value:
    status_placeholder = st.empty()
    user_text_placeholder = st.empty()
    ai_text_placeholder = st.empty()
    audio_placeholder = st.empty()

    if file_exists("robot_talking.gif"):
        robot_placeholder.image("robot_talking.gif", use_container_width=True)
        
    status_placeholder.markdown("<div class='thinking-animation'>🎤 زايد يستمع... / Zayed is listening...</div>", unsafe_allow_html=True)
    user_text, detected_lang = transcribe_audio_groq(audio_value)
    status_placeholder.empty() 
    
    if user_text:
        user_text_placeholder.success(f"**You said / قلت:** {user_text}")
        
        status_placeholder.markdown("<div class='thinking-animation'>🧠 زايد يفكر... / Zayed is thinking...</div>", unsafe_allow_html=True)
        with ai_text_placeholder.container():
            response_text = st.write_stream(get_ai_response_stream(user_text))
        status_placeholder.empty() 
        
        status_placeholder.markdown("<div class='thinking-animation'>🔊 زايد يتحدث... / Zayed is speaking...</div>", unsafe_allow_html=True)
        audio_file = asyncio.run(generate_tts(response_text, detected_lang))
        
        # حساب مدة الصوت الفعلية باستخدام mutagen (لضمان عدم الانتظار طويلاً)
        try:
            audio_length = MP3(audio_file).info.length
        except Exception:
            audio_length = 3  # قيمة افتراضية معقولة
            
        with audio_placeholder.container():
            with open(audio_file, "rb") as f:
                st.audio(f.read(), format="audio/mp3", autoplay=True)
        
        os.remove(audio_file)
        status_placeholder.empty()
        
        # وقت الانتظار: مدة الصوت + ثانية واحدة فقط
        time.sleep(audio_length + 1.0) 
        
        user_text_placeholder.empty()
        ai_text_placeholder.empty()
        audio_placeholder.empty()
        status_placeholder.empty()
        
        if file_exists("robot_idle.png"):
            robot_placeholder.image("robot_idle.png", use_container_width=True)
            
        # مسح الصوت من الذاكرة لمنع التكرار
        if "audio_recorder" in st.session_state:
            del st.session_state["audio_recorder"]
            
        st.rerun()
            
    else:
        status_placeholder.empty()
        st.error("عذراً، لم أفهم كلامك أو أن الصوت لم يُسجل بشكل صحيح. يرجى المحاولة مرة أخرى.\n\nSorry, I couldn't understand or the audio was empty. Please try again.")
        time.sleep(3) 
        
        if file_exists("robot_idle.png"):
            robot_placeholder.image("robot_idle.png", use_container_width=True)
            
        if "audio_recorder" in st.session_state:
            del st.session_state["audio_recorder"]
            
        st.rerun()