import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
#import koreanize_matplotlib  # 한글/마이너스 자동 설정
#import matplotlib.font_manager as fm

# NanumGothic 폰트 경로를 직접 지정
# font_path = "C:/Windows/Fonts/NanumGothic.ttf"
# fontprop = fm.FontProperties(fname=font_path)
# plt.rcParams["font.family"] = "NanumGothic"
# plt.rcParams["axes.unicode_minus"] = False

# 한글 폰트 설정 (배포 환경 호환)
try:
    plt.rcParams['font.family'] = "Malgun Gothic"
except:
    try:
        plt.rcParams['font.family'] = "DejaVu Sans"
    except:
        plt.rcParams['font.family'] = "sans-serif"
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="퇴직율 대시보드", layout="wide")
try:
    sns.set(style="whitegrid", font="Malgun Gothic")
except:
    sns.set(style="whitegrid")

# 1) 데이터 로드
@st.cache_data
def load_df(path:str ="HR_Data.csv") -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except: 
        return pd.DataFrame()
    df["퇴직"] = df["퇴직여부"].map({"Yes":1, "No":0}).astype("int8")
    df.drop(['직원수', '18세이상'], axis=1, inplace=True)
    return df


df = load_df()
if df.empty:
    st.error("데이터가 없습니다. 'HR_Data.csv' 파일을 확인하세요.")
    st.stop()

# ===== KPI  =====
# 1) 헤더 & KPI
st.title("퇴직율 분석 및 인사이트")
n = len(df); quit_n = int(df["퇴직"].sum())
quit_rate = df["퇴직"].mean()*100
stay_rate = 100 - quit_rate
k1,k2,k3,k4 = st.columns(4)
k1.metric("전체 직원 수", f"{n:,}명")
k2.metric("퇴직자 수", f"{quit_n:,}명")
k3.metric("유지율", f"{stay_rate:.1f}%")
k4.metric("퇴직율", f"{quit_rate:.1f}%")

# 3) 그래프 1: 부서별 퇴직율
if "부서" in df.columns:
    dept = (df.groupby("부서")["퇴직"].mean().sort_values(ascending=False)*100)
    # 부서명을 영어로 매핑
    dept_mapping = {
        "Research & Development": "R&D",
        "Sales": "Sales",
        "Human Resources": "HR"
    }
    dept.index = [dept_mapping.get(x, x) for x in dept.index]
    
    st.subheader("부서별 퇴직율")
    fig1, ax1 = plt.subplots(figsize=(7.5,3.8))
    sns.barplot(x=dept.index, y=dept.values, ax=ax1)
    ax1.set_ylabel("Turnover Rate (%)"); 
    ax1.set_xlabel("Department")
    ax1.bar_label(ax1.containers[0], fmt="%.1f")
    plt.xticks(rotation=15); 
    st.pyplot(fig1)


# 4) 그래프 2/3를 두 칼럼으로
c1, c2 = st.columns(2)


# (좌) 급여인상율과 퇴직율 (정수%로 라운딩 후 라인)
if "급여증가분백분율" in df.columns:
    tmp = df[["급여증가분백분율","퇴직"]].dropna().copy()
    tmp["인상률(%)"] = tmp["급여증가분백분율"].round().astype(int)
    sal = tmp.groupby("인상률(%)")["퇴직"].mean()*100
    with c1:
        st.subheader("💰 급여인상율과 퇴직율")
        fig2, ax2 = plt.subplots(figsize=(6.5,3.5))
        sns.lineplot(x=sal.index, y=sal.values, marker="o", ax=ax2)
        ax2.set_xlabel("Salary Increase Rate (%)"); 
        ax2.set_ylabel("Turnover Rate (%)")
        st.pyplot(fig2)


# (우) 야근정도별 퇴직율 (Yes/No 막대)
col_name = "야근정도"
if col_name in df.columns:
    ot = (df.groupby(col_name)["퇴직"].mean()*100)
    # 야근 라벨을 영어로 변경
    ot.index = ot.index.map({"Yes": "Overtime", "No": "No Overtime"})
    
    with c2:
        st.subheader("⏰ 야근정도별 퇴직율")
        fig3, ax3 = plt.subplots(figsize=(6.5,3.5))
        sns.barplot(x=ot.index, y=ot.values, ax=ax3)
        ax3.set_ylabel("Turnover Rate (%)"); 
        ax3.set_xlabel("Overtime Status")
        ax3.bar_label(ax3.containers[0], fmt="%.1f")
        st.pyplot(fig3)

# 5) 연령대별 퇴직율 분석
st.subheader("📊 연령대별 퇴직율 분석")
if "나이" in df.columns:
    df["연령대"] = pd.cut(df["나이"], bins=[0,30,40,50,100], labels=["20s","30s","40s","50s+"])
    age_quit = df.groupby("연령대")["퇴직"].mean()*100
    
    c3, c4 = st.columns(2)
    with c3:
        fig4, ax4 = plt.subplots(figsize=(6,4))
        sns.barplot(x=age_quit.index, y=age_quit.values, ax=ax4, palette="viridis")
        ax4.set_ylabel("Turnover Rate (%)")
        ax4.set_xlabel("Age Group")
        ax4.bar_label(ax4.containers[0], fmt="%.1f")
        plt.title("Turnover Rate by Age Group")
        st.pyplot(fig4)
    
    with c4:
        age_dist = df["연령대"].value_counts().sort_index()
        fig5, ax5 = plt.subplots(figsize=(6,4))
        colors = plt.cm.Set3(np.linspace(0,1,len(age_dist)))
        wedges, texts, autotexts = ax5.pie(age_dist.values, labels=age_dist.index, autopct='%1.1f%%', colors=colors)
        plt.title("Employee Age Distribution")
        st.pyplot(fig5)

