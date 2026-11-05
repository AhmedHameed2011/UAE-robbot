import streamlit as st
import edge_tts
import asyncio
import os
import time
from groq import Groq
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder
from mutagen.mp3 import MP3

# Load local .env file
load_dotenv()

# --- API KEY SETUP ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API"]
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API")

# --- UI SETUP ---
st.set_page_config(page_title="Zayed Robot", page_icon="🇦🇪🤖", layout="centered")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .stApp { background-color: #ffffff; }
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.2rem !important; 
        padding-bottom: 0rem !important;
    }
    div[data-testid="stImage"] {
        margin-bottom: -15px !important; 
        padding-bottom: 0px !important;
        line-height: 0 !important;
    }
    h1 { color: #00732f !important; text-align: center; font-family: 'Arial', sans-serif; font-weight: bold; margin-top: 5px !important; margin-bottom: 0px !important; font-size: 22px !important;}
    h2 { text-align: center; color: #333 !important; margin-bottom: 15px !important; margin-top: 0px !important; font-size: 16px !important;}
    .arabic-text { text-align: center; font-size: 18px; color: #333; direction: rtl; font-family: 'Tahoma', sans-serif; margin-bottom: 0px; margin-top: 10px; font-weight: bold;}
    .english-text { text-align: center; font-size: 14px; color: #666; margin-bottom: 5px; }
    
    div[data-testid="stAudioRecorder"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stAudioRecorder"] > div {
        background-color: transparent !important;
    }
    div[data-testid="stAudioRecorder"] button {
        transform: scale(1.8) !important;
        margin: 0px auto !important;
        display: block !important;
        box-shadow: 0 0 15px rgba(0, 115, 47, 0.4) !important;
        border: 2px solid #00732f !important;
        background-color: #ffffff !important; 
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

# --- RENDER UI ---
try:
    st.image("intro.gif", use_container_width=True)
except Exception:
    st.warning("⚠️ لم يتم العثور على صورة الغلاف 'intro.gif'.")

st.markdown("<h1>🤖 زايد - صديق اليوم الوطني 55</h1>", unsafe_allow_html=True)
st.markdown("<h2>Zayed - National Day 55 Buddy</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 16px; font-weight: bold; color: #00732f; margin-bottom: 5px; margin-top: 10px;'>📱 Scan to try on your phone</p>", unsafe_allow_html=True)

col_qr1, col_qr2, col_qr3 = st.columns([1, 1, 1])
with col_qr2:
    try:
        st.image("qr_code.png", use_container_width=True)
    except Exception:
        st.warning("QR Code image not found.")

st.markdown("<p class='arabic-text'>👇 تحدث مع زايد</p>", unsafe_allow_html=True)
st.markdown("<p class='english-text'>👇 Talk to Zayed</p>", unsafe_allow_html=True)

col_mic1, col_mic2, col_mic3 = st.columns([1, 1, 1])
with col_mic2:
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ff0000",
        neutral_color="#00732f",
        icon_name="microphone",
        icon_size="2x",
        key="mic_center"
    )

# --- INITIALIZE GROQ ---
if not GROQ_API_KEY:
    st.error("API Key not found.")
    st.stop()
    
client = Groq(api_key=GROQ_API_KEY)

# --- ROBOT'S PERSONALITY (With Sheikh Zayed's Info) ---
SYSTEM_PROMPT = """
You are "Zayed" (زايد), a very friendly and welcoming robot at a UAE 55th National Day school exhibition. 
When you introduce yourself, you should say something like: "أنا زايد، روبوت الذكاء الاصطناعي" (I am Zayed, the AI robot).
Your job is to answer parents' questions.
You MUST follow these rules strictly:
1. If the user speaks Arabic, reply in Arabic.
2. If the user speaks English, reply in English.
3. Provide a comprehensive, rich, and complete answer. Do not cut your answer short. Explain the topic fully and enthusiastically so the parents get a complete picture (up to 6-7 sentences if needed).
4. If the user asks about Sheikh Zayed, his life, or his legacy, you MUST give a highly detailed, accurate, and respectful answer using the following information:
   - Sheikh Zayed bin Sultan Al Nahyan (6 May 1918 – 2 November 2004) is the founding father and the first President of the United Arab Emirates.
   - He was born in Abu Dhabi in 1918, the youngest of four brothers. He grew up in Al Ain, memorizing the Holy Quran and learning Bedouin traditions, falconry, and wisdom.
   - In 1946, he became the Ruler's Representative in Al Ain, where he developed the oasis, repaired the falaj irrigation systems, and built the first school and hospital there.
   - In 1966, he became the Ruler of Abu Dhabi and started a comprehensive modernization process, investing oil revenues in infrastructure.
   - In 1971, he led the efforts (alongside his brother Sheikh Rashid bin Saeed Al Maktoum) to unite the Trucial States, announcing the establishment of the UAE on December 2nd, 1971. He was elected as the first President and re-elected multiple times until his death.
   - He transformed the UAE from a simple society relying on pearl diving and fishing into a modern state with high living standards. He co-founded the Gulf Cooperation Council (GCC) in 1981.
   - He was famous for his extensive charitable initiatives worldwide, his passion for agriculture, desert afforestation, and environmental protection.
   - He passed away on November 2, 2004, at the age of 86, leaving behind a profound national and humanitarian legacy.
5. Remember these facts about the exhibition:
   - Your name is Zayed, named in his honor.
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
        temperature=0.7,
        max_tokens=1000, 
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

# --- RESPONSE LOGIC (FIXED LOOP) ---
if audio_bytes:
    # 1. إنشاء حاويات مؤقتة
    listen_placeholder = st.empty()
    user_text_placeholder = st.empty()
    ai_text_placeholder = st.empty()
    audio_placeholder = st.empty()
    status_placeholder = st.empty()

    # 2. حالة الاستماع
    listen_placeholder.markdown("<div class='thinking-animation'>🎤 زايد يستمع... / Zayed is listening...</div>", unsafe_allow_html=True)
    user_text, detected_lang = transcribe_audio_groq(audio_bytes)
    listen_placeholder.empty() 
    
    if user_text:
        user_text_placeholder.success(f"**You said / قلت:** {user_text}")
        
        # 3. حالة التفكير
        status_placeholder.markdown("<div class='thinking-animation'>🧠 زايد يفكر... / Zayed is thinking...</div>", unsafe_allow_html=True)
        with ai_text_placeholder.container():
            response_text = st.write_stream(get_ai_response_stream(user_text))
        status_placeholder.empty() 
        
        # 4. حالة التحدث
        status_placeholder.markdown("<div class='thinking-animation'>🔊 زايد يتحدث... / Zayed is speaking...</div>", unsafe_allow_html=True)
        audio_file = asyncio.run(generate_tts(response_text, detected_lang))
        
        try:
            audio_length = MP3(audio_file).info.length
        except Exception:
            audio_length = 5 
            
        with audio_placeholder.container():
            with open(audio_file, "rb") as f:
                st.audio(f.read(), format="audio/mp3", autoplay=True)
        
        os.remove(audio_file)
        status_placeholder.empty()
        
        # 5. الانتظار حتى ينتهي الصوت
        time.sleep(audio_length + 3.5) 
        
        # 6. تنظيف الشاشة بصرياً (بدون إعادة تشغيل الصفحة)
        user_text_placeholder.empty()
        ai_text_placeholder.empty()
        audio_placeholder.empty()
        status_placeholder.empty()
        
        # 7. الحل النهائي لمنع التكرار: مسح الصوت من الذاكرة
        # (هذا يمنع التطبيق من معالجة نفس الصوت مرة أخرى في الدورة التالية)
        if "mic_center" in st.session_state:
            del st.session_state["mic_center"]
        
        # ملاحظة: لم نستخدم st.rerun() هنا لتجنب الحلقة المفرغة.
        # الشاشة الآن نظيفة، وزر المايكروفون جاهز للضغط عليه من جديد.

    else:
        listen_placeholder.empty()
        st.error("عذراً، لم أفهم كلامك. يرجى المحاولة مرة أخرى.\n\nSorry, I couldn't understand. Please try again.")
        time.sleep(3) 
        
        # مسح الصوت من الذاكرة
        if "mic_center" in st.session_state:
            del st.session_state["mic_center"]
        
        # إعادة تشغيل الصفحة هنا آمنة لأننا مسحنا الصوت
        st.rerun()