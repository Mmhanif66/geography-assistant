import os
import streamlit as st
import google.generativeai as genai
import glob
import gdown

st.set_page_config(page_title="GIS Academic Assistant", page_icon="🌍")
st.title("Ges Academic AI Assistant")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("দয়া করে Streamlit Secrets-এ আপনার Gemini API Key সেট করুন।")
    st.stop()

# --- GOOGLE DRIVE FOLDER LINKS ---
GDRIVE_LINKS = [
    "https://drive.google.com/drive/folders/18HWp-8h5Q-SjKAO2uoJtq5m-KDpvHNQy?usp=sharing",
    "https://drive.google.com/drive/folders/1F5lTVpg4UgrEHPm1ffOiDUogeeOgPxaT?usp=sharing",
    "https://drive.google.com/drive/folders/1nHGAGPn39ev0zuYiatRmVPozMj-KBD9c?usp=sharing",
    "https://drive.google.com/drive/folders/1miba1GdMQYtq89MmIeArMUooBTea0DnA" # Masters
]

# Sidebar option to manually clear cache and force update instantly if needed
with st.sidebar:
    st.header("⚙️ ডাটা ম্যানেজমেন্ট")
    st.markdown("ড্রাইভে বা ফোল্ডারে নতুন ফাইল যোগ করলে সাথে সাথে আপডেট করতে নিচে ক্লিক করুন:")
    if st.button("🔄 Force Sync & Update"):
        st.cache_resource.clear()
        st.success("ক্যাশ আপডেট করা হয়েছে!")
        st.rerun()

# Auto-sync and load files (TTL 600 seconds = every 10 minutes it automatically re-checks Drive for updates)
@st.cache_resource(ttl=600)
def initialize_files():
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Download/Sync from all Google Drive folders (gdown automatically skips old files and pulls new files)
    for link in GDRIVE_LINKS:
        if link:
            try:
                gdown.download_folder(link, output=output_dir, quiet=True, use_cookies=False)
            except Exception:
                pass
                
    # 2. Gather all PDFs from both local 'data' folder and Google Drive synced folder
    uploaded_files = []
    pdf_files = glob.glob(os.path.join(output_dir, "**/*.pdf"), recursive=True)
    
    for pdf in pdf_files:
        try:
            # Upload directly to Gemini File API (Supports Scanned PDFs, Images & Text natively)
            f = genai.upload_file(pdf)
            uploaded_files.append(f)
        except Exception:
            pass
            
    return uploaded_files

with st.spinner("গুগল ড্রাইভ ও লোকাল ডাটা সিঙ্ক করা হচ্ছে..."):
    gemini_files = initialize_files()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_query = st.chat_input("Enter Your Query:")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Answer is processing..."):
            try:
                model = genai.GenerativeModel("gemini-3.6-flash")
                
                # Combine uploaded files context with the user prompt
                contents = gemini_files + [
                    f"""You are an expert academic research assistant in Geography, GIS, and Geoinformatics. 
                    - **Priority Rule:** If the topic is found in the provided files context, prioritize and base your answer primarily on it.
                    - **Fallback Rule:** If the topic is NOT mentioned in the files, you can provide a comprehensive, accurate, and professional answer using your advanced expert knowledge in GIS, Remote Sensing, and Geography.
                    
                    Question: {user_query}"""
                ]
                
                response = model.generate_content(contents)
                answer = response.text
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                error_msg = f"টেকনিক্যাল সমস্যা দেখা দিয়েছে: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
