import math
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------------------------
# 1. 스트림릿 페이지 기본 설정
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# 2. 감각적인 어두운 파스텔 톤 Custom CSS
# ------------------------------------------------------------------------------
st.markdown("""
    <style>
    /* 전체 배경: 어두운 파스텔 딥 슬레이트 그라데이션 */
    .stApp {
        background: linear-gradient(135deg, #13151E 0%, #1A1D28 50%, #222636 100%);
        color: #E2E8F0;
    }
    
    /* 타이틀 그라데이션 포인트 */
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #A855F7, #EC4899, #6366F1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .sub-title {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }

    /* 상단 지표 카드: 글래스모피즘 & 호버 모션 */
    div[data-testid="stMetric"] {
        background: rgba(30, 34, 48, 0.65);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 18px 22px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        border-color: rgba(168, 85, 247, 0.4);
        box-shadow: 0 12px 28px rgba(168, 85, 247, 0.15);
    }
    
    /* 지표 카드 내부 글씨 색상 조정 */
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-weight: 700;
    }

    /* 하단 진단 박스: 프리미엄 카드 디자인 */
    .summary-card {
        background: linear-gradient(135deg, rgba(35, 40, 58, 0.7) 0%, rgba(24, 28, 42, 0.8) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(236, 72, 153, 0.25);
        border-left: 6px solid #EC4899;
        padding: 22px 26px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        margin-top: 30px;
        font-size: 1.08rem;
        line-height: 1.7;
        color: #E2E8F0;
    }
    
    /* 구분선 컬러 모던화 */
    hr {
        border-color: rgba(255, 255, 255, 0.08) !important;
    }
    </style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# 3. 데이터 로드 및 캐싱
# ------------------------------------------------------------------------------
@st.cache_data
def load_population_data():
    raw_url = "https://raw.githubusercontent.com/keunyoo75750909/population/main/population_ts_yearly_gender.zip"
    df = pd.read_csv(raw_url)
    latest_year = int(df['연도'].max())
    df_latest = df[df['연도'] == latest_year].copy()
    return df_latest, latest_year

with st.spinner("
