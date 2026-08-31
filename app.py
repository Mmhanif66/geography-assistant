import os
import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
import glob

st.set_page_config(page_title="GIS Academic Assistant", page_icon="🌍")
st.title("🌍 GIS & Geography Academic AI Assistant")

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

# Automatically find a working model supported by your API key
@st.cache_resource
def get_working_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return genai.GenerativeModel(m.name)
    except Exception:
        pass
    return genai.GenerativeModel("gemini-1.5-flash")

user_query = st.text_input("আপনার জিআইএস বা ভূগোলের প্রশ্নটি এখানে লিখুন:")

if user_query:
    if not pdf_context:
        st.warning("`data` ফোল্ডারে কোনো পিডিএফ ফাইল পাওয়া যায়নি।")
    else:
        with st.spinner("উত্তর তৈরি করা হচ্ছে..."):
            try:
                model = get_working_model()
                
                prompt = f"""You are an expert academic research assistant in Geography and GIS. 
                Answer accurately and concisely based on the context below.
                
                Context:
                {pdf_context[:25000]}
                
                Question: {user_query}"""
                
                response = model.generate_content(prompt)
                st.markdown("### উত্তর:")
                st.write(response.text)
            except Exception as e:
                st.error(f"টেকনিক্যাল সমস্যা দেখা দিয়েছে: {e}")
