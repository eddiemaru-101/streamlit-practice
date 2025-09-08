#심플 streamlit 웹 앱
import streamlit as st

st.title("간단한 인사 앱")
name = st.text_input("당신의 이름을 입력하세요")
if name: 
	st.write(f"안녕하세요, {name}님! 반갑습니다!")
# 실행방법
# 1. 터미널에서 프로젝트 폴더로 이동
# 2. streamlit run app.py 실행	