# 6) 업무만족도와 퇴직율 상관관계
st.subheader("😊 업무만족도별 퇴직율")
satisfaction_cols = ["업무만족도", "업무환경만족도", "업무참여도"]
c5, c6, c7 = st.columns(3)

for i, col in enumerate(satisfaction_cols):
    if col in df.columns:
        sat_quit = df.groupby(col)["퇴직"].mean()*100
        with [c5, c6, c7][i]:
            fig, ax = plt.subplots(figsize=(5,3.5))
            sns.lineplot(x=sat_quit.index, y=sat_quit.values, marker="o", ax=ax, color=["red","blue","green"][i])
            ax.set_xlabel(col.replace("업무만족도", "Job Satisfaction").replace("업무환경만족도", "Work Environment").replace("업무참여도", "Work Engagement"))
            ax.set_ylabel("Turnover Rate (%)")
            ax.set_title(f"{col.replace('업무만족도', 'Job Satisfaction').replace('업무환경만족도', 'Work Environment').replace('업무참여도', 'Work Engagement')} vs Turnover")
            st.pyplot(fig)

# 7) 근속연수와 승진 분석
st.subheader("🏆 근속연수 및 승진 분석")
if "근속연수" in df.columns and "마지막승진년수" in df.columns:
    c8, c9 = st.columns(2)
    
    with c8:
        # 근속연수별 퇴직율
        df["근속그룹"] = pd.cut(df["근속연수"], bins=[-1,2,5,10,50], labels=["Junior(0-2y)","Mid(3-5y)","Senior(6-10y)","Expert(10y+)"])
        tenure_quit = df.groupby("근속그룹")["퇴직"].mean()*100
        
        fig6, ax6 = plt.subplots(figsize=(6,4))
        sns.barplot(x=tenure_quit.index, y=tenure_quit.values, ax=ax6, palette="coolwarm")
        ax6.set_ylabel("Turnover Rate (%)")
        ax6.set_xlabel("Tenure Group")
        ax6.bar_label(ax6.containers[0], fmt="%.1f")
        plt.xticks(rotation=45)
        plt.title("Turnover Rate by Tenure")
        st.pyplot(fig6)
    
    with c9:
        # 승진 횟수와 퇴직율 관계
        promo_quit = df.groupby("마지막승진년수")["퇴직"].mean()*100
        fig7, ax7 = plt.subplots(figsize=(6,4))
        ax7.scatter(promo_quit.index, promo_quit.values, s=60, alpha=0.7, color="orange")
        ax7.set_xlabel("Years Since Last Promotion")
        ax7.set_ylabel("Turnover Rate (%)")
        plt.title("Years Since Promotion vs Turnover")
        st.pyplot(fig7)

# 8) 급여 vs 연령 vs 퇴직 3차원 분석
st.subheader("💰 급여-연령-퇴직 종합 분석")
if "월급여" in df.columns and "나이" in df.columns:
    fig8, ax8 = plt.subplots(figsize=(10,6))
    
    # 퇴직자와 재직자 분리
    quit_yes = df[df["퇴직여부"]=="Yes"]
    quit_no = df[df["퇴직여부"]=="No"]
    
    ax8.scatter(quit_no["나이"], quit_no["월급여"], alpha=0.6, c="blue", label="Active", s=30)
    ax8.scatter(quit_yes["나이"], quit_yes["월급여"], alpha=0.8, c="red", label="Resigned", s=30)
    ax8.set_xlabel("Age")
    ax8.set_ylabel("Monthly Salary")
    ax8.legend()
    plt.title("Age-Salary Distribution by Employment Status")
    st.pyplot(fig8)

# 9) 성별-부서별 퇴직율 히트맵
st.subheader("🔥 성별-부서별 퇴직율 히트맵")
if "성별" in df.columns and "부서" in df.columns:
    # 성별과 부서를 영어로 매핑
    df_temp = df.copy()
    df_temp["성별"] = df_temp["성별"].map({"Male": "Male", "Female": "Female"})
    df_temp["부서"] = df_temp["부서"].map({
        "Research & Development": "R&D",
        "Sales": "Sales", 
        "Human Resources": "HR"
    })
    
    gender_dept = df_temp.pivot_table(values="퇴직", index="성별", columns="부서", aggfunc="mean")*100
    
    fig9, ax9 = plt.subplots(figsize=(10,4))
    sns.heatmap(gender_dept, annot=True, fmt=".1f", cmap="Reds", ax=ax9)
    ax9.set_xlabel("Department")
    ax9.set_ylabel("Gender")
    plt.title("Turnover Rate by Gender-Department (%)")
    st.pyplot(fig9)

# 10) 핵심 인사이트 요약
st.subheader("🎯 핵심 인사이트")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **🔍 주요 발견사항:**
    - 가장 높은 퇴직율을 보이는 부서 확인
    - 급여 인상률과 퇴직율의 역관계
    - 야근이 퇴직에 미치는 영향
    - 연령대별 퇴직 패턴 분석
    """)

with col2:
    if "부서" in df.columns:
        highest_quit_dept = (df.groupby("부서")["퇴직"].mean()*100).idxmax()
        highest_quit_rate = (df.groupby("부서")["퇴직"].mean()*100).max()
        st.metric("최고 퇴직율 부서", highest_quit_dept, f"{highest_quit_rate:.1f}%")
    
    if "연령대" in df.columns:
        age_quit_max = age_quit.idxmax()
        age_quit_rate = age_quit.max()
        st.metric("최고 위험 연령대", age_quit_max, f"{age_quit_rate:.1f}%")
