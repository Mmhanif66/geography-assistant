import os
import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
import glob
import gdown

st.set_page_config(page_title="GIS Academic Assistant", page_icon="🌍")
st.title("🌍 GIS & Geography Academic AI Assistant")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("দয়া করে Streamlit Secrets-এ আপনার Gemini API Key সেট করুন।")
    st.stop()

# --- MULTIPLE GOOGLE DRIVE FOLDER LINKS ---
# আপনি যত খুশি ড্রাইভ ফোল্ডারের লিংক এখানে নিচের মতো করে যুক্ত করতে পারবেন:
GDRIVE_LINKS = [
    "https://drive.google.com/drive/folders/18HWp-8h5Q-SjKAO2uoJtq5m-KDpvHNQy?usp=sharing",
    "https://drive.google.com/drive/folders/1F5lTVpg4UgrEHPm1ffOiDUogeeOgPxaT?usp=sharing",
    "https://drive.google.com/drive/folders/1nHGAGPn39ev0zuYiatRmVPozMj-KBD9c?usp=sharing",
    "https://drive.google.com/drive/folders/1miba1GdMQYtq89MmIeArMUooBTea0DnA"#Masters
    # "আপনার_৩য়_লিংকটি_এখানে_বসান"
]

@st.cache_data
def load_pdf_texts():
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    
    # Download files from all provided Google Drive folders
    for link in GDRIVE_LINKS:
        if link and "YOUR_" not in link:
            try:
                gdown.download_folder(link, output=output_dir, quiet=True, use_cookies=False)
            except Exception as e:
                pass

    # Read all PDFs from data folder
    text = ""
    for pdf in glob.glob(os.path.join(output_dir, "*.pdf")):
        try:
            reader = PdfReader(pdf)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception:
            pass
    return text

with st.spinner("গুগল ড্রাইভ ও সিস্টেম প্রস্তুত করা হচ্ছে..."):
    pdf_context = load_pdf_texts()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input box
user_query = st.chat_input("আপনার জিআইএস বা ভূগোলের প্রশ্নটি এখানে লিখুন:")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("উত্তর তৈরি করা হচ্ছে..."):
            try:
                model = genai.GenerativeModel("gemini-3.6-flash")
                
                prompt = f"""You are an expert academic research assistant in Geography, GIS, and Geoinformatics. 
                - **Priority Rule:** If the topic is found in the provided syllabus/books context, prioritize and base your answer primarily on it.
                - **Fallback Rule:** If the topic is NOT mentioned in the syllabus, you can provide a comprehensive, accurate, and professional answer using your advanced expert knowledge in GIS, Remote Sensing, and Geography.
                
                Syllabus Context:
                {pdf_context[:25000]}
                
                Question: {user_query}"""
                
                response = model.generate_content(prompt)
                answer = response.text
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                error_msg = f"টেকনিক্যাল সমস্যা দেখা দিয়েছে: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
