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
    
    /* زر المايكروفون الكبير */
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
You are a friendly robot named "Zayed" (زايد) at a UAE 55th National Day school exhibition.
Answer in just 1 or 2 short sentences. Be very brief and warm.
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

def get_ai_response_stream(user_text):
    stream = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        model="openai/gpt-oss-20b",
        temperature=0.7,
        max_tokens=80, # تقليل العدد لجعل الرد أسرع
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

# --- LOGIC ---
if audio_bytes:
    listen_placeholder = st.empty()
    listen_placeholder.markdown("<div class='thinking-animation'>🎤 زايد يستمع إليك...</div>", unsafe_allow_html=True)
    
    user_text, detected_lang = transcribe_audio_groq(audio_bytes)
    listen_placeholder.empty() 
    
    if user_text:
        st.success(f"**You said / قلت:** {user_text}")
        
        # تنظيف النص من كلمة "زايد" إذا قالها المستخدم
        user_text_lower = user_text.lower()
        wake_words = ["zayed", "زايد", "زايداً", "زايدا"]
        prompt_for_ai = user_text
        for word in wake_words:
            prompt_for_ai = prompt_for_ai.replace(word, "").replace(word.capitalize(), "").strip()
            
        # إذا كان المستخدم قال "زايد" فقط دون سؤال
        if not prompt_for_ai:
            ai_response = "نعم؟ كيف يمكنني مساعدتك اليوم؟" if detected_lang == "ar" else "Yes? How can I help you today?"
            st.info(f"**🤖 Zayed:** {ai_response}")
            speak_placeholder = st.empty()
            speak_placeholder.markdown("<div class='thinking-animation'>🔊 زايد يتحدث...</div>", unsafe_allow_html=True)
            audio_out_file = asyncio.run(generate_tts(ai_response, detected_lang))
            with open(audio_out_file, "rb") as f:
                st.audio(f.read(), format="audio/mp3", autoplay=True)
            os.remove(audio_out_file)
            speak_placeholder.empty()
            
        else:
            # الرد على أي سؤال مباشرة (بدون اشتراط كلمة زايد)
            think_placeholder = st.empty()
            think_placeholder.markdown("<div class='thinking-animation'>🧠 زايد يفكر...</div>", unsafe_allow_html=True)
            
            try:
                response_text = st.write_stream(get_ai_response_stream(prompt_for_ai))
            except Exception as e:
                response_text = "عذراً، حدث خطأ في الاتصال. / Sorry, a connection error occurred."
                st.error(response_text)
            finally:
                think_placeholder.empty()
            
            if response_text and "عذراً" not in response_text:
                speak_placeholder = st.empty()
                speak_placeholder.markdown("<div class='thinking-animation'>🔊 زايد يتحدث...</div>", unsafe_allow_html=True)
                
                audio_out_file = asyncio.run(generate_tts(response_text, detected_lang))
                with open(audio_out_file, "rb") as f:
                    st.audio(f.read(), format="audio/mp3", autoplay=True)
                os.remove(audio_out_file)
                speak_placeholder.empty()
    else:
        st.error("Sorry, I couldn't understand. Please try again. / عذراً، لم أفهم. حاول مرة أخرى.")