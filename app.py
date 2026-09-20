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

# Page configuration
st.set_page_config(
    page_title="AI Content & Video Engine", 
    page_icon="🚀", 
    layout="centered"
)

st.title("🚀 AI Multi-Format Content & Video Engine")
st.markdown("Upload any document or notes to generate human-grade video scripts, posts, and downloadable audio voiceovers.")

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

# Custom Voice Selector with a Custom Input Option
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

# Helper function to run edge-tts asynchronously in Streamlit
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
                        pdf_texts = []
                        for page_num, page in enumerate(pdf_reader.pages, start=1):
                            text = page.extract_text()
                            if text:
                                pdf_texts.append(f"--- Page {page_num} ---\n{text}")
                        content_text = "\n".join(pdf_texts)
                    elif file_extension == "docx":
                        doc = Document(io.BytesIO(uploaded_file.read()))
                        doc_texts = [para.text for para in doc.paragraphs if para.text.strip()]
                        content_text = "\n".join(doc_texts)
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
                You are an elite, top 1% human content creator, documentary filmmaker, and expert copywriter. Your job is to transform the provided source content into an ultra-engaging, completely human-sounding script and post.

                CRITICAL ANTI-AI WRITING RULES:
                1. NEVER use cliché AI filler words such as: "delve", "tapestry", "testament", "beacon", "game-changer", "in conclusion", "dive deep", "revolutionize", "unleash", or "it's important to note".
                2. Write like a real human speaks to a friend or an audience on camera. Use natural speech cadences, contractions (don't, won't, it's, you're), rhetorical questions, and occasional conversational transitions ("Look,", "Here's the thing,", "Now,").
                3. The voiceover narration must sound spoken, not written. Avoid overly complex academic sentences; keep the rhythm punchy, variable, and engaging for text-to-speech audio generation.
                
                LANGUAGE REQUIREMENT: The entire output must be written fluently in **{target_language}**.

                Generate:
                1. A viral LinkedIn post with a sharp, thumb-stopping hook, crisp spacing, zero corporate jargon, and relevant hashtags.
                2. A long-form YouTube script divided into clear visual cues and voiceover narration formatted specifically for clean audio flow.
                3. A punchy 30-second YouTube Short / Reel script with immediate pattern-interrupt pacing.
                
                Source Content to process:
                {content_text}
                """
                
                # Use gemini-2.0-flash as the primary production-stable model
                response = None
                models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
                
                for model_name in models_to_try:
                    success = False
                    for attempt in range(2):
                        try:
                            response = client.models.generate_content(
                                model=model_name,
                                contents=prompt,
                            )
                            if response and response.text:
                                success = True
                                break
                        except Exception:
                            time.sleep(1.5)
                    if success:
                        break
                
                if response and response.text:
                    st.success(f"Human-Grade Content Generated Successfully in {target_language}!")
                    st.markdown("### 📝 Results Output")
                    st.write(response.text)
                    
                    # Save generated text into session state for audio generation
                    st.session_state["generated_script"] = response.text
                else:
                    st.error("Server traffic is currently high on Google's free tier. Please try again in a few seconds.")
                
            except Exception as e:
                st.error(f"An error occurred while processing your file: {e}")

# If content has been generated, provide an audio generation section
if "generated_script" in st.session_state and st.session_state["generated_script"]:
    st.markdown("---")
    st.subheader("🎙️ Voiceover Audio Generator")
    st.markdown(f"Convert your script narration into a realistic MP3 voiceover using voice ID: `{selected_voice_id}`.")
    
    if st.button("Generate & Download Voiceover MP3"):
        with st.spinner("Synthesizing lifelike speech audio..."):
            try:
                # Create a temporary file to store the audio
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    tmp_path = tmp_file.name
                
                # Run edge-tts to generate the audio file
                asyncio.run(generate_tts_audio(st.session_state["generated_script"], selected_voice_id, tmp_path))
                
                # Read audio bytes for player and download button
                with open(tmp_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button(
                    label="📥 Download Voiceover (.mp3)",
                    data=audio_bytes,
                    file_name="ai_voiceover.mp3",
                    mime="audio/mp3"
                )
                st.success("Voiceover generated successfully!")
            except Exception as tts_error:
                st.error(f"Error generating audio: {tts_error}")
