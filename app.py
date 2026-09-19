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
st.markdown("Upload any document (TXT, PDF, Word, PPTX, MD) or notes to instantly generate YouTube scripts and LinkedIn posts.")

# Sidebar for API configuration
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your Google AI Studio API Key", type="password")

# Main user inputs - expanded file support
uploaded_file = st.file_uploader(
    "Upload your source file (TXT, PDF, DOCX, PPTX, MD)", 
    type=["txt", "pdf", "docx", "pptx", "md"]
)
user_prompt = st.text_area("Or type/paste your topic or raw notes here:")

if st.button("Generate Content Pipeline", type="primary"):
    if not api_key:
        st.error("Please enter your Google AI Studio API key in the sidebar.")
    elif not uploaded_file and not user_prompt:
        st.warning("Please upload a file or enter some text to begin.")
    else:
        with st.spinner("AI is analyzing your file and writing cross-platform content..."):
            try:
                client = genai.Client(api_key=api_key)
                
                content_text = ""
                if uploaded_file is not None:
                    file_extension = uploaded_file.name.split(".")[-1].lower()
                    
                    # 1. Text & Markdown files
                    if file_extension in ["txt", "md"]:
                        content_text = uploaded_file.read().decode("utf-8", errors="ignore")
                    
                    # 2. PDF files
                    elif file_extension == "pdf":
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                        pdf_texts = []
                        for page_num, page in enumerate(pdf_reader.pages, start=1):
                            text = page.extract_text()
                            if text:
                                pdf_texts.append(f"--- Page {page_num} ---\n{text}")
                        content_text = "\n".join(pdf_texts)
                    
                    # 3. Word documents (.docx)
                    elif file_extension == "docx":
                        doc = Document(io.BytesIO(uploaded_file.read()))
                        doc_texts = [para.text for para in doc.paragraphs if para.text.strip()]
                        content_text = "\n".join(doc_texts)
                    
                    # 4. PowerPoint presentations (.pptx)
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
                Analyze the following content from the uploaded file and generate:
                1. A viral LinkedIn post with a strong hook and relevant hashtags.
                2. A long-form YouTube script divided clearly into visual cues and voiceover narration.
                3. A punchy 30-second YouTube Short script.
                
                Content to process:
                {content_text}
                """
                
                response = client.models.generate_content(
                   model="gemini-3.5-flash",
                    contents=prompt,
                )
                
                st.success("Content Generated Successfully!")
                st.markdown("### 📝 Results Output")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"An error occurred while processing your file: {e}")
