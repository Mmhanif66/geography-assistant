import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

st.set_page_config(page_title="GIS Academic Assistant", page_icon="🌍")
st.title("🌍 GIS & Geography Academic AI Assistant")

# Get API Key from Streamlit Secrets and set to environment
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = api_key
except Exception:
    st.error("দয়া করে Streamlit Secrets-এ আপনার Gemini API Key সেট করুন।")
    st.stop()

@st.cache_resource
def load_vector_db():
    loader = PyPDFDirectoryLoader("data")
    docs = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    
    # Using text-embedding-004 model
    embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
    vectorstore = FAISS.from_documents(splits, embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 3})

with st.spinner("সিলেবাস ও নোটস লোড করা হচ্ছে... দয়া করে অপেক্ষা করুন।"):
    retriever = load_vector_db()

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)
qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

user_query = st.text_input("আপনার জিআইএস বা ভূগোলের প্রশ্নটি এখানে লিখুন:")
if user_query:
    with st.spinner("সিলেবাস খুঁজে উত্তর তৈরি করা হচ্ছে..."):
        prompt = f"You are an expert academic research assistant in Geography, GIS, and Geoinformatics. Answer strictly and accurately based on the provided context: {user_query}"
        response = qa_chain.run(prompt)
        st.markdown("### উত্তর:")
        st.write(response)
