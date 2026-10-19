import pandas as pd
import requests
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------------------------
# 1. 스트림릿 페이지 기본 설정
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="전국 고령화 단계구분도",
    page_icon="🗺️",
    layout="wide"
)

# ------------------------------------------------------------------------------
# 2. 어두운 파스텔 톤 Custom CSS (디자인 스파크)
# ------------------------------------------------------------------------------
st.markdown("""
    <style>
    /* 전체 배경: 딥 슬레이트 파스텔 그라데이션 */
    .stApp {
        background: linear-gradient(135deg, #12141D 0%, #181B26 50%, #1E2230 100%);
        color: #F8FAFC !important;
    }
    
    /* 텍스트 가독성 강화 */
    p, span, label, h1, h2, h3, h4, h5, h6 {
        color: #F1F5F9 !important;
    }
    
    /* 메인 타이틀 그라데이션 */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #C084FC, #F472B6, #818CF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .sub-title {
        color: #CBD5E1 !important;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }

    /* 지표 카드 스타일링 */
    div[data-testid="stMetric"] {
        background: rgba(38, 43, 61, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 18px 22px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetricLabel"] {
        color: #CBD5E1 !important;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 700;
    }

    /* 요약 안내 박스 */
    .info-card {
        background: linear-gradient(135deg, rgba(38, 43, 61, 0.85) 0%, rgba(26, 29, 41, 0.9) 100%);
        border: 1px solid rgba(244, 114, 182, 0.3);
        border-left: 6px solid #EC4899;
        padding: 20px 24px;
        border-radius: 14px;
        margin-top: 25px;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# 3. 데이터 및 GeoJSON 로드 & 전처리 함수 (캐싱 적용)
# ------------------------------------------------------------------------------
@st.cache_data
def load_and_process_data():
    """
    1) GitHub에서 인구 CSV와 시군구 GeoJSON을 불러옵니다.
    2) 2026년 데이터만 필터링합니다.
    3) 동 코드를 5자리 시군구 코드로 변환하여 시군구별 고령화율을 계산합니다.
    """
    # Raw URL 주소 설정
    csv_url = "https://raw.githubusercontent.com/keunyoo75750909/population/main/population_ts_yearly_gender.zip"
    geojson_url = "https://raw.githubusercontent.com/keunyoo75750909/population/main/sigungu_kr.geojson.txt"
    
    # 1. 인구 CSV 파일 읽기 (코드는 문자열로 지정
