import streamlit as st
from google import genai
from pptx import Presentation
import PyPDF2
from docx import Document
import io

# Page configuration
st.set_page_config(
    page_title="AI Content & Video Engine", 
    page_icon="🚀", 
    layout="centered"
)

st.title("🚀 AI Multi-Format Content & Video Engine")
st.markdown("Upload any document or notes to generate ultra-realistic, human-sounding video scripts and posts.")

# Automatically fetch API key from Streamlit Cloud Secrets securely
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    api_key = None

# Sidebar for Localization (Language Selection Only)
st.sidebar.header("Localization")
target_language = st.sidebar.selectbox(
    "Output Language",
    ["English", "Hindi (हिन्दी)", "Spanish (Español)", "French (Français)", "German (Deutsch)", "Japanese (日本語)", "Arabic (العربية)"]
)

# Main user inputs
uploaded_file = st.file_uploader(
    "Upload your source file (TXT, PDF, DOCX, PPTX, MD)", 
    type=["txt", "pdf", "docx", "pptx", "md"]
)
user_prompt = st.text_area("Or type/paste your topic or raw notes here:")

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
                
                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt,
                )
                
                st.success(f"Human-Grade Content Generated Successfully in {target_language}!")
                st.markdown("### 📝 Results Output")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"An error occurred while processing your file: {e}")
