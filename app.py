import streamlit as st
from google import genai

# Page configuration
st.set_page_config(
    page_title="AI Content & Video Engine", 
    page_icon="🚀", 
    layout="centered"
)

st.title("🚀 AI Multi-Format Content & Video Engine")
st.markdown("Upload any document, notes, or topic to instantly generate YouTube scripts, LinkedIn posts, and more using your Gemini subscription key.")

# Sidebar for API configuration
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your Google AI Studio API Key", type="password")

# Main user inputs
uploaded_file = st.file_uploader("Upload your source file (TXT or PDF)", type=["txt", "pdf"])
user_prompt = st.text_area("Or type/paste your topic or raw notes here:")

if st.button("Generate Content Pipeline", type="primary"):
    if not api_key:
        st.error("Please enter your Google AI Studio API key in the sidebar.")
    elif not uploaded_file and not user_prompt:
        st.warning("Please upload a file or enter some text to begin.")
    else:
        with st.spinner("AI is analyzing your input and writing cross-platform content..."):
            try:
                # Initialize Gemini client with the new SDK structure
                client = genai.Client(api_key=api_key)
                
                content_text = ""
                if uploaded_file is not None:
                    content_text = uploaded_file.read().decode("utf-8", errors="ignore")
                else:
                    content_text = user_prompt

                # Constructing the structured prompt for Gemini
                prompt = f"""
                Analyze the following content and generate:
                1. A viral LinkedIn post with a strong hook and relevant hashtags.
                2. A long-form YouTube script divided clearly into visual cues and voiceover narration.
                3. A punchy 30-second YouTube Short script.
                
                Content to process:
                {content_text}
                """
                
                # Generating content using Gemini 2.5 Flash
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                
                st.success("Content Generated Successfully!")
                st.markdown("### 📝 Results Output")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"An error occurred while connecting to Gemini: {e}")
