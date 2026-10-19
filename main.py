import io
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------------------------
# 1. 스트림릿 페이지 기본 설정 (가장 먼저 실행)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="전국 고령화 단계구분도",
    page_icon="🗺️",
    layout="wide"
)

# ------------------------------------------------------------------------------
# 2. 어두운 파스텔 Custom CSS
# ------------------------------------------------------------------------------
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #12141D 0%, #181B26 50%, #1E2230 100%);
        color: #F8FAFC !important;
    }
    p, span, label, h1, h2, h3, h4, h5, h6 {
        color: #F1F5F9 !important;
    }
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
# 3. 화면 타이틀 및 로딩 레이아웃 (접속 즉시 화면 표시)
# ------------------------------------------------------------------------------
st.markdown('<div class="main-title">🗺️ 전국 시·군·구 고령화 단계구분도</div>', unsafe_allow_html=True)
st.markdown('**2026년 최신 인구 데이터** 기준, 시·군·구별 65세 이상 고령화율(%)을 경계 지도로 시각화합니다.')
st.divider()


# ------------------------------------------------------------------------------
# 4. 데이터 로드 함수 (안전한 requests + io.BytesIO 방식 적용)
# ------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_and_process_data():
    csv_url = "https://raw.githubusercontent.com/keunyoo75750909/population/main/population_ts_yearly_gender.zip"
    geojson_url = "https://raw.githubusercontent.com/keunyoo75750909/population/main/sigungu_kr.geojson.txt"
    
    # 1. 인구 데이터 ZIP 파일 다운로드
    res_csv = requests.get(csv_url, timeout=30)
    res_csv.raise_for_status()
    
    # pandas로 ZIP 압축 해제하며 읽기
    df = pd.read_csv(io.BytesIO(res_csv.content), compression='zip', dtype={'코드': str})
    
    # 2. 2026년 최신 연도만 필터링 (2026년 데이터가 없을 경우 max 연도 자동 선택)
    latest_year = 2026 if 2026 in df['연도'].values else int(df['연도'].max())
    df = df[df['연도'] == latest_year].copy()
    
    # 3. 동 코드 앞 5자리 추출 (시군구 5자리 문자열 코드)
    df['시군구코드'] = df['코드'].astype(str).str.zfill(8).str[:5]
    
    # 4. 전체 인구 ('계_'로 시작하는 컬럼만)
    total_cols = [col for col in df.columns if col.startswith('계_')]
    
    # 5. 65세 이상 고령 인구 ('계_65세' ~ '계_100세 이상')
    elderly_cols = [f'계_{i}세' for i in range(65, 100)] + ['계_100세 이상']
    elderly_cols = [col for col in elderly_cols if col in df.columns]
    
    # 6. 시군구 5자리 코드로 합산
    df_sigungu = df.groupby('시군구코드').agg({
        '시도': 'first',
        '시군구': 'first',
        **{col: 'sum' for col in total_cols}
    }).reset_index()
    
    # 7. 전체인구, 고령인구, 고령화율(%) 연산
    df_sigungu['총인구'] = df_sigungu[total_cols].sum(axis=1)
    df_sigungu['고령인구'] = df_sigungu[elderly_cols].sum(axis=1)
    df_sigungu['고령화율'] = (df_sigungu['고령인구'] / df_sigungu['총인구']) * 100
    df_sigungu['지역명'] = df_sigungu['시도'] + ' ' + df_sigungu['시군구']
    
    # 8. GeoJSON 내려받기
    res_geo = requests.get(geojson_url, timeout=30)
    res_geo.raise_for_status()
    geojson_data = res_geo.json()
    
    return df_sigungu, geojson_data, latest_year


# ------------------------------------------------------------------------------
# 5. 실행 및 예외 처리 (오류 발생 시 화면에 안내)
# ------------------------------------------------------------------------------
try:
    with st.spinner("⏳ 인구 통계 데이터 및 시·군·구 경계를 불러오는 중입니다... (약 5~10초 소요)"):
        df_sigungu, sigungu_geojson, used_year = load_and_process_data()

    # 상단 요약 카드
    max_region = df_sigungu.loc[df_sigungu['고령화율'].idxmax()]
    min_region = df_sigungu.loc[df_sigungu['고령화율'].idxmin()]

    nat_total = df_sigungu['총인구'].sum()
    nat_elderly = df_sigungu['고령인구'].sum()
    nat_ratio = (nat_elderly / nat_total * 100) if nat_total > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("🇰🇷 전국 평균 고령화율", f"{nat_ratio:.1f} %")
    c2.metric("🟣 최고 고령화 지역", f"{max_region['지역명']}", f"{max_region['고령화율']:.1f} %")
    c3.metric("🔵 최저 고령화 지역", f"{min_region['지역명']}", f"{min_region['고령화율']:.1f} %")

    st.write("")

    # --------------------------------------------------------------------------
    # 6. Plotly 단계구분도 (배경 지도 타일 없이 경계만 시각화)
    # --------------------------------------------------------------------------
    fig = px.choropleth(
        df_sigungu,
        geojson=sigungu_geojson,
        locations='시군구코드',
        featureidkey="properties.코드",
        color='고령화율',
        color_continuous_scale=[
            [0.0, "#312E81"],
            [0.25, "#6366F1"],
            [0.5, "#A855F7"],
            [0.75, "#EC4899"],
            [1.0, "#F43F5E"]
        ],
        hover_name='지역명',
        hover_data={
            '시군구코드': False,
            '고령화율': ':.1f',
            '총인구': ':,',
            '고령인구': ':,'
        },
        labels={
            '고령화율': '고령화율(%)',
            '총인구': '총인구(명)',
            '고령인구': '65세 이상 인구(명)'
        }
    )

    # 배경 타일 없이 경계선 위치로 줌 설정
    fig.update_geos(
        fitbounds="locations",
        visible=False
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin={"r": 0, "t": 20, "l": 0, "b": 0},
        height=750,
        coloraxis_colorbar=dict(
            title="<b>고령화율 (%)</b>",
            title_font=dict(color="#F8FAFC", size=13),
            tickfont=dict(color="#CBD5E1"),
            len=0.7,
            thickness=18
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
        <div class="info-card">
            💡 <b>지도 활용 가이드</b><br>
            • <b>5자리 코드 매핑</b>: 행정구역 5자리 고유 코드를 이용해 경계선과 인구 통계를 정확히 일치시켰습니다.<br>
            • <b>마우스 오버</b>: 시·군·구 위에 마우스를 올리면 <b>지역 이름</b>과 <b>고령화율(%)</b>, <b>총인구수</b>를 확인할 수 있습니다.<br>
            • <b>색상 표현</b>: 붉은색에 가까울수록 65세 이상 고령 인구 비율이 높은 지역입니다.
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ 데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.info("GitHub 저장소의 파일 URL 접근 상태를 확인하거나 잠시 후 다시 새로고침해 주세요.")
