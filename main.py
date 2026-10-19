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
# 2. 고대비 텍스트 & 피라미드 은은한 글로우(Glow) Custom CSS
# ------------------------------------------------------------------------------
st.markdown("""
    <style>
    /* 전체 배경: 어두운 파스텔 딥 슬레이트 */
    .stApp {
        background: linear-gradient(135deg, #12141D 0%, #181B26 50%, #1E2230 100%);
        color: #F8FAFC !important;
    }
    
    /* 일반 라벨 및 마크다운 텍스트 선명도 보정 */
    p, span, label, h1, h2, h3, h4, h5, h6 {
        color: #F1F5F9 !important;
    }
    
    /* 메인 타이틀 */
    .main-title {
        font-size: 2.3rem;
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

    /* 드롭다운(Selectbox) 글씨 선명도 및 배경 보정 */
    div[data-baseweb="select"] > div {
        background-color: #262B3D !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] * {
        color: #FFFFFF !important;
    }
    /* 드롭다운 클릭 시 메뉴 목록 스타일 */
    ul[data-baseweb="menu"] {
        background-color: #262B3D !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    li[data-baseweb="option"] {
        color: #FFFFFF !important;
        background-color: #262B3D !important;
    }
    li[data-baseweb="option"]:hover {
        background-color: #3B4259 !important;
    }

    /* 상단 지표 카드 스타일 */
    div[data-testid="stMetric"] {
        background: rgba(38, 43, 61, 0.75);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 18px 22px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        border-color: rgba(192, 132, 252, 0.5);
        box-shadow: 0 12px 28px rgba(192, 132, 252, 0.2);
    }
    
    div[data-testid="stMetricLabel"] {
        color: #CBD5E1 !important;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 700;
    }

    /* 하단 진단 박스 */
    .summary-card {
        background: linear-gradient(135deg, rgba(38, 43, 61, 0.85) 0%, rgba(26, 29, 41, 0.9) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(244, 114, 182, 0.3);
        border-left: 6px solid #EC4899;
        padding: 22px 26px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        margin-top: 30px;
        font-size: 1.08rem;
        line-height: 1.7;
        color: #F8FAFC !important;
    }

    /* [핵심] Plotly 피라미드 막대에 은은한 네온 글로우(Glow) 효과 적용 */
    .js-plotly-plot .plotly .bars path {
        filter: drop-shadow(0px 0px 5px rgba(129, 140, 248, 0.55));
        transition: all 0.2s ease;
    }
    .js-plotly-plot .plotly .bars path:hover {
        filter: drop-shadow(0px 0px 9px rgba(244, 114, 182, 0.85));
    }
    
    hr {
        border-color: rgba(255, 255, 255, 0.12) !important;
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

with st.spinner("인구 데이터를 불러오는 중입니다..."):
    df, latest_year = load_population_data()


# ------------------------------------------------------------------------------
# 4. 앱 헤더 및 안내
# ------------------------------------------------------------------------------
st.markdown('<div class="main-title">🏡 우리 동네 인구 피라미드</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title"><b>{latest_year}년 최신 데이터</b> 기준 전국 읍·면·동별 연령 및 성별 인구 구조 분석</div>', unsafe_allow_html=True)
st.divider()


# ------------------------------------------------------------------------------
# 5. 상단 드롭다운 메뉴 (3단계)
# ------------------------------------------------------------------------------
st.markdown("##### 📍 분석할 지역을 선택해주세요")

col_sido, col_sigungu, col_dong = st.columns(3)

with col_sido:
    sido_list = sorted(df['시도'].dropna().unique())
    selected_sido = st.selectbox("시·도", sido_list)

df_sido = df[df['시도'] == selected_sido]
with col_sigungu:
    sigungu_list = sorted(df_sido['시군구'].dropna().unique())
    selected_sigungu = st.selectbox("시·군·구", sigungu_list)

df_sigungu = df_sido[df_sido['시군구'] == selected_sigungu]
with col_dong:
    dong_list = sorted(df_sigungu['동'].dropna().unique())
    selected_dong = st.selectbox("읍·면·동", dong_list)


# ------------------------------------------------------------------------------
# 6. 데이터 연산 및 주요 지표
# ------------------------------------------------------------------------------
selected_data = df_sigungu[df_sigungu['동'] == selected_dong]

if not selected_data.empty:
    row = selected_data.iloc[0]
    
    age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]
    
    male_counts = [row[f"남_{age}"] if f"남_{age}" in row else 0 for age in age_labels]
    female_counts = [row[f"여_{age}"] if f"여_{age}" in row else 0 for age in age_labels]
    
    age_totals = [m + f for m, f in zip(male_counts, female_counts)]
    
    total_pop = sum(age_totals)
    
    if total_pop > 0:
        weighted_age_sum = sum(i * count for i, count in enumerate(age_totals[:100]))
        weighted_age_sum += 100 * age_totals[100]
        avg_age = weighted_age_sum / total_pop
    else:
        avg_age = 0.0
        
    child_pop = sum(age_totals[0:15])          # 0~14세
    elderly_pop = sum(age_totals[65:])         # 65세 이상
    
    child_ratio = (child_pop / total_pop * 100) if total_pop > 0 else 0.0
    elderly_ratio = (elderly_pop / total_pop * 100) if total_pop > 0 else 0.0

    st.write("")

    # --------------------------------------------------------------------------
    # 7. 지표 카드 3개 나란히 배치
    # --------------------------------------------------------------------------
    card1, card2, card3 = st.columns(3)
    
    card1.metric(
        label="👥 총인구",
        value=f"{total_pop:,} 명"
    )
    
    card2.metric(
        label="🎂 평균연령",
        value=f"{avg_age:.1f} 세"
    )
    
    if elderly_ratio >= 20.0:
        card3.metric(
            label="👵 고령화율 (65세 이상) ⚠️",
            value=f"{elderly_ratio:.1f} %",
            delta="초고령사회 (20% 이상)",
            delta_color="inverse"
        )
    else:
        card3.metric(
            label="👵 고령화율 (65세 이상)",
            value=f"{elderly_ratio:.1f} %",
            delta="일반" if elderly_ratio < 14.0 else "고령사회 (14% 이상)",
            delta_color="normal"
        )

    st.write("")

    # --------------------------------------------------------------------------
    # 8. X축 눈금 함수
    # --------------------------------------------------------------------------
    def get_nice_ticks(max_val):
        if max_val == 0:
            return [-10, 0, 10], ["10", "0", "10"]
        
        raw_step = max_val / 4
        magnitude = 10 ** math.floor(math.log10(raw_step)) if raw_step > 0 else 1
        residual = raw_step / magnitude
        
        if residual > 5:
            step = 10 * magnitude
        elif residual > 2:
            step = 5 * magnitude
        elif residual > 1:
            step = 2 * magnitude
        else:
            step = magnitude
            
        step = int(max(1, step))
        num_steps = math.ceil(max_val / step)
        
        vals = [i * step for i in range(-num_steps, num_steps + 1)]
        texts = [f"{abs(v):,}" for v in vals]
        return vals, texts

    male_x = [-x for x in male_counts]
    female_x = female_counts
    max_population = max(max(male_counts), max(female_counts))
    x_vals, x_texts = get_nice_ticks(max_population)


    # --------------------------------------------------------------------------
    # 9. Plotly 차트 (피라미드 색상 유지 + 빛나는 라인 외곽선 적용)
    # --------------------------------------------------------------------------
    fig = go.Figure()

    # 남자 막대 - 파스텔 인디고 (#6366F1) + 발광용 외곽선 (#A5B4FC)
    fig.add_trace(go.Bar(
        y=age_labels,
        x=male_x,
        name='남자',
        orientation='h',
        marker=dict(
            color='#6366F1',
            line=dict(color='#818CF8', width=0.8)
        ),
        customdata=male_counts,
        hovertemplate='<b>%{y}</b><br>남성 인구: %{customdata:,}명<extra></extra>'
    ))

    # 여자 막대 - 파스텔 로즈 핑크 (#EC4899) + 발광용 외곽선 (#F472B6)
    fig.add_trace(go.Bar(
        y=age_labels,
        x=female_x,
        name='여자',
        orientation='h',
        marker=dict(
            color='#EC4899',
            line=dict(color='#F472B6', width=0.8)
        ),
        customdata=female_counts,
        hovertemplate='<b>%{y}</b><br>여성 인구: %{customdata:,}명<extra></extra>'
    ))

    fig.update_layout(
        title=dict(
            text=f"<b>[{selected_sido} {selected_sigungu} {selected_dong}]</b> 연령별 인구 분포",
            font=dict(size=20, color="#FFFFFF")
        ),
        barmode='overlay',
        bargap=0.08,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        
        # X축 디자인 (고대비 백색 폰트)
        xaxis=dict(
            title="<b>인구수 (명)</b>",
            title_font=dict(color="#E2E8F0"),
            tickvals=x_vals,
            ticktext=x_texts,
            tickfont=dict(color="#F1F5F9", size=11),
            gridcolor='rgba(255, 255, 255, 0.08)',
            zerolinecolor='rgba(255, 255, 255, 0.25)',
            zerolinewidth=1.5
        ),
        
        # Y축 디자인 (0세 맨 아래, 100세 이상 맨 위 고정 & 선명한 나이 글씨)
        yaxis=dict(
            title="<b>나이</b>",
            title_font=dict(color="#E2E8F0"),
            type='category',
            categoryorder='array',
            categoryarray=age_labels,
            tickfont=dict(color="#F1F5F9", size=10),
            gridcolor='rgba(255, 255, 255, 0.05)'
        ),
        
        # 범례 디자인
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=14, color="#FFFFFF")
        ),
        
        height=950,
        margin=dict(l=50, r=50, t=90, b=50)
    )

    st.plotly_chart(fig, use_container_width=True)


    # --------------------------------------------------------------------------
    # 10. 하단 자동 진단 요약 카드 (고대비 텍스트)
    # --------------------------------------------------------------------------
    if child_ratio > elderly_ratio:
        summary_text = (
            f"👧👶 <b style='color:#818CF8;'>이 동네는 아이들이 상대적으로 많은 편입니다!</b><br>"
            f"유소년(0~14세) 비율이 <b>{child_ratio:.1f}%</b>로, 고령 인구(65세 이상, <b>{elderly_ratio:.1f}%</b>)보다 더 높아서 "
            f"어린이와 가족 단위 인구가 많이 거주하는 활기찬 특성을 보입니다."
        )
    elif elderly_ratio >= 20.0:
        summary_text = (
            f"👵👴 <b style='color:#F472B6;'>이 동네는 어르신들이 많이 거주하는 초고령화 지역입니다.</b><br>"
            f"65세 이상 어르신 비율이 <b>{elderly_ratio:.1f}%</b>(20% 이상)로, 아이들(0~14세, <b>{child_ratio:.1f}%</b>)에 비해 "
            f"고령층 비중이 매우 높은 지역입니다."
        )
    elif elderly_ratio > child_ratio:
        summary_text = (
            f"🏡👵 <b style='color:#C084FC;'>이 동네는 아이들보다 어르신 비율이 조금 더 높은 편입니다.</b><br>"
            f"65세 이상 어르신 비율(<b>{elderly_ratio:.1f}%</b>)이 유소년 비율(<b>{child_ratio:.1f}%</b>)보다 높아 "
            f"차분한 주거 환경의 특성을 보입니다."
        )
    else:
        summary_text = (
            f"⚖️ <b style='color:#38BDF8;'>이 동네는 아이들과 어르신의 비율이 균형을 이루고 있습니다.</b><br>"
            f"유소년 비율(<b>{child_ratio:.1f}%</b>)과 고령 인구 비율(<b>{elderly_ratio:.1f}%</b>)이 조화를 이루고 있습니다."
        )

    st.markdown(f'<div class="summary-card">{summary_text}</div>', unsafe_allow_html=True)

else:
    st.warning("선택하신 지역의 인구 데이터가 존재하지 않습니다.")
