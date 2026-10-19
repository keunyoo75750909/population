import math
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------------------------
# 1. 스트림릿 페이지 기본 설정 (페이지 제목, 레이아웃 등)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 따뜻한 톤을 위한 Custom CSS 스타일 적용
st.markdown("""
    <style>
    /* 전체 배경색을 따뜻한 아이보리 톤으로 설정 */
    .main {
        background-color: #FDFBF7;
    }
    /* 지표 카드 박스 스타일링 */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        border: 1px solid #F0EAE1;
    }
    /* 피라미드 아래 특징 요약 박스 스타일링 */
    .summary-box {
        background-color: #FFFDF9;
        border-left: 5px solid #E07A5F;
        padding: 18px 22px;
        border-radius: 10px;
        margin-top: 25px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        font-size: 1.05rem;
        line-height: 1.6;
        color: #2B2D42;
    }
    </style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# 2. 데이터 로드 및 캐싱 (속도 최적화)
# ------------------------------------------------------------------------------
@st.cache_data
def load_population_data():
    """
    GitHub에 업로드된 압축 CSV 파일을 판다스로 직접 읽어옵니다.
    GitHub의 'blob' URL 대신 직접 파일 데이터를 가져올 수 있는 'raw' URL을 사용합니다.
    """
    raw_url = "https://raw.githubusercontent.com/keunyoo75750909/population/main/population_ts_yearly_gender.zip"
    
    # CSV 데이터 읽기
    df = pd.read_csv(raw_url)
    
    # 가장 최신 연도만 추출 (예: 2026년)
    latest_year = int(df['연도'].max())
    df_latest = df[df['연도'] == latest_year].copy()
    
    return df_latest, latest_year

# 데이터 로딩 진행 상태 표시
with st.spinner("인구 데이터를 불러오는 중입니다..."):
    df, latest_year = load_population_data()


# ------------------------------------------------------------------------------
# 3. 앱 타이틀 및 안내 문구
# ------------------------------------------------------------------------------
st.title("🏡 우리 동네 인구 피라미드")
st.markdown(f"**{latest_year}년 최신 데이터** 기준 전국 읍·면·동별 연령 및 성별 인구 구조를 확인해 보세요.")
st.divider()


# ------------------------------------------------------------------------------
# 4. 상단 드롭다운 메뉴 (시도 → 시군구 → 동 3단계 연동)
# ------------------------------------------------------------------------------
st.subheader("📍 지역 선택")

col_sido, col_sigungu, col_dong = st.columns(3)

# 1) 시도 선택
with col_sido:
    sido_list = sorted(df['시도'].dropna().unique())
    selected_sido = st.selectbox("1. 시·도 선택", sido_list)

# 2) 시군구 선택 (선택된 시도에 해당하는 데이터만 필터링)
df_sido = df[df['시도'] == selected_sido]
with col_sigungu:
    sigungu_list = sorted(df_sido['시군구'].dropna().unique())
    selected_sigungu = st.
