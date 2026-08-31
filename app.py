import os
import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
import glob

st.set_page_config(page_title="GIS Academic Assistant", page_icon="🌍")
st.title("🌍 Geography Academic AI Assistant")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("দয়া করে Streamlit Secrets-এ আপনার Gemini API Key সেট করুন।")
    st.stop()

@st.cache_data
def load_pdf_texts():
    text = ""
    for pdf in glob.glob("data/*.pdf"):
        reader = PdfReader(pdf)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

with st.spinner("সিস্টেম প্রস্তুত করা হচ্ছে..."):
    pdf_context = load_pdf_texts()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input box
user_query = st.chat_input("Write your question:")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("processing yor answer base on syllabus..."):
            try:
                model = genai.GenerativeModel("gemini-3.6-flash")
                
                # Strict syllabus priority prompt
                prompt = f"""You are an expert academic research assistant in Geography, GIS, and Geoinformatics. 
                - **Primary Rule (Strict Priority):** Always prioritize the provided syllabus and course books context first when answering. Use them as your main reference.
                - If the requested topic or answer is found in the syllabus, base your answer primarily on it.
                - If the topic is NOT mentioned or available in the syllabus, clearly state that it is not covered in the provided syllabus/books. Do not fabricate or force external answers as syllabus material.
                
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
