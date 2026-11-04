import streamlit as st
import edge_tts
import asyncio
import os
import time
from groq import Groq
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder
from mutagen.mp3 import MP3 # مكتبة جديدة لحساب مدة الصوت

# Load local .env file
load_dotenv()

# --- API KEY SETUP ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API"]
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API")

# --- UI SETUP ---
st.set_page_config(page_title="Zayed Robot", page_icon="🇦🇪", layout="centered")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .uae-border {
        height: 10px;
        background: linear-gradient(to right, #00732f 33%, #ffffff 33%, #ffffff 66%, #000000 66%);
        border-top: 5px solid #ff0000;
        margin-bottom: 30px;
        border-radius: 5px;
    }
    h1 { color: #00732f; text-align: center; font-family: 'Arial', sans-serif; font-weight: bold; }
    .qr-card {
        background-color: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); text-align: center;
        margin: 20px auto; max-width: 300px;
    }
    .arabic-text { text-align: center; font-size: 24px; color: #333; direction: rtl; font-family: 'Tahoma', sans-serif; margin-bottom: 5px; font-weight: bold;}
    .english-text { text-align: center; font-size: 18px; color: #666; margin-bottom: 20px; }
    
    div[data-testid="stAudioRecorder"] button {
        transform: scale(1.8);
        margin: 30px 0px;
        box-shadow: 0 0 20px rgba(0, 115, 47, 0.4);
        border: 2px solid #00732f;
    }

    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    .thinking-animation {
        text-align: center;
        font-size: 20px;
        color: #00732f;
        animation: pulse 1.5s infinite;
        margin-top: 20px;
    }
    
    header {visibility: hidden;} footer {visibility: hidden;} #MainMenu {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- RENDER UI ---
st.markdown("<div class='uae-border'></div>", unsafe_allow_html=True)
st.markdown("<h1>🤖 زايد - صديق اليوم الوطني 55</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #333;'>Zayed - National Day 55 Buddy</h2>", unsafe_allow_html=True)

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
        st.warning("QR Code image not found.")

# --- INITIALIZE GROQ ---
if not GROQ_API_KEY:
    st.error("API Key not found.")
    st.stop()
    
client = Groq(api_key=GROQ_API_KEY)

# --- ROBOT'S PERSONALITY ---
SYSTEM_PROMPT = """
You are "Zayed" (زايد), a very friendly and welcoming robot at a UAE 55th National Day school exhibition. 
When you introduce yourself, you should say something like: "أنا زايد، الروبوت الودود" (I am Zayed, the friendly robot).
Your job is to answer parents' questions.
You MUST follow these rules strictly:
1. If the user speaks Arabic, reply in Arabic.
2. If the user speaks English, reply in English.
3. Provide a detailed, warm, and engaging answer (about 2 to 3 sentences). Elaborate on the facts to make it interesting for the parents.
4. Remember these facts:
   - Your name is Zayed. You are named in honor of the late Sheikh Zayed bin Sultan Al Nahyan, the founding father of the UAE.
   - The school hosting this exhibition is "مدرسة الظاهر للشراكات التعليمية" (Al Dhaher charter school).
   - The UAE 55th National Day is on December 2nd, 2026.
   - This exhibition showcases student projects in Artificial Intelligence.
   - You are built using Python and AI by a brilliant student from this school.
"""

# --- HELPER FUNCTIONS ---

def transcribe_audio_groq(audio_bytes):
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
        print(f"Groq transcription error: {e}")
        text = None
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    if text:
        lang = "ar" if any('\u0600' <= c <= '\u06FF' for c in text) else "en"
    else:
        lang = "en"
    return text, lang

def get_ai_response_stream(user_text):
    stream = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        model="openai/gpt-oss-20b",
        temperature=0.6,
        max_tokens=200,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

async def generate_tts(text, lang):
    if lang == "ar":
        voice = "ar-AE-HamdanNeural" 
    else:
        voice = "en-US-GuyNeural"    
    output_file = "response_audio.mp3"
    communicate = edge_tts.Communicate(text, voice, volume="+100%", rate="+15%")
    await communicate.save(output_file)
    return output_file

# --- MAIN APP LOGIC ---
st.write("---") 

st.markdown("<p class='arabic-text'>👇 اضغط على المايكروفون وتحدث مع زايد</p>", unsafe_allow_html=True)
st.markdown("<p class='english-text'>👇 Press the microphone and talk to Zayed</p>", unsafe_allow_html=True)

col_mic1, col_mic2, col_mic3 = st.columns([1, 1, 1])
with col_mic2:
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ff0000",
        neutral_color="#00732f",
        icon_name="microphone",
        icon_size="3x",
    )

# --- RESPONSE LOGIC ---
if audio_bytes:
    # إنشاء "حاويات فارغة" (Placeholders) للعناصر التي نريد مسحها لاحقاً
    listen_placeholder = st.empty()
    user_text_placeholder = st.empty()
    ai_text_placeholder = st.empty()
    audio_placeholder = st.empty()
    status_placeholder = st.empty()

    # 1. حالة الاستماع
    listen_placeholder.markdown("<div class='thinking-animation'>🎤 زايد يستمع إليك... / Zayed is listening...</div>", unsafe_allow_html=True)
    user_text, detected_lang = transcribe_audio_groq(audio_bytes)
    listen_placeholder.empty() 
    
    if user_text:
        # عرض ما قاله المستخدم في الحاوية المخصصة
        user_text_placeholder.success(f"**You said / قلت:** {user_text}")
        
        # 2. حالة التفكير
        status_placeholder.markdown("<div class='thinking-animation'>🧠 زايد يفكر... / Zayed is thinking...</div>", unsafe_allow_html=True)
        
        # بث النص داخل الحاوية المخصصة
        with ai_text_placeholder.container():
            response_text = st.write_stream(get_ai_response_stream(user_text))
            
        status_placeholder.empty() 
        
        # 3. حالة التحدث
        status_placeholder.markdown("<div class='thinking-animation'>🔊 زايد يتحدث... / Zayed is speaking...</div>", unsafe_allow_html=True)
        
        audio_file = asyncio.run(generate_tts(response_text, detected_lang))
        
        # حساب مدة الصوت
        audio_length = MP3(audio_file).info.length
        
        # عرض الصوت في الحاوية المخصصة
        with audio_placeholder.container():
            with open(audio_file, "rb") as f:
                st.audio(f.read(), format="audio/mp3", autoplay=True)
        
        os.remove(audio_file)
        status_placeholder.empty()
        
        # الانتظار حتى ينتهي الصوت (نضيف ثانية إضافية كهامش أمان)
        time.sleep(audio_length + 1)
        
        # --- مسح الشاشة بعد انتهاء التحدث ---
        user_text_placeholder.empty()
        ai_text_placeholder.empty()
        audio_placeholder.empty()
        # سيتم مسح الرسائل تلقائياً وسيعود التطبيق لحالته الأصلية
        st.rerun() # إعادة تشغيل التطبيق لمسح أي أثر متبقٍ

    else:
        st.error("Sorry, I couldn't understand. Please try again. / عذراً، لم أفهم. حاول مرة أخرى.")