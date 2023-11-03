import streamlit as st
import requests

st.image('DocuAI.png')

selected_tab = st.sidebar.selectbox("Select a tab:", ["Try", "Docs"])

if selected_tab == "Try":
    try:
        # Code that may raise an exception
        st.title('URL Summarization & QnA Model')
        user_url_input = st.text_input("Extract a file", "")
        extraction_method = st.selectbox("Choose Extraction Method", ["PyPDF", "Nougat OCR"])

        if extraction_method == "PyPDF":
            response = requests.get(f"https://pdf-qna-fastapi-e398b25aae73.herokuapp.com/extract_text/?selected_tab=Try&user_url_input={user_url_input}&&extraction_method={extraction_method}")
            st.write(response.json().get("texts"))
            user_url_question= st.text_input("Ask a Question", "")
            response = requests.get(f"https://pdf-qna-fastapi-e398b25aae73.herokuapp.com/get_a/?user_url_input={user_url_input}&user_question={user_url_question}")
            st.write(response.json().get("answer"))

        
        elif extraction_method == "Nougat OCR":
            response = requests.get(f"https://pdf-qna-fastapi-e398b25aae73.herokuapp.com/extract_text/?selected_tab=Try&user_url_input={user_url_input}&$extraction_method={extraction_method}")
            st.write(response.json().get("texts"))
            user_url_question= st.text_input("Ask a Question", "")
            response = requests.get(f"https://pdf-qna-fastapi-e398b25aae73.herokuapp.com/get_a/?user_url_input={user_url_input}&user_question={user_url_question}")
            st.write(response.json().get("answer"))
                


    except Exception as e:
        # Handle the exception
        st.write("Enter URL Above")

elif selected_tab == "Docs":
    st.title("DOCUMENTATION FOR NOUGHAT AND PYPDF")
    st.subheader("NOUGHAT PROS AND CONS:")
    st.write("""
             **PROS:**
             - Better handling of images and embedded objects within the PDF
             - Provides more contextual summaries for longer documents
             """)
    st.write("""
             **CONS:**
             - Slower processing time as compared to pypdf
             - Some compatibility issues with heavily formatted documents
             """)
    st.subheader("PYPDF PROS AND CONS:")
    st.write("""
             **PROS:**
             - Faster processing speeds for text-heavy documents
             - Simple to use and has a straightforward integration with Streamlit
             """)
    st.write("""
             **CONS:**
             - Cannot effectively handle images or embedded objects
             - Summaries can occasionally miss crucial information for very lengthy documents
              """)
    st.subheader("ARCHITECTURE DIAGRAM")
    st.image('pdf_qna.png')










