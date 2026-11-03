import streamlit as st
import edge_tts
import asyncio
import os
from groq import Groq
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder

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
    
    /* تصميم الزر الدائري الكبير */
    div[data-testid="stAudioRecorder"] button {
        background-color: #00732f !important;
        color: white !important;
        width: 120px !important;
        height: 120px !important;
        border-radius: 50% !important;
        box-shadow: 0 0 20px rgba(0, 115, 47, 0.6) !important;
        border: 4px solid #ffffff !important;
        margin: 20px auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: transform 0.2s !important;
    }
    div[data-testid="stAudioRecorder"] button:hover {
        transform: scale(1.1) !important;
    }
    /* إخفاء النص والصندوق الأسود الافتراضي */
    div[data-testid="stAudioRecorder"] > div > div {
        display: none !important;
    }

    /* مربع كلام الروبوت */
    .robot-bubble {
        background-color: #e8f5e9;
        color: #1b5e20;
        padding: 15px 20px;
        border-radius: 15px;
        border-left: 5px solid #00732f;
        margin: 15px 0;
        font-size: 18px;
        direction: rtl;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
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
You are a friendly robot named "Zayed" (زايد) at a UAE 55th National Day school exhibition.
Answer briefly (2-3 sentences). Be warm and engaging.
Reply in the same language the user speaks (Arabic or English).
Facts: You are named after Sheikh Zayed. The school is "الظاهر للشراكات التعليمية". The exhibition shows AI student projects.
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

def get_ai_response(user_text):
    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        model="openai/gpt-oss-20b",
        temperature=0.6,
        max_tokens=150,
    )
    return completion.choices[0].message.content

async def generate_tts(text, lang):
    if lang == "ar":
        voice = "ar-AE-HamdanNeural" 
    else:
        voice = "en-US-GuyNeural"    
    output_file = "response_audio.mp3"
    
    # إعادة المحاولة حتى 3 مرات في حال فشل الخدمة
    max_retries = 3
    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(text, voice, volume="+100%", rate="+15%")
            await communicate.save(output_file)
            return output_file
        except edge_tts.exceptions.NoAudioReceived:
            if attempt < max_retries - 1:
                print(f"TTS attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(1.5)
            else:
                raise
        except Exception as e:
            raise e

# --- MAIN APP LOGIC ---
st.write("---") 

st.markdown("<p class='arabic-text'>👇  اضغط على المايكروفون وتحدث مع زايد</p>", unsafe_allow_html=True)
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
    with st.spinner("Listening... / جاري الاستماع..."):
        user_text, detected_lang = transcribe_audio_groq(audio_bytes)
    
    if user_text:
        st.success(f"**You said / قلت:** {user_text}")
        
        with st.spinner("Thinking... / جاري التفكير..."):
            ai_response = get_ai_response(user_text)
            
            # عرض كلام الروبوت في المربع الأخضر
            st.markdown(f"<div class='robot-bubble'>🤖 <b>زايد:</b> {ai_response}</div>", unsafe_allow_html=True)
        
        with st.spinner("Speaking... / جاري التحدث..."):
            try:
                audio_out_file = asyncio.run(generate_tts(ai_response, detected_lang))
                with open(audio_out_file, "rb") as f:
                    st.audio(f.read(), format="audio/mp3", autoplay=True)
                os.remove(audio_out_file)
            except Exception as e:
                st.warning("عذراً، حدث تأخير في الصوت. / Sorry, audio generation failed. Please try again.")
    else:
        st.error("Sorry, I couldn't understand. Please try again. / عذراً، لم أفهم. حاول مرة أخرى.")