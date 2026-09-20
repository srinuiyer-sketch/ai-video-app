import streamlit as st
from google import genai
from pptx import Presentation
import PyPDF2
from docx import Document
import io
import time
import asyncio
import edge_tts
import tempfile
import os
import re
import requests

# --- PIL COMPATIBILITY PATCH FOR MOVIEPY ---
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips

# Page configuration
st.set_page_config(
    page_title="AI Content & Video Engine", 
    page_icon="🚀", 
    layout="centered"
)

st.title("🚀 AI Multi-Format Content & Video Engine")
st.markdown("Generate human-grade scripts, clean voiceovers, and dynamic MP4 videos with context-matching visuals.")

# Automatically fetch API key from Streamlit Cloud Secrets securely
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    api_key = None

# Sidebar Configuration
st.sidebar.header("Localization & Audio")
target_language = st.sidebar.selectbox(
    "Output Language",
    ["English", "Hindi (हिन्दी)", "Spanish (Español)", "French (Français)", "German (Deutsch)", "Japanese (日本語)", "Arabic (العربية)"]
)

# Custom Voice Selector
voice_options = {
    "English (US - Female: Aria)": "en-US-AriaNeural",
    "English (US - Male: Andrew)": "en-US-AndrewNeural",
    "English (UK - Female: Sonia)": "en-GB-SoniaNeural",
    "English (UK - Male: Ryan)": "en-GB-RyanNeural",
    "Hindi (India - Female: Swara)": "hi-IN-SwaraNeural",
    "Hindi (India - Male: Madhur)": "hi-IN-MadhurNeural",
    "Spanish (Spain - Female: Elvira)": "es-ES-ElviraNeural",
    "French (France - Female: Denise)": "fr-FR-DeniseNeural",
    "German (Germany - Female: Katja)": "de-DE-KatjaNeural",
    "Japanese (Japan - Female: Nanami)": "ja-JP-NanamiNeural",
    "Arabic (Egypt - Female: Salma)": "ar-EG-SalmaNeural",
    "✨ Custom Voice ID (Type Below)": "custom"
}

selected_voice_label = st.sidebar.selectbox("Select Voice Profile", list(voice_options.keys()))

if selected_voice_label == "✨ Custom Voice ID (Type Below)":
    selected_voice_id = st.sidebar.text_input("Enter exact edge-tts Voice ID", value="en-US-ChristopherNeural")
else:
    selected_voice_id = voice_options[selected_voice_label]

# Main user inputs
uploaded_file = st.file_uploader(
    "Upload your source file (TXT, PDF, DOCX, PPTX, MD)", 
    type=["txt", "pdf", "docx", "pptx", "md"]
)
user_prompt = st.text_area("Or type/paste your topic or raw notes here:")

