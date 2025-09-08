import streamlit as st


st.title("안녕봇")
st.write('단간한 인사앱')

name = st.text_input("이름이 어떻게 되세요")
if name :
    st.write(f"반가워 {name}아!")
