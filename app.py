import streamlit as st
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder
import edge_tts
import asyncio
import os
from groq import Groq
from dotenv import load_dotenv

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
    .stApp { background-color: #f8f9fa; }
    .uae-border {
        height: 10px;
        background: linear-gradient(to right, #00732f 33%, #ffffff 33%, #ffffff 66%, #000000 66%);
        border-top: 5px solid #ff0000;
        margin-bottom: 20px;
        border-radius: 5px;
    }
    h1 { color: #00732f; text-align: center; font-family: 'Tahoma', sans-serif; font-weight: bold; direction: rtl; margin-bottom: 0; font-size: 2.5rem;}
    h3 { text-align: center; color: #333; margin-top: 5px; margin-bottom: 20px;}
    
    /* تنسيق حاوية الفيديو/الصورة */
    .robot-media-container {
        display: flex;
        justify-content: center;
        align-items: center;
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }

    .arabic-text { text-align: center; font-size: 20px; color: #333; direction: rtl; font-family: 'Tahoma', sans-serif; margin-bottom: 5px; font-weight: bold;}
    .english-text { text-align: center; font-size: 16px; color: #666; margin-bottom: 15px; }
    header {visibility: hidden;} footer {visibility: hidden;} #MainMenu {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='uae-border'></div>", unsafe_allow_html=True)

# --- MAIN LAYOUT ---
col_robot, col_ui = st.columns([1, 1.2])

# --- LEFT COLUMN: Robot Video/Image ---
with col_robot:
    robot_col1, robot_col2, robot_col3 = st.columns([0.1, 2, 0.1])
    with robot_col2:
        st.markdown("<div class='robot-media-container'>", unsafe_allow_html=True)
        # محاولة عرض الفيديو أولاً
        if os.path.exists("robot_video.mp4"):
            # autoplay=True (يشتغل تلقائياً), loop=True (يعيد), muted=True (صامت لتجنب مشاكل المتصفح)
            st.video("robot_video.mp4", autoplay=True, loop=True, muted=True)
        elif os.path.exists("robot.png"):
            # إذا لم يوجد فيديو، اعرض الصورة
            st.image("robot.png", use_container_width=True)
        else:
            st.warning("⚠️ لم يتم العثور على صورة أو فيديو الروبوت.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- RIGHT COLUMN: The UI ---
with col_ui:
    st.markdown("<h1>🤖 زايد - صديق اليوم الوطني 55</h1>", unsafe_allow_html=True)
    st.markdown("<h3>Zayed - National Day 55 Buddy</h3>", unsafe_allow_html=True)
    
    # QR Code
    qr_col1, qr_col2, qr_col3 = st.columns([1, 1, 1])
    with qr_col2:
        try:
            st.image("qr_code.png", width=130)
            st.markdown("<p style='text-align:center; font-size:12px; color:#00732f; margin-top:-10px;'>Scan to try 📱</p>", unsafe_allow_html=True)
        except Exception:
            st.warning("QR Code image not found.")

    st.markdown("<p class='arabic-text'>👇 اضغط على المايكروفون وتحدث مع زايد</p>", unsafe_allow_html=True)
    st.markdown("<p class='english-text'>👇 Press the microphone and talk to Zayed</p>", unsafe_allow_html=True)

    mic_col1, mic_col2, mic_col3 = st.columns([1, 1, 1])
    with mic_col2:
        audio_bytes = audio_recorder(
            text="", 
            recording_color="#ff0000",
            neutral_color="#00732f",
            icon_name="microphone",
            icon_size="4x", 
        )

    # --- INITIALIZE GROQ ---
    if not GROQ_API_KEY:
        st.error("API Key not found.")
        st.stop()
        
    client = Groq(api_key=GROQ_API_KEY)

    SYSTEM_PROMPT = """
    You are a friendly, intelligent robot named "Zayed" (زايد). You are at a school exhibition for the UAE 55th National Day.
    Your job is to answer parents' questions.
    You MUST follow these rules strictly:
    1. If the user speaks Arabic, reply in Arabic.
    2. If the user speaks English, reply in English.
    3. Provide a detailed, warm, and engaging answer (about 3 to 4 sentences).
    4. Remember these facts:
       - Your name is Zayed. You are named in honor of the late Sheikh Zayed bin Sultan Al Nahyan.
       - The school hosting this exhibition is "مدرسة الظاهر للشراكات التعليمية " (Al Dhahir charter school).
       - The UAE 55th National Day is on December 2nd, 2026.
       - The UAE National Day is a celebration of unity and solidarity among the SEVEN Emirates (الإمارات السبعة). (Never say six).
       - This exhibition showcases student projects in Artificial Intelligence.
    """

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
            voice = "ar-AE-HamdanNeural" 
        else:
            voice = "en-US-GuyNeural"    
        output_file = "response_audio.mp3"
        communicate = edge_tts.Communicate(text, voice, volume="+100%", rate="+10%")
        await communicate.save(output_file)
        return output_file

    if audio_bytes:
        st.info("Processing... / جاري المعالجة...")
        user_text, detected_lang = transcribe_audio(audio_bytes)
        
        if user_text:
            st.success(f"**You said / قلت:** {user_text}")
            
            user_text_lower = user_text.lower()
            wake_words = ["zayed", "زايد", "زايداً", "زايدا"]
            
            if any(word in user_text_lower for word in wake_words):
                
                prompt_for_ai = user_text
                for word in wake_words:
                    prompt_for_ai = prompt_for_ai.replace(word, "").replace(word.capitalize(), "").strip()
                    
                if not prompt_for_ai:
                    ai_response = "نعم؟ كيف يمكنني مساعدتك اليوم؟" if detected_lang == "ar" else "Yes? How can I help you today?"
                    st.info(f"**🤖 Zayed:** {ai_response}")
                    with st.spinner("Speaking..."):
                        audio_file = asyncio.run(generate_tts(ai_response, detected_lang))
                        with open(audio_file, "rb") as f:
                            st.audio(f.read(), format="audio/mp3", autoplay=True)
                        os.remove(audio_file)
                else:
                    with st.spinner("Thinking... / جاري التفكير..."):
                        ai_response = get_ai_response(prompt_for_ai)
                        st.info(f"**🤖 Zayed:** {ai_response}")
                        
                    with st.spinner("Speaking... / جاري التحدث..."):
                        audio_file = asyncio.run(generate_tts(ai_response, detected_lang))
                        with open(audio_file, "rb") as f:
                            st.audio(f.read(), format="audio/mp3", autoplay=True)
                        os.remove(audio_file)
            else:
                st.warning("I am sleeping. You must call my name first! / أنا نائم. يجب أن تنادي باسمي أولاً! (قل: زايد)")
        else:
            st.error("Sorry, I couldn't understand. Please try again.")