# Helper to clean text for TTS
def clean_script_for_tts(raw_text):
    cleaned = re.sub(r'\[VISUAL:.*?\]', '', raw_text, flags=re.IGNORECASE)
    cleaned = re.sub(r'Visual:.*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Narration:.*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'#+', '', cleaned)
    cleaned = re.sub(r'\*\*', '', cleaned)
    cleaned = re.sub(r'\*', '', cleaned)
    cleaned = re.sub(r'\[.*?\]', '', cleaned)
    cleaned = re.sub(r'\d{2}:\d{2}', '', cleaned)
    cleaned = "\n".join([line.strip() for line in cleaned.splitlines() if line.strip() and not line.startswith("Visual")])
    return cleaned

def parse_script_scenes(raw_text):
    scenes = []
    lines = raw_text.split('\n')
    current_visual = "business technology concept"
    current_narration = []
    
    for line in lines:
        if "visual:" in line.lower() or "[visual:" in line.lower():
            if current_narration:
                scenes.append({"visual": current_visual, "text": " ".join(current_narration)})
                current_narration = []
            current_visual = re.sub(r'\[?visual:?\]?', '', line, flags=re.IGNORECASE).strip()
        elif line.strip() and not line.startswith("#") and not "narration:" in line.lower():
            current_narration.append(line.strip())
            
    if current_narration:
        scenes.append({"visual": current_visual, "text": " ".join(current_narration)})
        
    if not scenes:
        scenes = [{"visual": "corporate technology", "text": raw_text}]
    return scenes

def fetch_context_image(visual_cue, output_path):
    clean_query = re.sub(r'[^a-zA-Z0-9\s]', '', visual_cue).strip()
    words = [w for w in clean_query.split() if len(w) > 3]
    search_term = "+".join(words[:3]) if words else "business"
    
    try:
        seed_val = abs(hash(search_term)) % 900 + 100
        img_url = f"https://picsum.photos/seed/{seed_val}/1080/1920"
        response = requests.get(img_url, timeout=5)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return True
    except Exception:
        pass
    
    try:
        res = requests.get("https://picsum.photos/1080/1920", timeout=5)
        with open(output_path, "wb") as f:
            f.write(res.content)
        return True
    except Exception:
        return False

async def generate_tts_audio(text_content, voice_name, output_filename):
    communicate = edge_tts.Communicate(text_content, voice_name)
    await communicate.save(output_filename)

if st.button("Generate Content Pipeline", type="primary"):
    if not api_key:
        st.error("API key not found in Streamlit Secrets! Please verify your settings.")
    elif not uploaded_file and not user_prompt:
        st.warning("Please upload a file or enter some text to begin.")
    else:
        with st.spinner(f"AI is analyzing your file and crafting a human-like script in {target_language}..."):
            try:
                client = genai.Client(api_key=api_key)
                
                content_text = ""
                if uploaded_file is not None:
                    file_extension = uploaded_file.name.split(".")[-1].lower()
                    if file_extension in ["txt", "md"]:
                        content_text = uploaded_file.read().decode("utf-8", errors="ignore")
                    elif file_extension == "pdf":
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                        pdf_texts = [page.extract_text() for page in pdf_reader.pages if page.extract_text()]
                        content_text = "\n".join(pdf_texts)
                    elif file_extension == "docx":
                        doc = Document(io.BytesIO(uploaded_file.read()))
                        content_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                    elif file_extension == "pptx":
                        prs = Presentation(io.BytesIO(uploaded_file.read()))
                        slide_texts = []
                        for slide_num, slide in enumerate(prs.slides, start=1):
                            slide_content = f"--- Slide {slide_num} ---\n"
                            for shape in slide.shapes:
                                if shape.has_text_frame:
                                    for paragraph in shape.text_frame.paragraphs:
                                        slide_content += paragraph.text + "\n"
                            slide_texts.append(slide_content)
                        content_text = "\n".join(slide_texts)
                else:
                    content_text = user_prompt

                prompt = f"""
                You are an elite, top 1% human content creator and documentary filmmaker. Transform the source content into a structured video script.

                CRITICAL FORMATTING REQUIREMENT:
                For every paragraph or section, explicitly provide a visual direction line starting with `Visual:` followed by the exact scene description, then the spoken script starting with `Narration:`.
                
                Example format:
                Visual: Close-up of glowing laptop screen in a dark room at night
                Narration: Here is the brutal truth about building a tech startup...

                CRITICAL ANTI-AI WRITING RULES:
                1. NEVER use cliché AI filler words such as: "delve", "tapestry", "testament", "beacon", "game-changer", "in conclusion".
                2. Write like a real human speaks to an audience on camera with natural speech cadences and contractions.
                
                LANGUAGE REQUIREMENT: Written fluently in **{target_language}**.
                
                Source Content:
                {content_text}
                """
                
                response = None
                models_to_try = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
                for model_name in models_to_try:
                    try:
                        response = client.models.generate_content(model=model_name, contents=prompt)
                        if response and response.text:
                            break
                    except Exception:
                        continue
                
                if response and response.text:
                    st.success(f"Content Generated Successfully in {target_language}!")
                    st.markdown("### 📝 Results Output")
                    st.write(response.text)
                    st.session_state["generated_script"] = response.text
                else:
                    st.error("Server traffic is high. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Audio & Video Generation Section
if "generated_script" in st.session_state and st.session_state["generated_script"]:
    st.markdown("---")
    st.subheader("🎬 AI Dynamic Video Studio")
    st.markdown(f"Render a professional MP4 video featuring scene visuals matching your script instructions.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Generate Clean Voiceover MP3"):
            with st.spinner("Synthesizing audio..."):
                try:
                    speech_text = clean_script_for_tts(st.session_state["generated_script"])
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                        tmp_audio_path = tmp_file.name
                    asyncio.run(generate_tts_audio(speech_text, selected_voice_id, tmp_audio_path))
                    with open(tmp_audio_path, "rb") as f:
                        audio_bytes = f.read()
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button("📥 Download MP3", data=audio_bytes, file_name="voiceover.mp3", mime="audio/mp3")
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        if st.button("Render Dynamic MP4 Video"):
            with st.spinner("Assembling multi-scene video with script-matching visuals..."):
                try:
                    raw_script = st.session_state["generated_script"]
                    speech_text = clean_script_for_tts(raw_script)
                    scenes = parse_script_scenes(raw_script)
                    
                    # Safely create audio file and ensure handle is closed before loading into MoviePy
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
                        tmp_audio_path = tmp_audio.name
                    
                    asyncio.run(generate_tts_audio(speech_text, selected_voice_id, tmp_audio_path))
                    time.sleep(0.5) # Buffer for file system sync
                    
                    audio_clip = AudioFileClip(tmp_audio_path)
                    total_duration = audio_clip.duration
                    
                    scene_duration = max(3.0, total_duration / len(scenes))
                    
                    image_clips = []
                    for scene in scenes:
                        img_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
                        fetch_context_image(scene["visual"], img_path)
                        img_clip = ImageClip(img_path).set_duration(scene_duration).resize(height=1920)
                        image_clips.append(img_clip)
                    
                    final_visual = concatenate_videoclips(image_clips, method="compose")
                    
                    if final_visual.duration > total_duration:
                        final_visual = final_visual.subclip(0, total_duration)
                    
                    video_clip = final_visual.set_audio(audio_clip)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
                        tmp_video_path = tmp_video.name
                    
                    video_clip.write_videofile(
                        tmp_video_path,
                        fps=24,
                        codec="libx264",
                        audio_codec="aac",
                        preset="ultrafast",
                        logger=None
                    )
                    
                    with open(tmp_video_path, "rb") as vid_file:
                        video_bytes = vid_file.read()
                    
                    st.video(video_bytes)
                    st.download_button(
                        label="📥 Download Dynamic MP4",
                        data=video_bytes,
                        file_name="dynamic_viral_video.mp4",
                        mime="video/mp4"
                    )
                    st.success("Dynamic multi-scene video rendered successfully!")
                    
                    audio_clip.close()
                    video_clip.close()
                    
                except Exception as vid_error:
                    st.error(f"Error rendering video: {vid_error}")
